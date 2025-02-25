from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from analyzer_engine import get_analyzer
from anonymizer_engine import get_anonymizer
from presidio_anonymizer.entities import OperatorConfig
from pydantic import BaseModel, Field
import logging
import os
from typing import Optional

# Ensure a 'logs' directory exists
os.makedirs('logs', exist_ok=True)

# Logging Configuration
logging.basicConfig(
    filename='logs/anonymization.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = FastAPI()

# CORS configuration
origins = [
    "http://localhost:3000",  # React frontend
    # Add other origins as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enhanced request model for more flexibility
class AnonymizeRequest(BaseModel):
    text: str
    language: Optional[str] = Field("en", description="Language code for analysis (default: en)")
    anonymization_method: Optional[str] = Field("mask", description="Anonymization method: mask, redact, hash, replace")
    masking_char: Optional[str] = Field("*", description="Character used for masking")
    chars_to_mask: Optional[int] = Field(6, description="Number of characters to mask")
    from_end: Optional[bool] = Field(False, description="Mask from end if True")

@app.post("/anonymize/")
async def anonymize_text(request: AnonymizeRequest):
    analyzer = get_analyzer()
    anonymizer = get_anonymizer()

    analyzer_results = analyzer.analyze(text=request.text, language=request.language)

    operator_config = OperatorConfig(
        operator_name=request.anonymization_method,
        params={
            "masking_char": request.masking_char,
            "chars_to_mask": request.chars_to_mask,
            "from_end": request.from_end
        }
    )

    anonymized_results = anonymizer.anonymize(
        text=request.text,
        analyzer_results=analyzer_results,
        operators={"DEFAULT": operator_config}
    )

    # Log anonymization events with more details
    logging.info(
        f"Request Anonymized | Method: {request.anonymization_method} | Language: {request.language} | Original: '{request.text}' | Anonymized: '{anonymized_results.text}'"
    )

    return {
        "original_text": request.text,
        "anonymized_text": anonymized_results.text,
        "method_used": request.anonymization_method,
        "language": request.language
    }
