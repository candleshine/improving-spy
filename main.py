# main.py
"""
Chronicle Engine: A teachable, functional AI RPG engine using Pydantic AI and FastAPI.
"""
import os
import json
import logging
import asyncio
import re
import websockets
from datetime import datetime
from fastapi import FastAPI, WebSocket, Query, HTTPException
from pydantic_ai.messages import ModelMessagesTypeAdapter

# --- Setup Logging ---
logger = logging.getLogger("chronicle_engine")
logger.setLevel(logging.INFO)

# Add handler if not already present (e.g., for direct execution)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        )
    )
    logger.addHandler(handler)

# --- Paths ---
SCENARIOS_DIR = "scenarios"
SAVES_DIR = "saves"

os.makedirs(SCENARIOS_DIR, exist_ok=True)
os.makedirs(SAVES_DIR, exist_ok=True)

# --- Create a minimal default scenario if none exists ---
if not os.listdir(SCENARIOS_DIR):
    with open(f"{SCENARIOS_DIR}/safehouse_vienna.json", "w") as f:
        json.dump({
            "title": "Safehouse Vienna",
            "system_prompt": "You are the Game Master of a tense, choice-driven espionage thriller. Keep the story moving. Raise the stakes.",
            "scenes": {
                "arrival": {
                    "narrative": "Rain hammers the windows of the Vienna safehouse. A man in a soaked trench coat collapses against the door, blood on his sleeve..."
                }
            },
            "npcs": {}
        }, f)
    logger.info("Created default scenario: safehouse_vienna.json")

# --- In-Memory Session Store ---
# In production, replace with Redis or DB
sessions = {}
session_timestamps = {}  # Track when sessions were last active
SESSION_TIMEOUT = 300  # 5 minutes in seconds

# --- Session Management Functions ---
async def cleanup_expired_sessions():
    """Cleanup sessions that have been inactive for longer than SESSION_TIMEOUT"""
    now = datetime.utcnow().timestamp()
    expired_sessions = []
    
    for session_id, timestamp in session_timestamps.items():
        if now - timestamp > SESSION_TIMEOUT:
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        if session_id in sessions:
            logger.info(f"Removing expired session | session_id={session_id} | inactive_seconds={now - session_timestamps[session_id]:.1f}")
            del sessions[session_id]
            del session_timestamps[session_id]


def update_session_timestamp(session_id):
    """Update the last activity timestamp for a session"""
    session_timestamps[session_id] = datetime.utcnow().timestamp()


# --- Periodic Session Cleanup ---
async def periodic_session_cleanup():
    """Run session cleanup periodically to remove abandoned sessions"""
    while True:
        try:
            await asyncio.sleep(60)  # Run every minute
            await cleanup_expired_sessions()
        except Exception as e:
            logger.error(f"Error in periodic session cleanup: {e}", exc_info=True)


# --- FastAPI App ---
app = FastAPI(
    title="Chronicle Engine",
    description="A teachable, functional AI RPG engine using Pydantic AI and FastAPI",
    version="0.1.0"
)


# --- Startup Event ---
@app.on_event("startup")
async def startup_event():
    """Start background tasks when the application starts"""
    # Start the periodic session cleanup task
    asyncio.create_task(periodic_session_cleanup())
    logger.info("Started periodic session cleanup task")

