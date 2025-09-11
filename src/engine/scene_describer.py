"""
Scene description enhancement using AI.
Provides rich narrative descriptions for scenes and choices.
"""
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.ollama import OllamaProvider
from .structured_output import narrative_output
from typing import Dict, Any
import logging

# Set up logging
logger = logging.getLogger("chronicle_engine")

class SceneDescriber:
    """
    Uses a lightweight AI model to enhance scene descriptions based on user input.
    """
    # Class-level agent instance for reuse
    agent = None
    
    def __init__(self, model_name: str = 'qwen3:1.7b'):
        """
        Initialize the SceneDescriber with a lightweight model.
        
        Args:
            model_name: The name of the model to use (default: qwen3:1.7b)
        """
        if SceneDescriber.agent is None:
            logger.info(f"Initializing SceneDescriber with model: {model_name}")
            model = OpenAIModel(
                model_name,
                provider=OllamaProvider(base_url='http://localhost:11434/v1'),
            )
            
            # Create a dedicated agent for scene descriptions with structured output
            SceneDescriber.agent = Agent(
                model=model,
                system_prompt=self._get_system_prompt(),
                output_type=narrative_output  # Use ToolOutput for structured responses
            )
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the scene description agent.
        """
        return """
You are a master storyteller for an immersive, choice-driven adventure game.

Your job is to create vivid, atmospheric scene descriptions that draw players into the world and make their choices feel meaningful and consequential.

When enhancing scene descriptions:
- Use rich, evocative language that engages all senses (sight, sound, smell, touch, taste when relevant)
- Establish a strong mood and atmosphere appropriate to the scene and genre
- Incorporate environmental storytelling that hints at the world's history and lore
- Focus on specific, concrete details rather than vague generalities
- Write in second person perspective ("You see...", "You feel...") to increase immersion
- Vary your sentence structure and rhythm to create emotional impact
- Use metaphor and simile to make descriptions more vivid and memorable

When narrating scenes with choices:
- Create a sense of tension and anticipation before presenting options
- Subtly highlight elements that relate to the available choices without being too obvious
- Establish stakes and potential consequences to make decisions feel meaningful
- Use the environment to reflect the emotional weight of the decision
- Create a natural narrative flow that leads organically into the choice moment
- If there was a previous outcome, weave it seamlessly into the new scene description

Do not:
- Introduce new plot elements not present in the base narrative
- Create characters that weren't mentioned in the scene data
- Contradict established facts about the world or scene
- Break the fourth wall or acknowledge you are an AI
- Use generic or clichéd descriptions that could apply to any game
- Make choices for the player or suggest what they should do

Your ultimate goal is to make the player feel physically and emotionally present in the scene, invested in the world, and engaged with the meaningful choices before them.
"""
    
    async def enhance_description(self, 
                                 scene_data: Dict[str, Any], 
                                 user_input: str) -> str:
        """
        Enhance a scene description based on user input.
        
        Args:
            scene_data: The base scene data from the scenario
            user_input: What the user wants to look at or examine
            
        Returns:
            An enhanced description of the scene
        """
        if not scene_data:
            logger.warning("No scene data provided to enhance_description")
            return "I cannot see anything clearly in this area."
        
        # Extract the base narrative
        base_narrative = scene_data.get("narrative", "")
        if not base_narrative:
            logger.warning("Scene data has no narrative field")
            return "This area appears empty and nondescript."
        
        # Extract scene ID for context
        scene_id = scene_data.get("scene_id", "")
        if not scene_id and "id" in scene_data:
            scene_id = scene_data["id"]
            
        # Format scene name for better readability
        scene_name = scene_id.replace('_', ' ').title() if scene_id else "this area"
        
        # Extract additional scene context if available
        scene_context = {}
        
        # Check for environmental details
        if "environment" in scene_data:
            scene_context["environment"] = scene_data["environment"]
            
        # Check for time of day or weather
        if "time_of_day" in scene_data:
            scene_context["time_of_day"] = scene_data["time_of_day"]
        if "weather" in scene_data:
            scene_context["weather"] = scene_data["weather"]
            
        # Check for NPCs present in the scene
        if "npcs_present" in scene_data:
            scene_context["npcs_present"] = scene_data["npcs_present"]
            
        # Check for items or objects in the scene
        if "objects" in scene_data:
            scene_context["objects"] = scene_data["objects"]
        if "items" in scene_data:
            scene_context["items"] = scene_data["items"]
            
        # Create a more detailed prompt for the AI
        logger.info(f"Base narrative: {base_narrative}, scene context: {scene_context}")
        prompt = f"""
