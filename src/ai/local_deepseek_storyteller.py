"""
Local DeepSeek-R1-Distill-Qwen-1.5B Storyteller
Runs the model locally for Blood on the Clocktower narration
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from ..core.game_state import GameState


class LocalDeepSeekStoryteller:
    """Local DeepSeek-R1 model for AI storytelling"""

    def __init__(self, model_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Model configuration
        self.model_name = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
        self.model_path = (
            model_path or Path.home() / ".cache" / "deepseek" / "qwen-1.5b"
        )

        # Generation parameters (recommended by DeepSeek)
        self.generation_config = {
            "temperature": 0.6,  # Recommended range: 0.5-0.7
            "max_new_tokens": 150,  # Keep narration concise
            "do_sample": True,
            "top_p": 0.9,
        }

    async def initialize(self) -> bool:
        """Load the model and tokenizer"""
        try:
            self.logger.info("Loading DeepSeek-R1-Distill-Qwen-1.5B model...")

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, cache_dir=self.model_path, trust_remote_code=True
            )

            # Load model with appropriate dtype
            dtype = torch.float16 if self.device == "cuda" else torch.float32
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                cache_dir=self.model_path,
                torch_dtype=dtype,
                trust_remote_code=True,
                device_map="auto" if self.device == "cuda" else None,
            )

            if self.device == "cpu":
                self.model = self.model.to(self.device)

            self.logger.info(f"Model loaded successfully on {self.device}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load DeepSeek model: {e}")
            return False

    def _generate_prompt(self, instruction: str) -> str:
        """
        Generate prompt in DeepSeek format
        Note: DeepSeek recommends no system prompt, all in user message
        """
        # DeepSeek R1 uses special thinking tags
        return f"""<think>
The user wants me to act as a Storyteller for Blood on the Clocktower. I should provide atmospheric narration without making player decisions.
</think>

{instruction}"""

    async def narrate(self, event_type: str, context: Dict[str, Any]) -> str:
        """Generate narration for a game event"""

        if not self.model:
            return self._get_fallback(event_type, context)

        # Build instruction based on event
        instruction = self._build_instruction(event_type, context)
        prompt = self._generate_prompt(instruction)

        try:
            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(**inputs, **self.generation_config)

            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Extract the actual response (remove the prompt and thinking)
            response = response.split(instruction)[-1].strip()

            # Remove any thinking tags if they appear in output
            if "<think>" in response:
                response = response.split("</think>")[-1].strip()

            return response

        except Exception as e:
            self.logger.error(f"Generation error: {e}")
            return self._get_fallback(event_type, context)

    def _build_instruction(self, event_type: str, context: Dict[str, Any]) -> str:
        """Build instruction for the model"""

        base_instruction = "You are the Storyteller for Blood on the Clocktower. Provide a brief (2-3 sentences), atmospheric narration for the following:"

        if event_type == "game_start":
            return f"{base_instruction}\n\nA new game is starting with {context.get('players', 'several')} players. Create an opening that sets a mysterious, gothic atmosphere."

        elif event_type == "night_phase":
            night = context.get("night", 1)
            return f"{base_instruction}\n\nNight {night} is beginning. The town goes to sleep. Build tension and atmosphere."

        elif event_type == "death_announcement":
            deaths = context.get("deaths", [])
            if deaths:
                return f"{base_instruction}\n\nAnnounce that {', '.join(deaths)} died in the night. Be dramatic but respectful."
            else:
                return f"{base_instruction}\n\nAnnounce that nobody died last night. Build suspicion."

        elif event_type == "execution":
            player = context.get("player", "someone")
            return f"{base_instruction}\n\n{player} is being executed by the town. Narrate this dramatic moment."

        elif event_type == "nomination":
            return f"{base_instruction}\n\n{context.get('nominator')} nominates {context.get('nominee')}. Build tension."

        elif event_type == "victory":
            team = context.get("team", "winning")
            return f"{base_instruction}\n\nThe {team} team has won! Create an epic victory announcement."

        elif event_type == "rule_question":
            return f"A player asks: {context.get('question', 'How does this work?')}\n\nProvide a clear, helpful answer about Blood on the Clocktower rules."

        else:
            return f"{base_instruction}\n\n{event_type}"

    def _get_fallback(self, event_type: str, context: Dict[str, Any]) -> str:
        """Fallback narration when model unavailable"""

        fallbacks = {
            "game_start": "The town gathers as darkness approaches. Evil has infiltrated your midst...",
            "night_phase": "Night falls upon the town. Everyone, close your eyes...",
            "death_announcement": "Dawn breaks, revealing the night's terrible events...",
            "execution": "The town has spoken. Justice, or tragedy?",
            "nomination": "Fingers point, accusations fly...",
            "victory": "The game concludes with a decisive victory!",
            "rule_question": "Please consult the rulebook for detailed information.",
        }

        return fallbacks.get(event_type, "The story continues...")

    async def answer_question(self, question: str) -> str:
        """Answer a player's rule question"""

        if not self.model:
            return "Model not loaded. Please check the setup."

        context = {"question": question}
        return await self.narrate("rule_question", context)

    def cleanup(self):
        """Clean up model from memory"""
        if self.model:
            del self.model
            self.model = None
        if self.tokenizer:
            del self.tokenizer
            self.tokenizer = None

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
