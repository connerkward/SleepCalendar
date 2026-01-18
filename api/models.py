"""Pydantic models for API requests and responses."""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Dict, Any, Optional, Union
import json


class SleepSample(BaseModel):
    """Single sleep sample from HealthKit."""
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    value: Optional[str] = None
    sourceName: Optional[str] = None
    source: Optional[str] = None


class SyncRequest(BaseModel):
    """Request to sync sleep data."""
    email: EmailStr = Field(..., description="User email for calendar identification")
    samples: Union[List[Dict[str, Any]], str] = Field(..., description="List of sleep samples or newline-delimited JSON string")
    
    @field_validator('samples', mode='before')
    @classmethod
    def parse_samples(cls, v):
        """Accept both list and string (newline-delimited JSON)."""
        if isinstance(v, str):
            # Try parsing as newline-delimited JSON
            try:
                return [json.loads(line) for line in v.strip().split('\n') if line.strip()]
            except (json.JSONDecodeError, AttributeError):
                # If parsing fails, return as-is (will be handled in server)
                return v
        return v


class SyncResponse(BaseModel):
    """Response from sync endpoint."""
    success: bool
    events_synced: Optional[int] = None
    calendar_id: Optional[str] = None
    calendar_url: Optional[str] = None
    error: Optional[str] = None
