from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import time
import pandas as pd
import logging
from typing import Optional
import os
import uvicorn
import json
from datetime import datetime
import sys

# Import your services
from ..core.config import Config
from ..model.pipeline import DataPipeline
from ..core.database import DatabaseService

# Initialize logger
logger = logging.getLogger(__name__)

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

# Modify the existing upload endpoint to not require feedback initially
@app.post("/upload")
async def upload(
    audio: UploadFile = File(...),
    language: str = Form("en"),
    model: str = Form("deepseek"),
    isConversation: Optional[str] = Form(None),
    doctorName: Optional[str] = Form(None),  # Keep doctor name field
    feedback: Optional[str] = Form(None)     # Make feedback optional (it will be populated later)
):
    """Handle file uploads and processing."""
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
        # Create a temporary file object
        contents = await audio.read()
        file_path = os.path.join(Config.UPLOAD_FOLDER, audio.filename)
        
        # Ensure upload directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write file
        with open(file_path, "wb") as f:
            f.write(contents)
        logger.info(f"File saved to {file_path}")
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
    try:
        logger.info("Starting batch processing mode")
        
        # Process the uploaded file
        response_data = DataPipeline.process_batch(file_path, language, model, conversational_mode)
        
        # Save results to database
        json_data_str = json.dumps(response_data["json_data"]) if isinstance(response_data["json_data"], (dict, list)) else response_data["json_data"]
        
        # Store in database with new fields (feedback is initially empty or with minimal value)
        result_id = DatabaseService.save_audio_result(
            filename=audio.filename,
            language=language,
            model=model,
            is_conversation=conversational_mode,
            raw_text=response_data["raw_text"],
            arabic_text=response_data["arabic_text"],
            translation_text=response_data["translation_text"],
            json_data=json_data_str,
            reasoning=response_data["reasoning"],
            preprocessing_time=response_data["preprocessing_time"],
            voice_processing_time=response_data["voice_processing_time"],
            llm_processing_time=3,
            doctor_name=doctorName,
            feedback=""  # Initially empty, will be populated via the save-feedback endpoint
        )
        
        logger.info(f"Saved processing result to database with ID: {result_id}")
        
        # Return the response
        return {
            "raw_text": response_data["raw_text"],
            "refine_text": response_data["arabic_text"],
            "translation_text": response_data["translation_text"],
            "json_data": response_data["json_data"],
            "reasoning": response_data["reasoning"],
            "preprocessing_time": response_data["preprocessing_time"],
            "voice_processing_time": response_data["voice_processing_time"],
            "doctor_name": doctorName,
            "saved_to_db": result_id  # Return the actual ID so we can use it for saving feedback
        }
    except Exception as e:
        logger.error(f"Error in batch processing: {str(e)}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
@app.post("/save-feedback")
async def save_feedback(request: Request):
    """Save feedback for an existing result."""
    try:
        # Get JSON data from request
        data = await request.json()
        result_id = data.get("result_id")
        feedback = data.get("feedback")
        
        if not result_id:
            return JSONResponse(content={"error": "Missing result ID"}, status_code=400)
        
        # Update the feedback in the database
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

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Display dashboard with stored results."""
    try:
        results = DatabaseService.get_audio_results(limit=50)
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "results": results
        })
    except Exception as e:
        logger.error(f"Error displaying dashboard: {str(e)}", exc_info=True)
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
    
    # Add project root to Python path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)
    
    uvicorn.run("src.controller.app:app", host="0.0.0.0", port=8587, reload=Config.DEBUG)
