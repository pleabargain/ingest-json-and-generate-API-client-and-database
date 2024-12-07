from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4

class PseudoCodeStep(BaseModel):
    step: int
    description: str
    pseudoCode: List[str]

class OutputContent(BaseModel):
    steps: List[PseudoCodeStep]

class LogEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    model: str
    input: str
    output: OutputContent
    response_time_seconds: float
    timestamp: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "model": "claude-3-opus-20240229",
                "input": "sample input text",
                "output": {
                    "steps": [
                        {
                            "step": 1,
                            "description": "Sample step",
                            "pseudoCode": ["line 1", "line 2"]
                        }
                    ]
                },
                "response_time_seconds": 19.605,
                "timestamp": "2024-12-07T11:58:11.653232"
            }
        }

class ValidationError(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error_type: str
    error_message: str
    data_snapshot: Dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2024-03-14T12:00:00",
                "error_type": "SchemaValidationError",
                "error_message": "Invalid JSON structure",
                "data_snapshot": {"partial_data": "error context"}
            }
        }
