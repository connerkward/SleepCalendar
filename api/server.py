#!/usr/bin/env python3
"""FastAPI server for sleep calendar sync."""

import os
import sys
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from api.models import SyncRequest, SyncResponse
from api.sleep_calendar import SleepCalendar
from api.rate_limit import rate_limiter

app = FastAPI(
    title="Sleep Calendar API",
    description="Sync Apple Health sleep data to Google Calendar",
    version="1.0.0"
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware."""
    # Skip rate limiting for health checks
    if request.url.path in ["/", "/health"]:
        return await call_next(request)
    
    # Check rate limit
    allowed, error_msg = rate_limiter.check_rate_limit(request)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": error_msg,
                "error_code": "RATE_LIMIT_EXCEEDED"
            }
        )
    
    return await call_next(request)


@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "sleep-calendar-api"}


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/sync", response_model=SyncResponse)
def sync_sleep_data(request: SyncRequest):
    """
    Sync sleep data to Google Calendar.
    
    Creates or updates a per-user calendar named "Sleep Data - {email}"
    and syncs sleep events from the provided samples.
    """
    try:
        # Initialize calendar with user email
        cal = SleepCalendar(user_email=request.email)
        
        # Handle samples - can be list or newline-delimited JSON string
        samples = request.samples
        if isinstance(samples, str):
            # Parse newline-delimited JSON (from Shortcuts conversion)
            samples = [json.loads(line) for line in samples.strip().split('\n') if line.strip()]
        elif not isinstance(samples, list):
            # Convert to list if it's not already
            samples = list(samples) if samples else []
        
        # Sync data
        data = {"samples": samples}
        events_synced = cal.sync_from_data(data, user_email=request.email)
        
        # Build calendar URL
        calendar_url = f"https://calendar.google.com/calendar/embed?src={cal.calendar_id}"
        
        return SyncResponse(
            success=True,
            events_synced=events_synced,
            calendar_id=cal.calendar_id,
            calendar_url=calendar_url
        )
    
    except Exception as e:
        error_msg = str(e)
        print(f"Error syncing sleep data: {error_msg}", file=sys.stderr)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync sleep data: {error_msg}"
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
