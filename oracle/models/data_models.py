from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class WindowInfo(BaseModel):
    window_id: int = Field(..., description="Unique window identifier from macOS Quartz")
    app_name: str = Field(..., description="Name of the application")
    title: str = Field("", description="Title of the window")
    bounds: dict = Field(..., description="Window bounds (x, y, width, height)")
    pid: int = Field(..., description="Process ID of the application")

class OCRResult(BaseModel):
    text: str = Field(..., description="Extracted text from the screenshot")
    confidence: float = Field(0.0, description="Confidence score of the OCR")
    has_text: bool = Field(False, description="True if useful text was extracted")

class ScreenshotResult(BaseModel):
    image_path: str = Field(..., description="Path to the captured screenshot file")
    window_info: Optional[WindowInfo] = Field(None, description="Metadata of the captured window")
    timestamp: datetime = Field(default_factory=datetime.now)
    is_temporary: bool = Field(True, description="True if the file was created for this session and should be cleaned up")

class LLMResponse(BaseModel):
    answer: str = Field(..., description="Answer from the local LLM")
    model: str = Field(..., description="Name of the model used")
    timestamp: datetime = Field(default_factory=datetime.now)

class InteractionLog(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    window_info: Optional[WindowInfo] = None
    question: str
    model: str
    ocr_text_excerpt: str
    response: str
    auto_typing_requested: bool
    status: str
    error_message: Optional[str] = None
