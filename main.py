# main.py
"""
Chronicle Engine: A teachable, functional AI RPG engine using Pydantic AI and FastAPI.
"""
import os
import json
import logging
import asyncio
import websockets
from datetime import datetime
from typing import List
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

# --- FastAPI App ---
app = FastAPI(
    title="Chronicle Engine",
    description="A teachable, functional AI RPG engine using Pydantic AI and FastAPI",
    version="0.1.0"
)

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
        options = [opt.strip().strip('"') for opt in choice_match.group(1).split("/")]
        events.append({"type": "choice", "options": options})

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
    
    try:
        # Load scenario
        with open(scenario_file, "r") as f:
            scenario_data = json.load(f)

        # Initialize or resume session
        if session_id not in sessions:
            logger.info(f"Initializing new session | scenario={scenario}")
            sessions[session_id] = {
                "scenario": scenario,
                "history": [],
                "current_scene": "arrival"
            }

            # Send starting scene with initial prompt
            scene = next(iter(scenario_data["scenes"].values()))
            logger.info(f"Found arrival scene: {scene}")
            if scene:
                # Send initial system prompt if available
                if "system_prompt" in scenario_data:
                    system_msg = {
                        "type": "system",
                        "text": scenario_data["system_prompt"],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await websocket.send_json(system_msg)
                    logger.info(f"Sent system prompt: {system_msg}")
                else:
                    logger.info("No system prompt found in scenario")
                
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
                connected = False
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

    except asyncio.CancelledError:
        logger.info(f"Game session was cancelled | session_id={session_id}")
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"WebSocket connection closed | session_id={session_id} | code={e.code} | reason={e.reason}")
    except Exception as e:
        logger.error(f"Unexpected error in game session | session_id={session_id} | error={str(e)}", exc_info=True)
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
            # Clean up the session if it exists
            if session_id in sessions:
                try:
                    # Optionally save session before removing
                    # await save_game(session_id)
                    del sessions[session_id]
                    logger.info(f"Cleaned up session | session_id={session_id}")
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