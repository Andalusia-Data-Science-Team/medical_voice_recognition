from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
import time
import pandas as pd
import logging
from typing import Optional, Generator
import os
import uvicorn
import json
import asyncio
import sys
from collections import defaultdict

# Import services
from ..core.config import Config
from ..core.database import DatabaseService
from ..model.speech_service import SpeechService
from ..model.input_validator import MedicalValidator
from ..model.refine_text import RefineText
from ..model.translation import Translate
from ..model.extract_features import ExtractFeature
from ..model.auth import AuthService

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize FastAPI app
app = FastAPI(title="Audio Processing API")

# Store cancellation events per user_id
cancel_events = defaultdict(asyncio.Event)

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

@app.post("/register")
async def register(
    username: str = Form(...),
    password: str = Form(...)
):
    """Register a new user."""
    try:
        hashed_password = AuthService.hash_password(password)
        user_id = DatabaseService.register_user(username, hashed_password)
        access_token = AuthService.create_access_token({"sub": username})
        logger.info(f"User registered successfully: {username}")
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post("/change-password")
async def change_password(
    request: Request,
    current_user: dict = Depends(AuthService.get_current_user)
):
    """Change the user's password."""
    try:
        data = await request.json()
        current_password = data.get("current_password")
        new_password = data.get("new_password")
        
        if not current_password or not new_password:
            raise HTTPException(status_code=400, detail="Current and new passwords are required")
        
        user = DatabaseService.verify_user(current_user["username"])
        if not AuthService.verify_password(current_password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Incorrect current password")
        
        hashed_new_password = AuthService.hash_password(new_password)
        success = DatabaseService.update_user_password(username = user["username"], new_pass = hashed_new_password)
        
        if success:
            logger.info(f"Password updated for user: {current_user['username']}")
            return {"status": "success", "message": "Password updated successfully"}
        else:
            logger.error(f"Failed to update password for user: {current_user['username']}")
            raise HTTPException(status_code=500, detail="Failed to update password")
            
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error changing password: {str(e)}")

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate a user and return a JWT token."""
    user = DatabaseService.verify_user(form_data.username)
    if not user or not AuthService.verify_password(form_data.password, user["hashed_password"]):
        logger.warning(f"Login failed for username: {form_data.username}")
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    access_token = AuthService.create_access_token({"sub": form_data.username})
    logger.info(f"User logged in: {form_data.username}")
    # Clear any existing cancellation event
    cancel_events[user["id"]].clear()
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/cancel")
async def cancel_processing(current_user: dict = Depends(AuthService.get_current_user)):
    """Cancel the ongoing audio processing for the current user."""
    user_id = current_user["id"]
    cancel_events[user_id].set()
    logger.info(f"Cancellation requested for user_id: {user_id}")
    return {"status": "cancellation_requested"}

@app.post("/upload")
async def upload(
    audio: UploadFile = File(...),
    language: str = Form("en"),
    model: str = Form("deepseek"),
    isConversation: Optional[str] = Form(None),
    doctorName: Optional[str] = Form(None),
    feedback: Optional[str] = Form(None),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """Handle file uploads and stream processing results for authenticated users."""
    user_id = current_user["id"]
    logger.info(f"Received upload request from user: {current_user['username']}")
    
    # Reset cancellation event for this user
    cancel_events[user_id].clear()
    
    # Check conversational mode
    conversational_mode = isConversation == 'on'
    logger.info(f"Upload parameters: language={language}, model={model}, conversational_mode={conversational_mode}")
    logger.info(f"Doctor: {doctorName}")
    
    # Determine if the file is a recording (temporary) or uploaded (persistent)
    is_recording = audio.filename.startswith("recording_")
    
    # Set filename for recorded audio
    if audio.filename == "":
        audio.filename = f"recorded_audio_{int(time.time())}.wav"
        is_recording = True
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
    
    async def stream_results() -> Generator[str, None, None]:
        """Stream processing results as they become available."""
        partial_results = {
            "filename": audio.filename,
            "language": language,
            "model": model,
            "is_conversation": conversational_mode,
            "doctor_name": doctorName,
            "feedback": feedback,
            "preprocessing_time": 0.0,
            "voice_processing_time": 0.0,
            "llm_processing_time": 0.0
        }
        
        try:
            # Step 1: Transcribe audio
            logger.info("Starting transcription")
            try:
                transcripted_text = SpeechService.transcribe_audio(file_path, Config.FIREWORKS_API_KEY, language)
                if not transcripted_text:
                    raise ValueError("Transcription returned empty text")
                partial_results["raw_text"] = transcripted_text
                yield json.dumps({"step": "transcription", "data": transcripted_text}) + "\n"
            except Exception as e:
                logger.error(f"Transcription error: {str(e)}", exc_info=True)
                yield json.dumps({"step": "error", "data": f"Transcription failed: {str(e)}"}) + "\n"
                return
            if cancel_events[user_id].is_set():
                logger.info(f"Processing cancelled after transcription for user_id: {user_id}")
                async for result in save_partial_results(partial_results, user_id):
                    yield result
                return
            await asyncio.sleep(0.1)

            # Step 1.5: Validate if the text is medical
            logger.info("Starting medical validation")
            try:
                result = MedicalValidator.validate_medical_content(transcripted_text)
                classification = result.get("classification", "NON_MEDICAL")
                confidence = result.get("confidence", 0.0)
                validation_data = {
                    "is_medical": classification == "MEDICAL",
                    "confidence": confidence,
                    "classification": classification,
                    "method": "llm_validation",
                    "raw_response": result
                }
                if not validation_data["is_medical"]:
                    logger.info(f"Non-medical audio detected for user_id: {user_id}")
                    yield json.dumps({"step": "error", "data": "Non-medical audio detected. Please upload medical-related audio."}) + "\n"
                    partial_results["reasoning"] = "Processing stopped due to non-medical audio"
                    async for result in save_partial_results(partial_results, user_id):
                        yield result
                    return
            except Exception as e:
                logger.error(f"Medical validation error: {str(e)}", exc_info=True)
                yield json.dumps({"step": "error", "data": f"Medical validation failed: {str(e)}"}) + "\n"
                return
            if cancel_events[user_id].is_set():
                logger.info(f"Processing cancelled after validation for user_id: {user_id}")
                async for result in save_partial_results(partial_results, user_id):
                    yield result
                return
            await asyncio.sleep(0.1)

            # Step 2: Refine text
            logger.info("Starting text refinement")
            try:
                refined_text = RefineText.refining_transcription(transcripted_text, conversational_mode, model="deepseek", language=language)
                partial_results["arabic_text"] = refined_text
                yield json.dumps({"step": "refinement", "data": refined_text}) + "\n"
            except Exception as e:
                logger.error(f"Refinement error: {str(e)}", exc_info=True)
                yield json.dumps({"step": "error", "data": f"Refinement failed: {str(e)}"}) + "\n"
                return
            if cancel_events[user_id].is_set():
                logger.info(f"Processing cancelled after refinement for user_id: {user_id}")
                async for result in save_partial_results(partial_results, user_id):
                    yield result
                return
            await asyncio.sleep(0.1)

            # Step 3: Translate if needed
            logger.info("Starting translation")
            try:
                if language == "ar":
                    end_text = Translate.translate(refined_text, conversational_mode, model="deepseek")
                else:
                    end_text = refined_text
                partial_results["translation_text"] = end_text
                yield json.dumps({"step": "translation", "data": end_text}) + "\n"
            except Exception as e:
                logger.error(f"Translation error: {str(e)}", exc_info=True)
                yield json.dumps({"step": "error", "data": f"Translation failed: {str(e)}"}) + "\n"
                return
            if cancel_events[user_id].is_set():
                logger.info(f"Processing cancelled after translation for user_id: {user_id}")
                async for result in save_partial_results(partial_results, user_id):
                    yield result
                return
            await asyncio.sleep(0.1)

            # Step 4: Extract features
            logger.info("Starting feature extraction")
            try:
                json_data, reasoning = ExtractFeature.extract(end_text, conversational_mode)
                partial_results["json_data"] = json.dumps(json_data) if isinstance(json_data, (dict, list)) else json_data
                partial_results["reasoning"] = reasoning
                yield json.dumps({"step": "feature_extraction", "data": {"json_data": json_data, "reasoning": reasoning}}) + "\n"
            except Exception as e:
                logger.error(f"Feature extraction error: {str(e)}", exc_info=True)
                yield json.dumps({"step": "error", "data": f"Feature extraction failed: {str(e)}"}) + "\n"
                return
            if cancel_events[user_id].is_set():
                logger.info(f"Processing cancelled after feature extraction for user_id: {user_id}")
                async for result in save_partial_results(partial_results, user_id):
                    yield result
                return
            await asyncio.sleep(0.1)

            # Step 5: Save to database
            logger.info("Saving to database")
            try:
                result_id = DatabaseService.save_audio_result(**partial_results, user_id=user_id)
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
            try:
                if is_recording and os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up temporary recording file: {file_path}")
            except Exception as e:
                logger.error(f"Error cleaning up file: {str(e)}")

    async def save_partial_results(results: dict, user_id: int):
        """Save partial results to database upon cancellation."""
        try:
            results["reasoning"] = results.get("reasoning", "Processing cancelled by user")
            result_id = DatabaseService.save_audio_result(
                user_id=user_id,
                filename=results.get("filename", "cancelled_audio"),
                language=results.get("language", "unknown"),
                model=results.get("model", "unknown"),
                is_conversation=results.get("is_conversation", False),
                raw_text=results.get("raw_text"),
                arabic_text=results.get("arabic_text"),
                translation_text=results.get("translation_text"),
                json_data=results.get("json_data"),
                reasoning=results.get("reasoning"),
                preprocessing_time=results.get("preprocessing_time", 0.0),
                voice_processing_time=results.get("voice_processing_time", 0.0),
                llm_processing_time=results.get("llm_processing_time", 0.0),
                doctor_name=results.get("doctor_name"),
                feedback=results.get("feedback")
            )
            logger.info(f"Saved partial results with ID: {result_id}")
            yield json.dumps({"step": "database_save", "data": {"result_id": result_id}}) + "\n"
        except Exception as e:
            logger.error(f"Error saving partial results: {str(e)}")
            yield json.dumps({"step": "error", "data": f"Partial results save failed: {str(e)}"}) + "\n"

    return StreamingResponse(stream_results(), media_type="text/event-stream")

@app.post("/save-feedback")
async def save_feedback(request: Request, current_user: dict = Depends(AuthService.get_current_user)):
    """Save feedback for an existing result."""
    try:
        data = await request.json()
        result_id = data.get("result_id")
        feedback = data.get("feedback")
        
        if not result_id:
            return JSONResponse(content={"error": "Missing result ID"}, status_code=400)
        
        success = DatabaseService.update_feedback(result_id, feedback)
        
        if success:
            logger.info(f"Updated feedback for result ID: {result_id} by user: {current_user['username']}")
            return JSONResponse(content={"status": "success", "message": "Feedback saved successfully"})
        else:
            logger.error(f"Failed to update feedback for result ID: {result_id}")
            return JSONResponse(content={"error": "Failed to update feedback"}, status_code=500)
            
    except Exception as e:
        logger.error(f"Error saving feedback: {str(e)}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/results")
async def get_results(limit: int = 100, current_user: dict = Depends(AuthService.get_current_user)):
    """Retrieve recent processing results for authenticated user"""
    try:
        results = DatabaseService.get_audio_results(limit)
        # Filter results for the current user
        user_results = [result for result in results if result["user_id"] == current_user["id"]]
        return {"results": user_results, "count": len(user_results)}
    except Exception as e:
        logger.error(f"Error retrieving results: {str(e)}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    logger.info(f"Starting FastAPI server on port {8587}")
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)
    
    uvicorn.run("src.controller.test:app", host="0.0.0.0", port=8587, reload=Config.DEBUG)