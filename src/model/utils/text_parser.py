import json
import re

def parse_refined_text_voice(refined_text):
    """Parse the refined text into structured data."""
    try:
        # Extract sections using regex
        refined_section = re.search(r"# SECTION 1: REFINED ARABIC TEXT(.*?)# SECTION 2:", refined_text, re.DOTALL)
        translation_section = re.search(r"# SECTION 2: ENGLISH TRANSLATION(.*?)# SECTION 3:", refined_text, re.DOTALL)
        json_section = re.search(r"# SECTION 3: PATIENT DATA \(JSON FORMAT\)(.*?)# SECTION 4:", refined_text, re.DOTALL)
        reasoning_section = re.search(r"# SECTION 4: ANALYSIS NOTES(.*)", refined_text, re.DOTALL)

        parsed_text = refined_section.group(1).strip() if refined_section else ""
        translate = translation_section.group(1).strip() if translation_section else ""
        # Parse JSON data
        json_data = {}
        if json_section:
            json_text = json_section.group(1).strip()
            # Find JSON object in text
            json_match = re.search(r'\{.*\}', json_text, re.DOTALL)
            if json_match:
                try:
                    json_data = json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    json_data = {"error": "Invalid JSON format"}
        
        reasoning = reasoning_section.group(1).strip() if reasoning_section else ""
        
        return parsed_text, translate, json_data, reasoning
    except Exception as e:
        raise Exception(f"Failed to parse refined text: {str(e)}")
    

def parse_refined_text(refined_text):
    """
    Parse the refined text into structured data, handling JSON within backticks.
    
    Args:
        refined_text (str): The input text containing patient features and reasoning
    
    Returns:
        tuple: A tuple containing parsed JSON data and reasoning text
    """
    try:
        # Extract JSON section, including handling of backticks and code block
        json_section = re.search(r"1\.\s*Fill Patient Features:\s*(?:```json)?\s*({[^}]+})\s*(?:```)?", refined_text, re.DOTALL)
        reasoning_section = re.search(r"2\.\s*Reasoning:\s*(.*)", refined_text, re.DOTALL)
        
        # Parse JSON data
        json_data = {}
        if json_section:
            json_text = json_section.group(1).strip()
            try:
                # Replace NULL with null for JSON compatibility
                json_text = json_text.replace('NULL', 'null')
                print(json_text)
                json_data = json.loads(json_text)
            except json.JSONDecodeError:
                json_data = {"error": "Invalid JSON format"}
        
        # Extract reasoning
        reasoning = ""
        if reasoning_section:
            reasoning = reasoning_section.group(1).strip()
        
        return json_data, reasoning
    
    except Exception as e:
        raise Exception(f"Failed to parse refined text: {str(e)}")
    


def parse_refined_text_voice2(refined_text):
    """Parse the refined text into structured data."""
    try:
        # Extract sections using regex
        json_section = re.search(r"# SECTION 1: PATIENT DATA \(JSON FORMAT\)(.*?)# SECTION 2:", refined_text, re.DOTALL)
        reasoning_section = re.search(r"# SECTION 2: ANALYSIS NOTES(.*)", refined_text, re.DOTALL)

        # Parse JSON data
        json_data = {}
        if json_section:
            json_text = json_section.group(1).strip()
            # Find JSON object in text
            json_match = re.search(r'\{.*\}', json_text, re.DOTALL)
            if json_match:
                try:
                    json_data = json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    json_data = {"error": "Invalid JSON format"}
        
        reasoning = reasoning_section.group(1).strip() if reasoning_section else ""
        
        return json_data, reasoning
    except Exception as e:
        raise Exception(f"Failed to parse refined text: {str(e)}")
    
