from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.exceptions import HTTPException
import time
import pandas as pd
import logging
from typing import Optional
import os
import uvicorn
import json
import asyncio
import sys

# Import your services
from ..core.config import Config
from ..core.database import DatabaseService
from ..model.speech_service import SpeechService
from ..model.input_validator import MedicalValidator
from ..model.refine_text import RefineText
from ..model.translation import Translate
from ..model.extract_features import ExtractFeature

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize FastAPI app
app = FastAPI(title="Audio Processing API")

def load_forms_dataframe():
    try:
        logger.info("Loading forms dataframe from data_latest.parquet")
        df = pd.read_parquet("data_latest.parquet", engine="pyarrow")
        logger.info(f"Loaded dataframe with {len(df)} forms")
        return df
    except Exception as e:
        logger.error(f"Error loading forms dataframe: {str(e)}")
        return pd.DataFrame(columns=['name', 'json_format'])

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Initializing application")
    
    # Initialize database
    db_initialized = DatabaseService.initialize_db()
    if db_initialized:
        logger.info("Database initialized successfully")
    else:
        logger.error("Failed to initialize database")

@app.get('/get_forms')
async def get_forms():
    df = load_forms_dataframe()
    form_names = df['name'].dropna().unique().tolist()
    return JSONResponse(form_names)

@app.post("/upload")
async def upload(
    audio: UploadFile = File(...),
    language: str = Form("en"),
    model: str = Form("deepseek"),
    isConversation: Optional[str] = Form(None),
    doctorName: Optional[str] = Form(None),
    feedback: Optional[str] = Form(None)
):
    """Handle file uploads and stream processing results."""
    logger.info("Received upload request")
    
    # Check conversational mode
    conversational_mode = isConversation == 'on'
    logger.info(f"Upload parameters: language={language}, model={model}, conversational mode={conversational_mode}")
    logger.info(f"Doctor: {doctorName}")
    
    # For recorded audio, set a default filename if none is provided
    if audio.filename == "":
        audio.filename = f"recorded_audio_{int(time.time())}.wav"
        logger.info(f"Set default filename: {audio.filename}")
    
    # Save the uploaded file
    try:
        contents = await audio.read()
        file_path = os.path.join(Config.UPLOAD_FOLDER, audio.filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(contents)
        logger.info(f"File saved to {file_path}")
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    async def stream_results():
        """Stream processing results as they become available."""
        try:
            # Step 1: Transcribe audio
            logger.info("Starting transcription")
            try:
                transcripted_text = SpeechService.transcribe_audio(file_path, Config.FIREWORKS_API_KEY, language)
                if not transcripted_text:
                    raise ValueError("Transcription returned empty text")
                yield json.dumps({"step": "transcription", "data": transcripted_text}) + "\n"
            except Exception as e:
                logger.error(f"Transcription error: {str(e)}", exc_info=True)
                yield json.dumps({"step": "error", "data": f"Transcription failed: {str(e)}"}) + "\n"
                return
            await asyncio.sleep(0.1)

            # Step 2: Refine text
            logger.info("Starting text refinement")
            try:
                refined_text = RefineText.refining_transcription(transcripted_text, conversational_mode, model="deepseek", language=language)
                yield json.dumps({"step": "refinement", "data": refined_text}) + "\n"
            except Exception as e:
                logger.error(f"Refinement error: {str(e)}", exc_info=True)
                yield json.dumps({"step": "error", "data": f"Refinement failed: {str(e)}"}) + "\n"
                return
            await asyncio.sleep(0.1)

            # Step 3: Translate if needed
            logger.info("Starting translation")
            try:
                if language == "ar":
                    end_text = Translate.translate(refined_text, conversational_mode, model="deepseek")
                else:
                    end_text = refined_text
                yield json.dumps({"step": "translation", "data": end_text}) + "\n"
            except Exception as e:
                logger.error(f"Translation error: {str(e)}", exc_info=True)
                yield json.dumps({"step": "error", "data": f"Translation failed: {str(e)}"}) + "\n"
                return
            await asyncio.sleep(0.1)

            # Step 4: Extract features
            logger.info("Starting feature extraction")
            try:
                json_data, reasoning = ExtractFeature.extract(end_text, conversational_mode)
                yield json.dumps({"step": "feature_extraction", "data": {"json_data": json_data, "reasoning": reasoning}}) + "\n"
            except Exception as e:
                logger.error(f"Feature extraction error: {str(e)}", exc_info=True)
                yield json.dumps({"step": "error", "data": f"Feature extraction failed: {str(e)}"}) + "\n"
                return
            await asyncio.sleep(0.1)

            # Step 5: Save to database
            logger.info("Saving to database")
            try:
                json_data_str = json.dumps(json_data) if isinstance(json_data, (dict, list)) else json_data
                result_id = DatabaseService.save_audio_result(
                    filename=audio.filename,
                    language=language,
                    model=model,
                    is_conversation=conversational_mode,
                    raw_text=transcripted_text,
                    arabic_text=refined_text,
                    translation_text=end_text,
                    json_data=json_data_str,
                    reasoning=reasoning,
                    preprocessing_time=3,
                    voice_processing_time=3,
                    llm_processing_time=3,
                    doctor_name=doctorName,
                    feedback=""
                )
                logger.info(f"Saved processing result to database with ID: {result_id}")
                yield json.dumps({"step": "database_save", "data": {"result_id": result_id}}) + "\n"
            except Exception as e:
                logger.error(f"Database save error: {str(e)}", exc_info=True)
                yield json.dumps({"step": "error", "data": f"Database save failed: {str(e)}"}) + "\n"
                return

        except Exception as e:
            logger.error(f"Unexpected error in stream processing: {str(e)}", exc_info=True)
            yield json.dumps({"step": "error", "data": f"Unexpected error: {str(e)}"}) + "\n"
        finally:
            # Clean up uploaded file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up file: {file_path}")
            except Exception as e:
                logger.error(f"Error cleaning up file: {str(e)}")

    return StreamingResponse(stream_results(), media_type="text/event-stream")

@app.post("/save-feedback")
async def save_feedback(request: Request):
    """Save feedback for an existing result."""
    try:
        data = await request.json()
        result_id = data.get("result_id")
        feedback = data.get("feedback")
        
        if not result_id:
            return JSONResponse(content={"error": "Missing result ID"}, status_code=400)
        
        success = DatabaseService.update_feedback(result_id, feedback)
        
        if success:
            logger.info(f"Updated feedback for result ID: {result_id}")
            return JSONResponse(content={"status": "success", "message": "Feedback saved successfully"})
        else:
            logger.error(f"Failed to update feedback for result ID: {result_id}")
            return JSONResponse(content={"error": "Failed to update feedback"}, status_code=500)
            
    except Exception as e:
        logger.error(f"Error saving feedback: {str(e)}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/results")
async def get_results(limit: int = 100):
    """Retrieve recent processing results"""
    try:
        results = DatabaseService.get_audio_results(limit)
        return {"results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Error retrieving results: {str(e)}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    logger.info(f"Starting FastAPI server on port {8587}")
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)
    
    uvicorn.run("src.controller.test:app", host="0.0.0.0", port=8587, reload=Config.DEBUG)