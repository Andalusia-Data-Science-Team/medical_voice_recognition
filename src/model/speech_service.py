import os
import logging
from fireworks.client.audio import AudioInference
import requests

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# from .audio_preprocessing import AudioPreprocessingService

class SpeechService:
    """Service for speech recognition with audio preprocessing."""
    
    @staticmethod
    def transcribe_audio(audio_file_path, api_key, language="en", preprocess=True):
        """
        Transcribe audio file to text with optional preprocessing.
        
        Args:
            audio_file_path: Path to the audio file
            api_key: Groq API key
            language: Language code (default: "en" for English)
            preprocess: Whether to apply audio preprocessing
            
        Returns:
            Transcribed text
            
        Raises:
            FileNotFoundError: If the audio file doesn't exist
            ValueError: If the audio format is invalid
            Exception: For other transcription failures
        """
        processed_file_path = audio_file_path
        temp_file_created = False
        
        try:
            # Validate input file exists
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
                
            # Apply preprocessing if requested
            if preprocess:
                from .audio_preprocessing import AudioPreprocessingService
                processed_file_path = AudioPreprocessingService.preprocess(audio_file_path)
                temp_file_created = processed_file_path != audio_file_path
                logger.info(f"Audio preprocessing applied: {audio_file_path} → {processed_file_path}")
            
            # Perform transcription
            logger.info(f"Starting transcription for {processed_file_path} in {language}")
            
        except Exception as e:
            # Clean up any temporary files in case of error
            if processed_file_path != audio_file_path and os.path.exists(processed_file_path):
                os.remove(processed_file_path)
            raise Exception(f"Audio transcription failed: {str(e)}")
        
        try:
            processed_file_path = audio_file_path
            audio_file = open(processed_file_path, "rb")
            response = requests.post(
            "https://api.fireworks.ai/inference/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": audio_file},
            data={"model": "whisper-v3", "language": language}
            )
            raw_text = response.json()["text"]
            print(f"Transcription completed successfully: {len(raw_text)} characters, raw_text: {raw_text}")
            return raw_text
            
        except FileNotFoundError as e:
            logger.error(f"File error: {str(e)}")
            raise
        except ValueError as e:
            logger.error(f"Value error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise Exception(f"Audio transcription failed: {str(e)}")
        finally:
            # Clean up temporary processed file if needed
            if temp_file_created and os.path.exists(processed_file_path):
                logger.debug(f"Cleaning up temporary file: {processed_file_path}")
                os.remove(processed_file_path)
            # Clean up temporary processed file if it's different from the original
            if processed_file_path != audio_file_path and os.path.exists(processed_file_path):
                os.remove(processed_file_path)

            return raw_text