# --- Event Parsing ---
def parse_game_events(text: str):
    """
    Parse structured events from AI output.
    Formats:
      [NPC:Name] "Dialogue"
      [CLUE:Title] "Description"
      [QUEST:Title] Status: status
      [CHOICE] "Option 1" / "Option 2"
    """
    import re
    events = []

    # NPC Speech
    for match in re.finditer(r"\[NPC:(\w+)\]\s*\"?([^\"\]]+)", text):
        events.append({
            "type": "npc_speak",
            "name": match.group(1),
            "text": match.group(2).strip()
        })

    # Clues
    for match in re.finditer(r"\[CLUE:([^\]]+)\]\s*\"?([^\"\]]+)", text):
        events.append({
            "type": "clue",
            "title": match.group(1),
            "description": match.group(2).strip()
        })

    # Quest Updates
    for match in re.finditer(r"\[QUEST:([^\]]+)\]\s*Status:\s*(\w+)", text):
        events.append({
            "type": "quest_update",
            "title": match.group(1),
            "status": match.group(2)
        })

    # Choices
    choice_match = re.search(r"\[CHOICE\]\s*(.+)", text)
    if choice_match:
        options_text = choice_match.group(1)
        # Extract options with their numbers if present (e.g., "1. Option One" / "2. Option Two")
        options = []
        for opt in options_text.split("/"):
            opt = opt.strip().strip('"')
            # Check if option has a number prefix (e.g., "1. Option")
            number_match = re.match(r"(\d+)\s*\.\s*(.+)", opt)
            if number_match:
                option_num = int(number_match.group(1))
                option_text = number_match.group(2).strip()
                options.append({"number": option_num, "text": option_text})
            else:
                # If no number, add as is
                options.append({"text": opt})
                
        events.append({
            "type": "choice", 
            "options": options,
            "raw_text": options_text
        })

    # Remaining text is narrative
    clean_text = re.sub(r"\[NPC:[^\]]+\][^\n]*", "", text)
    clean_text = re.sub(r"\[CLUE:[^\]]+\][^\n]*", "", clean_text)
    clean_text = re.sub(r"\[QUEST:[^\]]+\][^\n]*", "", clean_text)
    clean_text = re.sub(r"\[CHOICE\][^\n]*", "", clean_text).strip()
    if clean_text:
        events.append({"type": "narrative", "text": clean_text})

    return events

