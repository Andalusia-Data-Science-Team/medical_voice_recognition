import fireworks.client
import logging
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Generator
import json

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic model for structured output
class ProcessedTextOutput(BaseModel):
    refined_text: str = Field(description="Refined Arabic text from Whisper output")
    translated_text: str = Field(description="Translated text in English")
    Chief_complain: str = Field(description="chief complain of the patient") 
    ICD10_codes: str = Field(description="icd10 codes of the diagnosis of the doctor")

class LLMService:
    """Service for LLM processing with consolidated text processing and streaming support."""

    @staticmethod
    def _get_model_account(model):
        """Get the appropriate model account based on model name."""
        if model == "deepseek":
            return "accounts/fireworks/models/deepseek-v3"
        else:
            return "accounts/fireworks/models/llama4-maverick-instruct-basic"

    @staticmethod
    def _call_llm_api(api_key, model_account, prompt, pydantic_model=None, temperature=0.3, stream=False):
        """Make API call to the LLM service with optional streaming and structured output."""
        fireworks.client.api_key = api_key
        
        try:
            logger.info(f"Calling LLM API with model: {model_account}, stream={stream}")
            if stream:
                # Streaming mode: Yield partial responses
                stream_response = fireworks.client.Completion.create(
                    model=model_account,
                    prompt=prompt,
                    max_tokens=100000,
                    temperature=temperature,
                    stream=True
                )
                buffer = ""
                for chunk in stream_response:
                    if chunk.choices and chunk.choices[0].text:
                        buffer += chunk.choices[0].text
                        yield chunk.choices[0].text  # Yield partial text for UI streaming
                # Validate final response if pydantic_model is provided
                if pydantic_model and buffer.strip():
                    try:
                        parsed_output = json.loads(buffer)
                        validated_output = pydantic_model(**parsed_output)
                        yield validated_output  # Yield final validated Pydantic object
                    except (json.JSONDecodeError, ValidationError) as e:
                        logger.error(f"Failed to validate streamed output: {str(e)}")
                        raise Exception(f"Invalid streamed output: {str(e)}")
            else:
                # Non-streaming mode
                if pydantic_model:
                    json_schema = pydantic_model.schema()
                    response = fireworks.client.Completion.create(
                        model=model_account,
                        prompt=prompt,
                        max_tokens=100000,
                        temperature=temperature,
                        response_format={"type": "json_object", "schema": json_schema}
                    )
                    if response.choices and response.choices[0].text.strip():
                        raw_output = response.choices[0].text.strip()
                        try:
                            parsed_output = json.loads(raw_output)
                            validated_output = pydantic_model(**parsed_output)
                            return validated_output
                        except (json.JSONDecodeError, ValidationError) as e:
                            logger.error(f"Failed to validate structured output: {str(e)}")
                            raise Exception(f"Invalid structured output: {str(e)}")
                else:
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

    @staticmethod
    def process_arabic_text(raw_text, api_key, model, conversational_mode=False, stream=False):
        """Process Arabic Whisper output: refine, translate to English, and extract features with optional streaming."""
        model_account = LLMService._get_model_account(model)
        
        # Combined prompt for refinement, translation, and feature extraction
        prompt = (
            f"Given the following raw Arabic text from a Whisper transcription: '{raw_text}'\n"
            "Perform the following tasks:\n"
            "1. Refine the Arabic text to correct any transcription errors and improve clarity.\n"
            "2. Translate the refined Arabic text to natural and accurate English.\n"
            "3. Extract features from the translated text, including:\n"
            "   - Chief complain\n"
            "   - ICD10 codes (recomend as you can)\n"
            "Return the result as a JSON object with fields: refined_text, translated_text, Chief complain, ICD10 codes."
        )
        
        if stream:
            # Return a generator for streaming
            return LLMService._call_llm_api(
                api_key=api_key,
                model_account=model_account,
                prompt=prompt,
                pydantic_model=ProcessedTextOutput,
                temperature=0.3,
                stream=True
            )
        else:
            # Non-streaming call
            return LLMService._call_llm_api(
                api_key=api_key,
                model_account=model_account,
                prompt=prompt,
                pydantic_model=ProcessedTextOutput,
                temperature=0.3,
                stream=False
            )