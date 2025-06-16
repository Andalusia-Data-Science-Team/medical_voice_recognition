from .llm_service import LLMService
import logging
from ..core.config import Config
import re

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MedicalValidator:
    # Class-level constants
    VALIDATION_PROMPT = """
You are a medical content validator. Analyze the following transcribed text and determine if it contains medical content.

Medical content includes: symptoms, diagnoses, treatments, medications, medical procedures, patient complaints, physical examinations, medical history, vital signs, laboratory results, imaging studies, surgical procedures, therapeutic interventions, etc.

Text to analyze: {text}

Respond with only "MEDICAL" or "NON_MEDICAL" followed by a confidence score (0-100).
Response format: MEDICAL|95 or NON_MEDICAL|87
"""

    @staticmethod
    def validate_medical_content(text: str) -> dict:
        try:
            # Format the prompt with the actual text
            formatted_prompt = MedicalValidator.VALIDATION_PROMPT.format(text=text)
            
            logger.info("Validating medical content with LLM")
            
            # Call the LLM API using your existing service
            response = LLMService._call_llm_api(
                api_key=Config.FIREWORKS_API_KEY,
                model_account="accounts/fireworks/models/deepseek-v3",
                prompt=formatted_prompt,
                temperature=0.1
            )
            
            if not response:
                logger.warning("LLM returned empty response, using fallback validation")
            
            # Parse the response
            result = response.strip()
            logger.info(f"LLM validation response: {result}")
            
            # Extract classification and confidence
            if '|' in result:
                classification, confidence_str = result.split('|', 1)
                classification = classification.strip().upper()
                
                # Extract confidence score (handle various formats)
                confidence_match = re.search(r'(\d+)', confidence_str)
                confidence = int(confidence_match.group(1)) if confidence_match else 50
            else:
                # Handle cases where format might be different
                if 'MEDICAL' in result.upper():
                    classification = 'MEDICAL'
                    confidence = 80  # Default confidence
                else:
                    classification = 'NON_MEDICAL'
                    confidence = 80
            
            return {
                "is_medical": classification == "MEDICAL",
                "confidence": confidence,
                "classification": classification,
                "method": "llm_validation",
                "raw_response": result
            }
            
        except Exception as e:
            logger.error(f"LLM validation failed: {str(e)}")