# --- WebSocket Endpoint ---
@app.websocket("/ws/play")
async def play_game(websocket: WebSocket, scenario: str = Query(...)):
    """
    WebSocket endpoint to play a scenario.
    Usage: /ws/play?scenario=safehouse_vienna
    """
    await websocket.accept()
    session_id = f"{scenario}_{id(websocket)}"

    # Send immediate connection confirmation
    await websocket.send_json({
        "type": "system",
        "text": "Connection established. Starting your adventure..."
    })
    logger.debug("Sent initial connection confirmation")

    logger.info(f"WebSocket connected | session_id={session_id} | scenario={scenario}")

    # Validate scenario
    scenario_file = f"{SCENARIOS_DIR}/{scenario}.json"
    if not os.path.exists(scenario_file):
        error_msg = f"Scenario '{scenario}' not found. Available: {os.listdir(SCENARIOS_DIR)}"
        logger.error(error_msg)
        await websocket.send_json({"type": "error", "text": error_msg})
        return

    # Initialize connection state
    connected = True
    reconnection_allowed = True
    
    try:
        # Load scenario
        with open(scenario_file, "r") as f:
            scenario_data = json.load(f)

        # Clean up any expired sessions
        await cleanup_expired_sessions()
        
        # Initialize or resume session
        if session_id not in sessions:
            logger.info(f"Initializing new session | scenario={scenario}")
            sessions[session_id] = {
                "scenario": scenario,
                "history": [],
                "current_scene": "arrival"
            }
            
        # Update session timestamp
        update_session_timestamp(session_id)

        # For new sessions, send the starting scene
        if session_id in sessions and "engine" not in sessions[session_id]:
            # Send starting scene with initial prompt
            scene = next(iter(scenario_data["scenes"].values()))
            logger.info(f"Found arrival scene: {scene}")
            if scene:
                # Store system prompt for agent use but don't send to client
                if "system_prompt" in scenario_data:
                    logger.info(f"Found system prompt: {scenario_data['system_prompt']}")
                
                # Send the first narrative
                narrative_msg = {
                    "type": "narrative",
                    "text": scene["narrative"],
                    "scene_id": "arrival",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket.send_json(narrative_msg)
                logger.info(f"Sent starting scene: {narrative_msg}")
                
                # Add a prompt for user input if this is a new session
                prompt_msg = {
                    "type": "system",
                    "text": "What would you like to do?",
                    "requires_input": True,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket.send_json(prompt_msg)
        else:
            logger.info(f"Resuming existing session | session_id={session_id}")
            session = sessions[session_id]

        # Game loop
        while connected:
            try:
                # Wait for user input with timeout
                try:
                    user_msg = await asyncio.wait_for(websocket.receive_text(), timeout=300)  # 5 minute timeout
                except asyncio.TimeoutError:
                    logger.warning(f"Connection timeout | session_id={session_id}")
                    try:
                        await websocket.send_json({
                            "type": "system",
                            "text": "Connection timed out due to inactivity. Please refresh the page to continue.",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    except Exception as e:
                        logger.warning(f"Failed to send timeout message: {e}")
                    break
                except asyncio.CancelledError:
                    logger.info(f"Connection cancelled | session_id={session_id}")
                    break

                # Check if we're still connected
                if not connected:
                    break

                logger.info(f"Received input | session_id={session_id} | input='{user_msg[:50]}...'")
                session = sessions.get(session_id)
                if not session:
                    logger.warning(f"Session not found | session_id={session_id}")
                    break
                    
                # Update session timestamp on activity
                update_session_timestamp(session_id)

                # Add src to Python path and import engine
                import sys
                from pathlib import Path
                
                # Add the src directory to the Python path
                src_path = str(Path(__file__).parent / "src")
                if src_path not in sys.path:
                    sys.path.insert(0, src_path)
                    
                from engine.game_engine import GameEngine

                # Lazy-load engine if not already attached
                if "engine" not in session:
                    logger.info(f"Creating GameEngine for session | scenario={scenario}")
                    try:
                        session["engine"] = GameEngine(scenario_file)
                    except Exception as e:
                        logger.error(f"Failed to create GameEngine: {e}", exc_info=True)
                        await websocket.send_json({
                            "type": "error",
                            "text": f"Failed to initialize game engine: {str(e)}",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        break

                engine = session.get("engine")
                if not engine:
                    logger.error(f"Engine not available | session_id={session_id}")
                    break
                    
                history = session.get("history", [])

                # Run the agent with message history
                logger.debug(f"Running agent | history_length={len(history)} messages")
                
                # Send a typing indicator
                try:
                    await websocket.send_json({
                        "type": "system",
                        "text": "Processing your request...",
                        "is_typing": True,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                except Exception as e:
                    logger.warning(f"Failed to send typing indicator: {e}")
                    break
                
                try:
                    # Check for special command patterns
                    npc_interaction = False
                    scene_description = False
                    npc_id = None
                    scene_query = None
                    choice_index = None
                    
                    # Check for NPC interaction format: @NPC:name message
                    npc_match = re.match(r'^@NPC:([\w]+)\s+(.+)$', user_msg)
                    if npc_match:
                        npc_id = npc_match.group(1)
                        npc_message = npc_match.group(2)
                        logger.info(f"Detected direct NPC interaction with {npc_id}: {npc_message}")
                        npc_interaction = True
                    
                    # Check for scene description format: @LOOK message
                    scene_match = re.match(r'^@LOOK\s+(.+)$', user_msg) or re.match(r'^look\s+(.+)$', user_msg, re.IGNORECASE)
                    if scene_match:
                        scene_query = scene_match.group(1)
                        logger.info(f"Detected scene description request: {scene_query}")
                        scene_description = True
                    elif user_msg.lower() in ["look", "look around", "@look", "@look around"]:
                        scene_query = "look around"
                        logger.info("Detected general scene description request")
                        scene_description = True
                    
                    # Check for choice selection: @CHOOSE number or just a number
                    choice_match = re.match(r'^@CHOOSE\s+(\d+)$', user_msg) or re.match(r'^(\d+)$', user_msg)
                    if choice_match:
                        try:
                            choice_index = int(choice_match.group(1)) - 1  # Convert to 0-based index
                            logger.info(f"Detected choice selection: {choice_index + 1}")
                        except ValueError:
                            logger.warning(f"Invalid choice number: {choice_match.group(1)}")
                            choice_index = None
                    
                    if npc_interaction and npc_id:
                        # Handle direct NPC interaction
                        logger.info(f"Processing direct interaction with NPC: {npc_id}")
                        npc_response = await engine.interact_with_npc(npc_id, npc_message, history)
                        events = [npc_response]
                        
                        # Add the interaction to history
                        if "history" in session:
                            # Add user message to NPC
                            session["history"].append({
                                "role": "user",
                                "content": f"[To {npc_id}]: {npc_message}"
                            })
                            # Add NPC response
                            session["history"].append({
                                "role": "assistant",
                                "content": f"[NPC:{npc_id}] {npc_response['text']}"
                            })
                    elif scene_description and scene_query:
                        # Handle scene description request
                        logger.info(f"Processing scene description request: {scene_query}")
                        scene_response = await engine.describe_scene(scene_query, history)
                        events = [scene_response]
                        
                        # Add the interaction to history
                        if "history" in session:
                            # Add user query
                            session["history"].append({
                                "role": "user",
                                "content": f"[Looking at]: {scene_query}"
                            })
                            # Add scene description
                            session["history"].append({
                                "role": "assistant",
                                "content": f"[Scene]: {scene_response['text']}"
                            })
                    elif choice_index is not None:  # Using choice_index directly instead of choice_selection flag
                        # Handle choice selection
                        logger.info(f"Processing choice selection: {choice_index + 1}")
                        try:
                            # Process the choice
                            choice_response = await engine.process_choice_selection(choice_index)
                            events = [choice_response]
                            
                            # Add the choice to history
                            if "history" in session:
                                # Add user choice
                                session["history"].append({
                                    "role": "user",
                                    "content": f"[Choice]: Option {choice_index + 1}"
                                })
                                # Add choice outcome
                                session["history"].append({
                                    "role": "assistant",
                                    "content": f"[Outcome]: {choice_response['text']}"
                                })
                                
                            # If there was a scene transition, get the new scene description
                            if choice_response.get("next_scene"):
                                # Add a scene description event
                                scene_desc = await engine.describe_scene("look around", history)
                                events.append(scene_desc)
                                
                                # Add scene description to history
                                session["history"].append({
                                    "role": "assistant",
                                    "content": f"[Scene]: {scene_desc['text']}"
                                })
                        except Exception as e:
                            logger.error(f"Error processing choice: {e}")
                            events = [{
                                "type": "error",
                                "text": f"Error processing your choice: {str(e)}"
                            }]
                    else:
                        # Normal game master interaction
                        result = await engine.agent.run(user_msg, message_history=history)
                        
                        # Update full message history
                        if hasattr(result, 'all_messages'):
                            session["history"] = result.all_messages()
                            logger.debug(f"Updated history | now {len(result.all_messages())} messages")

                        # Parse and send events
                        ai_output = result.output if hasattr(result, 'output') else str(result)
                        events = parse_game_events(ai_output) if ai_output else []

                    for event in events:
                        # Add timestamp to each event
                        if isinstance(event, dict):
                            event["timestamp"] = datetime.utcnow().isoformat()
                            try:
                                await websocket.send_json(event)
                                logger.debug(f"Sent event | type={event.get('type', 'unknown')} | content='{str(event)[:200]}...'")
                            except Exception as send_error:
                                logger.error(f"Failed to send event: {send_error}")
                                connected = False
                                break
                        else:
                            logger.warning(f"Skipping non-dict event: {type(event)}")
                    
                    if not connected:
                        break
                            
                except Exception as e:
                    error_msg = f"Error processing your request: {str(e)}"
                    logger.error(f"Agent error | session_id={session_id} | error={error_msg}", exc_info=True)
                    try:
                        await websocket.send_json({
                            "type": "error",
                            "text": error_msg,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    except Exception as send_error:
                        logger.error(f"Failed to send error message: {send_error}")
                        connected = False
                    
            except websockets.exceptions.ConnectionClosed as e:
                logger.info(f"WebSocket connection closed | session_id={session_id} | code={e.code} | reason={e.reason}")
                # Only set connected to False, but keep the session intact for potential reconnection
                connected = False
                
                # Normal closure (1000) or going away (1001) are expected to reconnect
                # Other codes might indicate a more serious issue
                if e.code in (1000, 1001):
                    logger.info(f"Normal WebSocket closure, allowing reconnection | session_id={session_id}")
                    reconnection_allowed = True
                else:
                    logger.warning(f"Abnormal WebSocket closure, disallowing reconnection | session_id={session_id} | code={e.code}")
                    reconnection_allowed = False
            except Exception as e:
                logger.error(f"Unexpected error in game loop | session_id={session_id} | error={str(e)}", exc_info=True)
                try:
                    await websocket.send_json({
                        "type": "error",
                        "text": f"An unexpected error occurred: {str(e)}",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                except Exception as send_error:
                    logger.error(f"Failed to send error message to client: {send_error}")
                connected = False
                # Don't allow reconnection for unexpected errors
                reconnection_allowed = False

    except asyncio.CancelledError:
        logger.info(f"Game session was cancelled | session_id={session_id}")
        reconnection_allowed = False
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"WebSocket connection closed | session_id={session_id} | code={e.code} | reason={e.reason}")
        # Normal closure (1000) or going away (1001) are expected to reconnect
        if e.code in (1000, 1001):
            logger.info(f"Normal WebSocket closure, allowing reconnection | session_id={session_id}")
            reconnection_allowed = True
        else:
            logger.warning(f"Abnormal WebSocket closure, disallowing reconnection | session_id={session_id} | code={e.code}")
            reconnection_allowed = False
    except Exception as e:
        logger.error(f"Unexpected error in game session | session_id={session_id} | error={str(e)}", exc_info=True)
        reconnection_allowed = False
        try:
            if not websocket.client_state == websockets.protocol.State.CLOSED:
                await websocket.send_json({
                    "type": "error",
                    "text": f"A server error occurred: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                })
        except Exception as send_error:
            logger.warning(f"Could not send error message to client: {send_error}")
    finally:
        connected = False
        cleanup_errors = []
        
        try:
            # Only clean up the session if it exists and we're not expecting a reconnection
            # For normal WebSocket closures (code 1000), we'll keep the session for potential reconnection
            if session_id in sessions:
                # Check if we had a normal closure or an error
                # If we had an error or explicit cleanup request, remove the session
                # Otherwise, keep it for potential reconnection
                should_cleanup = not reconnection_allowed
                
                try:
                    # Optionally save session before potential removal
                    # await save_game(session_id)
                    
                    # Keep the session active for 5 minutes to allow for reconnection
                    # This helps with temporary disconnections and page refreshes
                    if should_cleanup:
                        # If we're cleaning up, remove the session completely
                        del sessions[session_id]
                        if session_id in session_timestamps:
                            del session_timestamps[session_id]
                        logger.info(f"Cleaned up session | session_id={session_id}")
                    else:
                        # Otherwise, keep the session but update its timestamp
                        # It will be automatically cleaned up after SESSION_TIMEOUT seconds of inactivity
                        logger.info(f"Preserving session for reconnection | session_id={session_id}")
                        update_session_timestamp(session_id)
                except Exception as e:
                    cleanup_errors.append(f"session cleanup: {str(e)}")

            
            # Close the WebSocket connection if it's still open
            if hasattr(websocket, 'client_state') and websocket.client_state != websockets.protocol.State.CLOSED:
                try:
                    # Send close frame if connection is still open
                    await websocket.close(code=1000, reason="Session ended")
                    logger.debug(f"Closed WebSocket connection | session_id={session_id}")
                except Exception as e:
                    cleanup_errors.append(f"WebSocket close: {str(e)}")
                    
        except Exception as e:
            cleanup_errors.append(f"cleanup: {str(e)}")
        finally:
            if cleanup_errors:
                logger.error(f"Errors during cleanup | session_id={session_id} | errors={', '.join(cleanup_errors)}")
            
            logger.info(f"WebSocket session ended | session_id={session_id}")
            return


# --- Save Game ---
@app.post("/save/{session_id}")
async def save_game(session_id: str):
    """
    Save a game session to disk using ModelMessagesTypeAdapter.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    save_data = {
        "scenario": session["scenario"],
        "current_scene": session["current_scene"],
        "state": session.get("state", {}),
        "history": json.dumps(session["history"])
    }

    save_path = f"{SAVES_DIR}/{session_id}.json"
    try:
        with open(save_path, "w") as f:
            json.dump(save_data, f, indent=2)
        logger.info(f"Game saved | session_id={session_id} | path={save_path}")
        return {"status": "saved", "session_id": session_id}
    except Exception as e:
        logger.error(f"Save failed | session_id={session_id} | error={str(e)}")
        raise HTTPException(status_code=500, detail="Save failed")


# --- Load Game ---
@app.post("/load/{session_id}")
async def load_game(session_id: str):
    """
    Load a saved game session using ModelMessagesTypeAdapter.validate_python().
    """
    save_path = f"{SAVES_DIR}/{session_id}.json"
    if not os.path.exists(save_path):
        raise HTTPException(status_code=404, detail="Save file not found")

    try:
        with open(save_path, "r") as f:
            data = json.load(f)

        # Restore history with proper types
        restored_history = ModelMessagesTypeAdapter.validate_python(data["history"])

        # Reconstruct session
        sessions[session_id] = {
            "scenario": data["scenario"],
            "current_scene": data["current_scene"],
            "state": data.get("state", {}),
            "history": restored_history
        }

        logger.info(f"Game loaded | session_id={session_id}")
        return {
            "status": "loaded",
            "scenario": data["scenario"],
            "current_scene": data["current_scene"]
        }

    except Exception as e:
        logger.error(f"Load failed | session_id={session_id} | error={str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to parse saved game")


# --- Health Check ---
@app.get("/health")
async def health():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "scenarios": os.listdir(SCENARIOS_DIR),
        "saves": os.listdir(SAVES_DIR),
        "sessions": len(sessions)
    }