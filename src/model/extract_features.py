import time
from .llm_service import LLMService
from ..core.config import Config
import logging
from .utils.text_parser import parse_refined_text_voice2

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExtractFeature:

    def extract(end_text, conversational_mode, model = "llama"):
        
        extraction_start = time.time()
        features_with_reasoning = LLMService.extract_features(
            end_text,
            Config.FIREWORKS_API_KEY,
            model,
            conversational_mode
        )
        extraction_time = time.time() - extraction_start
        logger.info(f"extraction total time: {extraction_time}")
        # Parse features
        json_data, reasoning = parse_refined_text_voice2(features_with_reasoning)

        print(reasoning)
        print(json_data)
        return json_data, reasoning