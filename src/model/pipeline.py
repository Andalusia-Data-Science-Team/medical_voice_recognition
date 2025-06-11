from .speech_service import SpeechService
from .llm_service import LLMService
from .audio_preprocessing import AudioPreprocessingService
from .utils.text_parser import parse_refined_text_voice2
import logging
import time
import os
import concurrent.futures
from pydub import AudioSegment
from typing import Optional, List
from ..core.config import Config
import asyncio
import numpy as np
from .input_validator import MedicalValidator

# Set up logging
logger = logging.getLogger(__name__)

class DataPipeline:
    """Service handling audio processing workflows."""
    
    @staticmethod
    def process_batch(audio_file: str, language: str, model: str, conversational_mode: bool):
        """Process audio in batch mode (non-streaming).
        
        Args:
            audio_file: Path to the audio file
            language: Language code for transcription ("en", "ar", etc.)
            model: Model name to use for processing
            conversational_mode: Whether to use conversational mode
            config: Application configuration containing API keys and folders
            
        Returns:
            JSONResponse containing processing results
        """
        process_start = time.time()
        file_path = None
        processed_file_path = None
        
        try:
            # File is already saved by this point in FastAPI approach
            file_path = audio_file
            
            # Step 1: Preprocess audio
            preprocess_start = time.time()
            processed_file_path = AudioPreprocessingService.preprocess_audio(file_path)
            preprocess_time = time.time() - preprocess_start
            logger.info(f"preprocessing total time: {preprocess_time}")

            # Step 2: Transcribe audio
            voice_start = time.time()
            raw_text = DataPipeline._process_audio_parallel(
                processed_file_path, 
                Config.FIREWORKS_API_KEY,
                language
            )
            voice_time = time.time() - voice_start
            logger.info(f"transcription total time: {voice_time}")
            print(raw_text)

            #step 2.5: validation
            validation_result = MedicalValidator.validate_medical_content(text = raw_text)

            if not validation_result["is_medical"] or validation_result["confidence"] < 70:
                return {
                "raw_text": raw_text + " (NON-MEDICAL)",
                "arabic_text": "error", 
                "translation_text": "error",
                "json_data": {  'chief_complaint': 'error', 
                                'icd10_codes': ['error'],
                                'history_of_illness': 'error',
                                'current_medication': 'error',
                                'imaging_results': 'error',
                                'plan': 'error',
                                'assessment': 'error',
                                'follow_up': 'error'},
                "reasoning": "error",
                "preprocessing_time": "error",
                "voice_processing_time": "error",
                "total_time": "error"
                }
            if language == "ar":
                # Step 3: Refine transcription
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

                # Step 4: Translate to English
                translated_text = LLMService.translate_to_eng(
                    refined_text,
                    Config.FIREWORKS_API_KEY,
                    model,
                    conversational_mode
                )
                end_text = translated_text
                print(translated_text)
            else:
                # Step 3: Refine transcription
                refine_start = time.time()
                refined_text = LLMService.refine_en_transcription(
                    raw_text,
                    Config.FIREWORKS_API_KEY,
                    model,
                    conversational_mode
                )
                end_text = refined_text

                refine_time = time.time() - refine_start
                logger.info(f"refining total time: {refine_time}")
                print(refined_text)

                # Step 4: Translate 
                translated_text = "there is no translation"

            # Step 5: Extract features 
            extraction_start = time.time()
            features_with_reasoning = LLMService.extract_features(
                end_text,
                Config.FIREWORKS_API_KEY,
                "llama",
                conversational_mode
            )
            extraction_time = time.time() - extraction_start
            logger.info(f"extraction total time: {extraction_time}")
            # Parse features
            json_data, reasoning = parse_refined_text_voice2(features_with_reasoning)

            print(reasoning)
            print(json_data)
            
            # Return results as a dictionary (FastAPI will convert to JSON)
            response_data = {
                "raw_text": raw_text,
                "arabic_text": refined_text, 
                "translation_text": translated_text,
                "json_data": json_data,
                "reasoning": reasoning,
                "preprocessing_time": preprocess_time,
                "voice_processing_time": voice_time,
                "total_time": time.time() - process_start
            }
            
            # Using JSONResponse to explicitly create a JSON response
            return response_data
            
        except Exception as e:
            logger.error(f"Error in batch processing: {str(e)}", exc_info=True)
                
            # Cleanup files
            DataPipeline._cleanup_files(file_path, processed_file_path)
            
            raise
    
    @staticmethod
    def _process_audio_parallel(file_path: str, api_key: str, language: str, max_workers: int = 3, 
                               chunk_percentage: int = 100) -> str:
        """Process audio in parallel chunks or as a single file based on chunk percentage."""
        # If chunk_percentage is 100 or close to it, process the whole file directly
        if chunk_percentage >= 100:
            logger.info("Processing audio as a single file (no chunking)")
            return DataPipeline._process_chunk(file_path, api_key, language)
        
        # Otherwise, split into chunks and process in parallel
        chunks = DataPipeline._split_audio(file_path, chunk_percentage)
        
        # If only one chunk was created, process it directly
        if len(chunks) <= 1:
            if chunks:
                result = DataPipeline._process_chunk(chunks[0], api_key, language)
                return result
            return ""
        
        # Multiple chunks - process in parallel
        results = [None] * len(chunks)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [(i, executor.submit(
                DataPipeline._process_chunk, chunk, api_key, language
            )) for i, chunk in enumerate(chunks)]
            
            for i, future in futures:
                try:
                    results[i] = future.result()
                    print(f"Chunk {i} processed successfully")
                except Exception as e:
                    logger.error(f"Chunk {i} failed: {str(e)}")
                    results[i] = ""
        
        return " ".join(filter(None, results))

    @staticmethod
    def _split_audio(file_path: str, chunk_percentage: int = 100) -> List[str]:
        """
        Split audio file into smaller chunks for parallel processing
        
        Args:
            file_path: Path to the audio file
            chunk_percentage: Percentage of total audio length for each chunk (default: 10%)
        
        Returns:
            List of paths to the created chunk files
        """
        try:
            audio = AudioSegment.from_file(file_path)
            total_duration = len(audio)
            
            # Calculate chunk duration in milliseconds based on percentage
            chunk_duration_ms = int(total_duration * (chunk_percentage / 100))
            
            chunks = []
            # Create chunks of calculated duration
            for i in range(0, total_duration, chunk_duration_ms):
                end = min(i + chunk_duration_ms, total_duration)
                chunk = audio[i:end]
                
                # Save chunk to temporary file
                chunk_path = f"{file_path}_chunk_{i}.wav"
                chunk.export(chunk_path, format="wav")
                chunks.append(chunk_path)
            
            logger.info(f"Created {len(chunks)} audio chunks (each {chunk_percentage}% of total duration)")
            return chunks
        except Exception as e:
            logger.error(f"Error splitting audio: {str(e)}")
            raise
    
    @staticmethod
    def _process_chunk(chunk_path: str, api_key: str, language: str) -> str:
        """Process a single audio chunk with Whisper"""
        try:
            logger.info(f"Processing audio chunk: {chunk_path}")
            text = SpeechService.transcribe_audio(chunk_path, api_key, language, preprocess=False)
                
            # Clean up chunk file
            if os.path.exists(chunk_path):
                os.remove(chunk_path)
                logger.info(f"Removed chunk {chunk_path}")
                
            # Clean up chunk file             
            return text
        except Exception as e:
            logger.error(f"Error processing chunk {chunk_path}: {str(e)}")
            if os.path.exists(chunk_path):
                os.remove(chunk_path)
                logger.info(f"Removed chunk {chunk_path} after error")
            return ""
    
    @staticmethod
    def _cleanup_files(file_path: Optional[str], processed_file_path: Optional[str]) -> None:
        """Clean up temporary files."""
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            
        if processed_file_path and processed_file_path != file_path and os.path.exists(processed_file_path):
            os.remove(processed_file_path)