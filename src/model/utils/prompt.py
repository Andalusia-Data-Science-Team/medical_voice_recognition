def get_refine_arabic_prompt_deepseek(raw_text):
    return f"""
    Correct the grammar and structure of this Arabic medical text and try to ignore the names of the speakers. 
    Return only the corrected Arabic text with no additional explanations.

    ORIGINAL TEXT:
    \"\"\"{raw_text}\"\"\"
    """


def get_refine_arabic_prompt_deepseek_conv(raw_text):
    return f"""
    Analyze this Arabic medical conversation in different dialects and format it properly it usually starts with greeting from one of the speakers:
    
    1. Identify speakers based on these clear role indicators:
       - DOCTOR: The person who asks questions, examines the patient, provides diagnoses, and recommends treatments
       - PATIENT: The person who describes symptoms, answers questions, explains concerns, and shares their medical history
    
    2. Format the conversation by labeling each speaker as **DOCTOR:** or **PATIENT:** before their dialogue
    
    3. Return ONLY the properly formatted Arabic dialogue with speaker labels, without any additional commentary or explanation
    
    ORIGINAL TEXT:
    \"\"\"{raw_text}\"\"\"
    """


def get_translation_prompt_deepseek_conv(refined_text):
    return f"""
    Translate this Arabic medical conversation to English.
    Preserve speaker labels (**DOCTOR:** and **PATIENT:**).
    Return only the English translation without commentary.

    ARABIC TEXT:
    \"\"\"{refined_text}\"\"\"
    """


def get_translation_prompt_deepseek(refined_text):
    return f"""
    Translate this Arabic medical text to English.
    Return only the English translation without commentary.

    ARABIC TEXT:
    \"\"\"{refined_text}\"\"\"
    """


def get_extraction_prompt_deepseek(translated_text):
    return f"""
    Extract patient information from this medical text into exactly two sections:

    # SECTION 1: PATIENT DATA (JSON FORMAT)
    ```json
    {{
    "chief_complaint": "",
    "icd10_codes": [
        "Code1 - Description",
        "Code2 - Description"
    ],
    "history_of_illness": "",
    "current_medication": "",
    "imaging_results": "",
    "plan": "",
    "assessment": "",
    "follow_up": ""
    }}
    ```

    # SECTION 2: ANALYSIS NOTES
    Brief justification for data extraction and ICD10 code selections.

    Rules:
    - Use 'null' for missing data
    - Include all relevant ICD10 codes with descriptions
    - Properly format JSON with no explanatory text inside

    TEXT:
    \"\"\"{translated_text}\"\"\"
    """


def get_extraction_prompt_llama(translated_text):
    return f"""
    Extract patient information into JSON format and provide brief analysis.
    Return only these two sections:

    # SECTION 1: PATIENT DATA (JSON FORMAT)
    ```json
    {{
    "chief_complaint": "",
    "icd10_codes": [
        "Code1 - Description",
        "Code2 - Description",
        "Code3 - Description"
    ],
    "history_of_illness": "",
    "current_medication": "",
    "imaging_results": "",
    "plan": "",
    "assessment": "",
    "follow_up": ""
    }}
    ```

    # SECTION 2: ANALYSIS NOTES
    Brief justification for extracted data and ICD10 codes.

    IMPORTANT:
    - Include all relevant ICD10 codes that apply to the patient's condition
    - List both primary and secondary diagnosis codes
    - Provide specific, detailed code descriptions for each ICD10 code
    - Ensure codes accurately match the medical conditions described in the text

    TEXT TO ANALYZE:
    \"\"\"{translated_text}\"\"\"
    """
def get_refine_english_prompt_deepseek(translated_text):
    return f"""
    Correct the grammar and structure of this English medical text.
    Return only the corrected English text with no additional explanations.
    ORIGINAL TEXT:
\"\"\"{translated_text}\"\"\"
    """

def get_refine_english_prompt_deepseek_conv(translated_text):
    return f"""
    Refine this English medical conversation while preserving speaker labels:
    1. Fix any grammatical errors or awkward phrasing
    2. Ensure medical terminology is used correctly
    3. Maintain the conversational flow and natural dialogue
    4. Preserve the **DOCTOR:** and **PATIENT:** labels
    
    Return ONLY the refined English conversation without any additional commentary.
    ORIGINAL TEXT:
\"\"\"{translated_text}\"\"\"
    """

def get_refine_arabic_prompt_llama(raw_text):
    return f"""
SYSTEM: You are a medical language processor that outputs ONLY corrected text with NO explanations.

USER: Correct this Arabic medical text:
\"\"\"{raw_text}\"\"\"

ASSISTANT:
"""

def get_refine_arabic_prompt_llama_conv(raw_text):
    return f"""
SYSTEM: You are an Arabic medical transcription system that outputs ONLY formatted text with speaker labels. Any additional text will trigger system errors.

USER: Format with **DOCTOR:** and **PATIENT:** labels:
\"\"\"{raw_text}\"\"\"

ASSISTANT:
"""

def get_translation_prompt_llama(refined_text):
    return f"""
SYSTEM: You are a translation system that outputs ONLY the English translation with NO explanations.

USER: Translate to English:
\"\"\"{refined_text}\"\"\"

ASSISTANT:
"""

def get_translation_prompt_llama_conv(refined_text):
    return f"""
SYSTEM: You are a translation system that outputs ONLY the English translation with speaker labels preserved. No explanations.

USER: Translate with **DOCTOR:** and **PATIENT:** labels:
\"\"\"{refined_text}\"\"\"

ASSISTANT:
"""

def get_refine_english_prompt_llama(translated_text):
    return f"""
SYSTEM: You are a text processor that outputs ONLY the corrected English text with NO explanations.

USER: Correct this medical text:
\"\"\"{translated_text}\"\"\"

ASSISTANT:
"""

def get_refine_english_prompt_llama_conv(translated_text):
    return f"""
SYSTEM: You are a text processor that outputs ONLY the refined English conversation with speaker labels. No explanations.

USER: Refine this conversation:
\"\"\"{translated_text}\"\"\"

ASSISTANT:
"""