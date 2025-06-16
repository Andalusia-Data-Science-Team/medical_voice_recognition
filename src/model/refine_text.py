import time
from .llm_service import LLMService
from ..core.config import Config
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RefineText:

    def refining_transcription(raw_text, conversational_mode, model, language):
        if language == "ar":
            refine_start = time.time()
            refined_text = LLMService.refine_ar_transcription(
                raw_text,
                Config.FIREWORKS_API_KEY,
                model,
                conversational_mode
            )
            refine_time = time.time() - refine_start
            logger.info(f"refining total time: {refine_time}")
            print(refined_text)
        else:
            refine_start = time.time()
            refined_text = LLMService.refine_en_transcription(
                raw_text,
                Config.FIREWORKS_API_KEY,
                model,
                conversational_mode
            )
            refine_time = time.time() - refine_start
            logger.info(f"refining total time: {refine_time}")
            print(refined_text)
        return refined_text