import time
from .llm_service import LLMService
from ..core.config import Config
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Translate:

    def translate(refined_text, conversational_mode, model):
        translation_start = time.time()
        translated_text = LLMService.translate_to_eng(
            refined_text,
            Config.FIREWORKS_API_KEY,
            model,
            conversational_mode
        )
        print(translated_text)
        translation_time = time.time() - translation_start
        logger.info(f"refining total time: {translation_time}")

        return translated_text