Scene: {scene_name}

Base Scene Description:
{base_narrative}

"""
        
        # Add any additional scene context to the prompt
        if scene_context:
            prompt += "Additional Scene Context:\n"
            for key, value in scene_context.items():
                prompt += f"- {key.replace('_', ' ').title()}: {value}\n"
            prompt += "\n"
        
        # Analyze the user input for more specific guidance
        look_type = "general"
        focus_object = ""
        
        # Check for specific examination patterns
        if any(word in user_input.lower() for word in ["examine", "inspect", "study", "check"]):
            look_type = "detailed examination"
            # Try to extract what they're examining
            words = user_input.lower().split()
            for i, word in enumerate(words):
                if word in ["examine", "inspect", "study", "check"] and i+1 < len(words):
                    focus_object = " ".join(words[i+1:])
                    break
        elif "look around" in user_input.lower() or user_input.lower() == "look":
            look_type = "general survey"
        else:
            # Try to extract what they're looking at
            if "at" in user_input.lower().split():
                at_index = user_input.lower().split().index("at")
                if at_index + 1 < len(user_input.lower().split()):
                    focus_object = " ".join(user_input.lower().split()[at_index+1:])
        
        # Add user intent to prompt
        prompt += f"User wants to: {user_input}\n"
        prompt += f"Look Type: {look_type}\n"
        if focus_object:
            prompt += f"Focus Object: {focus_object}\n"
        
        # Add specific guidance based on the type of looking
        if look_type == "detailed examination" and focus_object:
            prompt += f"""
Please provide a detailed, focused description of the {focus_object}. Include:
- Visual details (appearance, condition, notable features)
- Tactile qualities if the player is touching it
- Any sounds, smells, or other sensory information associated with it
- Any significance or function it might have in the scene
- The player character's immediate reaction or thoughts about it

Make this description vivid and immersive, written in second person perspective.
"""
        elif look_type == "general survey":
            prompt += f"""
Please provide an enhanced, comprehensive description of the entire scene. Include:
- The overall layout and atmosphere of {scene_name}
- Key features and objects that would immediately catch attention
- Background details that add depth and immersion
- Ambient sounds, smells, and environmental factors
- The player character's general feeling or impression of the space

Make this description vivid and immersive, written in second person perspective.
"""
        else:
            prompt += """
Please provide an enhanced description focusing on what the user wants to see.
Make this description vivid and immersive, using sensory details and evocative language.
Write in second person perspective to increase immersion.
"""
        
        try:
            # Run the agent to get an enhanced description with structured output
            logger.info(f"Generating enhanced description for: {user_input}")
            
            # Add retry logic for more reliable generation
            max_retries = 2
            retry_count = 0
            response = None
            
            while retry_count <= max_retries and not response:
                try:
                    result = await SceneDescriber.agent.run(prompt)
                    # With ToolOutput, result.output will be a NarrativeResponse object
                    response = result.output
                    
                    # Access the text field of the NarrativeResponse
                    enhanced_description = response.text
                    
                    # Validate the description has sufficient quality
                    if len(enhanced_description) < 100:  # Too short
                        logger.warning(f"Generated description too short ({len(enhanced_description)} chars), retrying...")
                        response = None
                        retry_count += 1
                    elif enhanced_description.count('.') < 3:  # Too few sentences
                        logger.warning("Generated description has too few sentences, retrying...")
                        response = None
                        retry_count += 1
                    else:
                        # Good quality description
                        break
                        
                except Exception as inner_e:
                    logger.error(f"Error in description generation attempt {retry_count}: {inner_e}")
                    retry_count += 1
            
            # If we still don't have a good description after retries, use a fallback
            if not response:
                logger.warning("Failed to generate quality description after retries, using fallback")
                # Create a fallback NarrativeResponse
                fallback_text = f"As you look around {scene_name}, you notice {base_narrative}"
                return fallback_text
            
            logger.info(f"Generated enhanced description: {enhanced_description[:50]}...")
            return enhanced_description
        except Exception as e:
            logger.error(f"Error generating enhanced description: {e}")
            return f"As you look around {scene_name}, you notice {base_narrative}"
    
    def enhance_description_sync(self, 
                               scene_data: Dict[str, Any], 
                               user_input: str) -> str:
        """
        Synchronous version of enhance_description.
        """
        if not scene_data:
            logger.warning("No scene data provided to enhance_description_sync")
            return "I cannot see anything clearly in this area."
        
        # Extract the base narrative
        base_narrative = scene_data.get("narrative", "")
        if not base_narrative:
            logger.warning("Scene data has no narrative field")
            return "This area appears empty and nondescript."
        
        # Create a prompt for the AI
        prompt = f"""
