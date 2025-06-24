import time
import logging
from .llm_service import LLMService
from ..core.config import Config

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExtractFeature:
    @staticmethod
    def extract(end_text: str, conversational_mode: bool, model: str = "text"):
        """
        Extract features from translated text using LLM and return structured output.
        
        Args:
            end_text (str): The translated text to process.
            conversational_mode (bool): Whether to use conversational mode.
            model (str): The LLM model to use ("text" or "deepseek").
            
        Returns:
            tuple: (json_data: dict, reasoning: str)
        """
        extraction_start = time.time()
        try:
            # Call LLMService to extract features, which returns a dictionary Pydantic model
            features_output = LLMService.extract_features(
                end_text,
                Config.FIREWORKS_API_KEY,
                model,
                conversational_mode
            )
            
            # Extract json_data and reasoning from the structured output
            json_data = features_output.get("json_data", {})
            reasoning = features_output.get("reasoning", "")
            
            extraction_time = time.time() - extraction_start
            logger.info(f"Extraction total time: {extraction_time}")
            
            print(json_data)
            print(reasoning)
            
            return json_data, reasoning
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {str(e)}")
            raise Exception(f"Failed to extract features: {str(e)}")