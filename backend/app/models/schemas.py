from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class OCRRequest(BaseModel):
    engine: Optional[str] = "tesseract"
    language: Optional[str] = "eng"

class OCRResponse(BaseModel):
    task_id: str
    status: str
    timestamp: datetime