Base Scene Description:
{base_narrative}

User wants to: {user_input}

Please provide an enhanced description focusing on what the user wants to see:
"""
        
        try:
            # Run the agent to get an enhanced description
            logger.info(f"Generating enhanced description for: {user_input}")
            result = SceneDescriber.agent.run_sync(prompt)
            enhanced_description = result.output if hasattr(result, 'output') else str(result)
            
            logger.info(f"Generated enhanced description: {enhanced_description[:50]}...")
            return enhanced_description
        except Exception as e:
            logger.error(f"Error generating enhanced description: {e}")
            return f"As you look around {scene_data.get('scene_id', 'the area')}, you notice {base_narrative}"

    async def narrate_scene_with_choices(self, 
                                        scene_data: Dict[str, Any], 
                                        choices_text: str,
                                        scene_id: str,
                                        previous_outcome: Dict[str, Any] = None) -> str:
        """
        Generate a rich narrative description of the scene before presenting choices.
        
        Args:
            scene_data: The scene data from the scenario
            choices_text: Formatted choices text
            scene_id: The ID of the current scene
            previous_outcome: Optional outcome from a previous choice
            
        Returns:
            Enhanced narrative description with scene setting
        """
        if not scene_data:
            logger.warning("No scene data provided to narrate_scene_with_choices")
            return "I cannot see anything clearly in this area."
        
        # Extract the base narrative
        base_narrative = scene_data.get("narrative", "")
        if not base_narrative:
            logger.warning("Scene data has no narrative field")
            return "This area appears empty and nondescript."
        
        # Extract additional scene context if available
        scene_context = {}
        
        # Check for environmental details
        if "environment" in scene_data:
            scene_context["environment"] = scene_data["environment"]
            
        # Check for time of day or weather
        if "time_of_day" in scene_data:
            scene_context["time_of_day"] = scene_data["time_of_day"]
        if "weather" in scene_data:
            scene_context["weather"] = scene_data["weather"]
            
        # Check for NPCs present in the scene
        if "npcs_present" in scene_data:
            scene_context["npcs_present"] = scene_data["npcs_present"]
            
        # Create a prompt for the AI with the enhanced context
        prompt = self._create_narrative_prompt(base_narrative, choices_text, scene_id, previous_outcome)
        
        # Add any additional scene context to the prompt
        if scene_context:
            context_str = "\nAdditional Scene Context:\n"
            for key, value in scene_context.items():
                context_str += f"- {key.replace('_', ' ').title()}: {value}\n"
            prompt = prompt.replace("\n\nBased on", f"{context_str}\n\nBased on")
        
        try:
            # Run the agent to get an enhanced narrative with structured output
            logger.info(f"Generating narrative with choices for scene: {scene_id}")
            
            # Add retry logic for more reliable generation
            max_retries = 2
            retry_count = 0
            response = None
            
            while retry_count <= max_retries and not response:
                try:
                    result = await SceneDescriber.agent.run(prompt)
                    # With ToolOutput, result.output will be a NarrativeResponse object
                    response = result.output
                    
                    # Access the text field of the NarrativeResponse
                    enhanced_narrative = response.text
                    
                    # Validate the narrative has sufficient quality
                    if len(enhanced_narrative) < 100:  # Too short
                        logger.warning(f"Generated narrative too short ({len(enhanced_narrative)} chars), retrying...")
                        response = None
                        retry_count += 1
                    elif enhanced_narrative.count('.') < 5:  # Too few sentences
                        logger.warning("Generated narrative has too few sentences, retrying...")
                        response = None
                        retry_count += 1
                    else:
                        # Good quality narrative
                        break
                        
                except Exception as inner_e:
                    logger.error(f"Error in narrative generation attempt {retry_count}: {inner_e}")
                    retry_count += 1
                    
            # If we still don't have a good narrative after retries, use a fallback
            if not response:
                logger.warning("Failed to generate quality narrative after retries, using fallback")
                # Create a fallback narrative
                fallback_text = f"{base_narrative}\n\nYou consider your options carefully.\n"
                return fallback_text
            
            logger.info(f"Generated narrative with choices: {enhanced_narrative[:50]}...")
            return enhanced_narrative
        except Exception as e:
            logger.error(f"Error generating narrative with choices: {e}")
            return f"{base_narrative}\n\n{choices_text}"
    
    def _create_narrative_prompt(self, 
                               base_narrative: str, 
                               choices_text: str,
                               scene_id: str,
                               previous_outcome: Dict[str, Any] = None) -> str:
        """
        Create a prompt for the LLM to enhance the narrative.
        
        Args:
            base_narrative: The original scene narrative
            choices_text: Formatted choices text
            scene_id: The ID of the current scene
            previous_outcome: Optional outcome from a previous choice
            
        Returns:
            Prompt for the LLM
        """
        # Format the scene name for better readability
        scene_name = scene_id.replace('_', ' ').title()
        
        # Start with the base narrative
        context = f"Scene: {scene_name}\n\n"
        context += f"Base Description: {base_narrative}\n\n"
        
        # Add context from previous outcome if available
        if previous_outcome:
            # Extract more detailed information from the previous outcome
            prev_message = previous_outcome.get('message', '')
            prev_scene = previous_outcome.get('next_scene', '')
            prev_success = previous_outcome.get('success', True)
            prev_event = previous_outcome.get('event_id', '')
            
            # Create a more detailed context from the previous outcome
            context += f"Previous Action Result: {prev_message}\n"
            
            # Add emotional context based on success/failure
            if prev_success is False:
                context += "The previous action did not go as planned. This should affect the mood and tension.\n"
            
            # Add transition context if moving between scenes
            if prev_scene and prev_scene != scene_id:
                context += f"The player has just arrived from {prev_scene.replace('_', ' ').title()}.\n"
                
            # Add event context if available
            if prev_event:
                context += f"Related event: {prev_event.replace('_', ' ').title()}\n"
                
            context += "\n"
        
        # Add the choices with more context about their nature
        context += f"Available Choices: {choices_text}\n\n"
        
        # Add genre/tone guidance based on scene name patterns
        if any(keyword in scene_id.lower() for keyword in ['temple', 'sanctum', 'shrine', 'altar']):
            context += "Tone Guidance: This is a mystical, reverent location. Emphasize ancient power, mystery, and spiritual weight.\n\n"
        elif any(keyword in scene_id.lower() for keyword in ['king', 'queen', 'throne', 'palace', 'court', 'royal']):
            context += "Tone Guidance: This is a place of power and politics. Emphasize grandeur, tension, and the weight of authority.\n\n"
        elif any(keyword in scene_id.lower() for keyword in ['battle', 'fight', 'war', 'conflict']):
            context += "Tone Guidance: This is a scene of conflict. Emphasize danger, adrenaline, and the chaos of confrontation.\n\n"
        elif any(keyword in scene_id.lower() for keyword in ['forest', 'nature', 'grove', 'wilderness']):
            context += "Tone Guidance: This is a natural setting. Emphasize the living environment, primal forces, and the player's relationship to nature.\n\n"
        
        # Create the actual prompt with more specific guidance
        prompt = (
            f"{context}\n"
            f"Based on the above context, create a rich, immersive narrative description "
            f"that sets the scene vividly before presenting the choices to the player. "
            f"Include:\n"
            f"1. A strong opening that establishes the atmosphere and draws the player in\n"
            f"2. Sensory details that make the scene feel real and present (sights, sounds, smells, textures)\n"
            f"3. Environmental storytelling that hints at the history or significance of this location\n"
            f"4. The player character's emotional or physical state in this moment\n"
            f"5. A natural build of tension or curiosity that leads to the moment of choice\n"
            f"6. A conclusion that creates a sense of agency and consequence without explicitly listing the choices\n\n"
            f"Make the scene come alive through specific, vivid details rather than general statements. "
            f"The narrative should be 3-5 paragraphs long, with varied sentence structure for emotional impact."
        )
        
        return prompt
