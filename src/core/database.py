import sqlite3
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for database operations"""
    
    DB_PATH = "app_data.db"
    
    @classmethod
    def initialize_db(cls):
        """Create database tables if they don't exist"""
        try:
            conn = sqlite3.connect(cls.DB_PATH)
            cursor = conn.cursor()
            
            # Create table for audio processing results
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS audio_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                language TEXT NOT NULL,
                model TEXT NOT NULL,
                is_conversation BOOLEAN NOT NULL,
                raw_text TEXT,
                arabic_text TEXT,
                translation_text TEXT,
                json_data TEXT,
                reasoning TEXT,
                preprocessing_time REAL,
                voice_processing_time REAL,
                llm_processing_time REAL,
                doctor_name TEXT,
                feedback TEXT,
                insertion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            conn.commit()
            logger.info(f"Database initialized at {cls.DB_PATH}")
            return True
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()

    @classmethod
    def save_audio_result(cls, 
                          filename, 
                          language, 
                          model, 
                          is_conversation, 
                          raw_text, 
                          arabic_text, 
                          translation_text, 
                          json_data, 
                          reasoning, 
                          preprocessing_time, 
                          voice_processing_time, 
                          llm_processing_time,
                          doctor_name=None,
                          feedback=None):
        """Save audio processing results to database"""
        try:
            conn = sqlite3.connect(cls.DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO audio_results 
            (filename, language, model, is_conversation, raw_text, arabic_text, translation_text, 
            json_data, reasoning, preprocessing_time, voice_processing_time, llm_processing_time,
            doctor_name, feedback)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                filename, 
                language, 
                model, 
                is_conversation, 
                raw_text, 
                arabic_text, 
                translation_text, 
                json_data, 
                reasoning, 
                preprocessing_time, 
                voice_processing_time, 
                llm_processing_time,
                doctor_name,
                feedback
            ))
            
            conn.commit()
            result_id = cursor.lastrowid
            logger.info(f"Saved audio result with ID: {result_id}")
            return result_id
        except Exception as e:
            logger.error(f"Error saving audio result: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()
    
    @classmethod
    def get_audio_results(cls, limit=100):
        """Get recent audio processing results"""
        try:
            conn = sqlite3.connect(cls.DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM audio_results
            ORDER BY insertion_date DESC
            LIMIT ?
            ''', (limit,))
            
            results = [dict(row) for row in cursor.fetchall()]
            logger.info(f"Retrieved {len(results)} audio results")
            return results
        except Exception as e:
            logger.error(f"Error retrieving audio results: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()


    @classmethod
    def update_feedback(cls, result_id, feedback):
        """
        Update the feedback for an existing audio result record.
        
        Args:
            result_id: The ID of the result to update
            feedback: The new feedback text
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(cls.DB_PATH)
            cursor = conn.cursor()
            
            # Update the feedback field
            query = """
            UPDATE audio_results 
            SET feedback = ?
            WHERE id = ?
            """
            
            cursor.execute(query, (feedback, result_id))
            conn.commit()
            
            # Check if any rows were affected
            if cursor.rowcount > 0:
                logger.info(f"Updated feedback for result ID: {result_id}")
                return True
            else:
                logger.warning(f"No record found with ID: {result_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating feedback in database: {str(e)}", exc_info=True)
            return False
        finally:
            if conn:
                conn.close()