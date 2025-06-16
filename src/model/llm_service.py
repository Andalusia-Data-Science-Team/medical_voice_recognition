import fireworks.client
import logging
from .utils.prompt import (get_refine_arabic_prompt_llama,
                            get_refine_english_prompt_deepseek_conv,
                            get_refine_english_prompt_deepseek,
                            get_refine_arabic_prompt_deepseek_conv,
                            get_refine_arabic_prompt_deepseek,
                            get_translation_prompt_deepseek_conv,
                            get_translation_prompt_deepseek,
                            get_extraction_prompt_llama,
                            get_refine_english_prompt_llama_conv,
                            get_refine_english_prompt_llama,
                            get_refine_arabic_prompt_llama_conv,
                            get_translation_prompt_llama_conv,
                            get_translation_prompt_llama)

from pydantic import ValidationError
import json
from pydantic import BaseModel, Field
from typing import List, Optional
# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExtractedFeatures(BaseModel):
    entities: List[str] = Field(description="List of extracted entities")
    sentiment: str = Field(description="Sentiment of the text (positive, negative, neutral)")
    keywords: List[str] = Field(description="Key keywords extracted from the text")
    summary: Optional[str] = Field(default=None, description="Optional summary of the text")
    
class LLMService:
    """Service for LLM processing."""
    
    def refine_en_transcription(raw_text, api_key, model, conversational_mode=False):
        """Process English voice transcription with LLM."""
        return LLMService.process_text(raw_text, api_key, model, "refine_english", conversational_mode)
    

    def refine_ar_transcription(raw_text, api_key, model, conversational_mode=False):
        """Process Arabic voice transcription with LLM."""
        return LLMService.process_text(raw_text, api_key, model, "refine_arabic", conversational_mode)
    

    def translate_to_eng(refined_text, api_key, model, conversational_mode=False):
        """Translate refined text to English with LLM."""
        return LLMService.process_text(refined_text, api_key, model, "translate", conversational_mode)
    

    def extract_features(translated_text, api_key, model, conversational_mode=False):
        """Extract features from translated text with LLM."""
        return LLMService.process_text(translated_text, api_key, model, "extract", conversational_mode)
    

    def _get_model_account(model):
        """Get the appropriate model account based on model name."""
        if model == "deepseek":
            return "accounts/fireworks/models/deepseek-v3"
        else:
            return "accounts/fireworks/models/llama4-maverick-instruct-basic"
    

    def _get_prompt(prompt_type, model, text, conversational_mode=False):
        """Get the appropriate prompt based on type, model and mode."""
        if prompt_type == "general_refine":
            return get_refine_arabic_prompt_llama(text) if model == "deepseek" else get_refine_arabic_prompt_llama(text)

        if prompt_type == "refine_english":
            if conversational_mode:
                return get_refine_english_prompt_deepseek_conv(text) if model == "deepseek" else get_refine_english_prompt_llama_conv(text)
            else:
                return get_refine_english_prompt_deepseek(text) if model == "deepseek" else get_refine_english_prompt_llama(text)
 
        if prompt_type == "refine_arabic":
            if conversational_mode:
                return get_refine_arabic_prompt_deepseek_conv(text) if model == "deepseek" else get_refine_arabic_prompt_llama_conv(text)
            else:
                return get_refine_arabic_prompt_deepseek(text) if model == "deepseek" else get_refine_arabic_prompt_llama(text)
        elif prompt_type == "translate":
            if conversational_mode:
                return get_translation_prompt_deepseek_conv(text) if model == "deepseek" else get_translation_prompt_llama_conv(text)
            else:
                return get_translation_prompt_deepseek(text) if model == "deepseek" else get_translation_prompt_llama(text)
        elif prompt_type == "extract":
            return get_extraction_prompt_llama(text) if model == "deepseek" else get_extraction_prompt_llama(text)
        else:
            raise ValueError(f"Unknown prompt type: {prompt_type}")
    
    def _call_llm_api(api_key, model_account, prompt, pydantic_model=None, temperature=0.3):
        """Make API call to the LLM service."""
        fireworks.client.api_key = api_key
        
        try:
            logger.info(f"Calling LLM API with model: {model_account}")
            if pydantic_model:
                # Convert Pydantic model to JSON schema
                json_schema = pydantic_model.schema()
                
                # Fireworks AI structured output call
                response = fireworks.client.Completion.create(
                    model=model_account,
                    prompt=prompt,
                    max_tokens=100000,
                    temperature=temperature,
                    response_format={"type": "json_object", "schema": json_schema}
                )
                
                # Parse the response
                if response.choices and response.choices[0].text.strip():
                    raw_output = response.choices[0].text.strip()
                    # Validate with Pydantic
                    try:
                        parsed_output = json.loads(raw_output)
                        validated_output = pydantic_model(**parsed_output)
                        return validated_output
                    except (json.JSONDecodeError, ValidationError) as e:
                        logger.error(f"Failed to validate structured output: {str(e)}")
                        raise Exception(f"Invalid structured output: {str(e)}")
                else:
                    logger.warning("LLM returned empty response")
                    return None
            else:
                # Fallback to non-structured output
                response = fireworks.client.Completion.create(
                    model=model_account,
                    prompt=prompt,
                    max_tokens=100000,
                    temperature=temperature,
                )
                if response.choices and response.choices[0].text.strip():
                    return response.choices[0].text.strip()
                else:
                    logger.warning("LLM returned empty response")
                    return None
        except Exception as e:
            logger.error(f"LLM API call failed: {str(e)}")
            raise Exception(f"LLM processing failed: {str(e)}")
    
    
    def process_text(text, api_key, model, prompt_type, conversational_mode=False, pydantic_model=None):
        """Generic method to process text with LLM."""
        model_account = LLMService._get_model_account(model)
        if prompt_type == "refine_arabic":
            prompt1 = LLMService._get_prompt("general_refine", model, text, conversational_mode)
            result1 = LLMService._call_llm_api(api_key, model_account, prompt1)
            text = result1
        prompt = LLMService._get_prompt(prompt_type, model, text, conversational_mode)
        result = LLMService._call_llm_api(api_key, model_account, prompt, pydantic_model=pydantic_model)
        return result if result else text
        
    def refine_ar_transcription(raw_text, api_key, model, conversational_mode=False):
        """Process Arabic voice transcription with LLM."""
        return LLMService.process_text(raw_text, api_key, model, "refine_arabic", conversational_mode)
    
    def translate_to_eng(refined_text, api_key, model, conversational_mode=False):
        """Translate refined text to English with LLM."""
        return LLMService.process_text(refined_text, api_key, model, "translate", conversational_mode)
    
    def extract_features(translated_text, api_key, model, conversational_mode=False):
        """Extract features from translated text with LLM."""
        return LLMService.process_text(translated_text, api_key, model, "extract", conversational_mode, pydantic_model=ExtractedFeatures)