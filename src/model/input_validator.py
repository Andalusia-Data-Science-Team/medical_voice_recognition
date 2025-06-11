from .llm_service import LLMService
import logging
from ..core.config import Config
import re
from typing import List, Dict

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
    
    MEDICAL_KEYWORDS = {
            'symptoms': ['pain', 'fever', 'headache', 'nausea', 'fatigue', 'cough', 'shortness of breath', 'dizziness', 'chest pain', 'abdominal pain'],
            'body_parts': ['heart', 'lung', 'liver', 'kidney', 'brain', 'chest', 'abdomen', 'throat', 'stomach', 'back'],
            'medical_terms': ['diagnosis', 'treatment', 'medication', 'prescription', 'surgery', 'therapy', 'examination', 'assessment'],
            'measurements': ['blood pressure', 'temperature', 'pulse', 'weight', 'height', 'bpm', 'mmHg', 'celsius', 'fahrenheit'],
            'procedures': ['x-ray', 'mri', 'ct scan', 'ultrasound', 'blood test', 'ecg', 'ekg', 'biopsy'],
            'medications': ['tablet', 'capsule', 'injection', 'dose', 'mg', 'ml', 'antibiotic', 'analgesic'],
            'conditions': ['diabetes', 'hypertension', 'infection', 'inflammation', 'fracture', 'allergy']
        }

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
            # Fallback to keyword-based validation
            return MedicalValidator._fallback_validation(text)

    @staticmethod
    def _fallback_validation(text: str) -> dict:
        """Fallback keyword-based validation when LLM fails"""
        try:
            logger.info("Using fallback keyword-based validation")
            
            text_lower = text.lower()
            total_score = 0
            matched_categories = 0
            matched_keywords = []
            
            for category, keywords in MedicalValidator.MEDICAL_KEYWORDS.items():
                category_matches = 0
                for keyword in keywords:
                    if keyword.lower() in text_lower:
                        category_matches += 1
                        matched_keywords.append(keyword)
                
                if category_matches > 0:
                    matched_categories += 1
                    # Weight categories differently
                    if category in ['symptoms', 'medical_terms', 'procedures']:
                        total_score += category_matches * 15  # Higher weight
                    else:
                        total_score += category_matches * 10
            
            # Calculate confidence based on matches
            confidence = min(total_score, 95)  # Cap at 95%
            is_medical = confidence >= 30  # Threshold for medical content
            
            logger.info(f"Fallback validation - Confidence: {confidence}%, Medical: {is_medical}")
            logger.info(f"Matched keywords: {matched_keywords}")
            
            return {
                "is_medical": is_medical,
                "confidence": confidence,
                "classification": "MEDICAL" if is_medical else "NON_MEDICAL",
                "method": "fallback_keywords",
                "matched_keywords": matched_keywords,
                "matched_categories": matched_categories
            }
            
        except Exception as e:
            logger.error(f"Fallback validation failed: {str(e)}")
            # Ultimate fallback - assume it's medical to avoid blocking valid content
            return {
                "is_medical": True,
                "confidence": 50,
                "classification": "MEDICAL",
                "method": "emergency_fallback",
                "error": str(e)
            }

    def _extract_confidence_score(self, text: str) -> int:
        """Extract confidence score from various response formats"""
        # Look for patterns like "95", "95%", "confidence: 95", etc.
        patterns = [
            r'(\d+)%',
            r'confidence[:\s]+(\d+)',
            r'score[:\s]+(\d+)',
            r'\|(\d+)',
            r'(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                return min(max(score, 0), 100)  # Ensure score is between 0-100
        
        return 50  # Default confidence if no score found