"""Parse JSON from iOS Shortcuts HealthKit queries."""

import json
from datetime import datetime
from typing import List, Optional
from dateutil import parser as date_parser
from apple_health_parser import SleepEntry


class HealthKitJSONParser:
    """Parse JSON from iOS Shortcuts."""
    
    WITHINGS_KEYWORDS = ["withings", "withings health mate"]
    
    def __init__(self, json_file_path: str):
        self.json_file_path = json_file_path
    
    def parse(self) -> List[SleepEntry]:
        """Extract all sleep entries from JSON."""
        with open(self.json_file_path, 'r') as f:
            data = json.load(f)
        
        samples = data if isinstance(data, list) else data.get('samples', [])
        
        entries = []
        for sample in samples:
            entry = self._parse_sample(sample)
            if entry:
                entries.append(entry)
        
        entries.sort(key=lambda x: x.start_date)
        return entries
    
    def _parse_sample(self, sample: dict) -> Optional[SleepEntry]:
        try:
            start_date = date_parser.parse(sample.get("startDate") or sample.get("start"))
            end_date = date_parser.parse(sample.get("endDate") or sample.get("end"))
            source_name = sample.get("sourceName", sample.get("source", "")).lower()
            device = sample.get("device", "")
            
            source = "Withings" if any(kw in f"{source_name} {device.lower()}" for kw in self.WITHINGS_KEYWORDS) else "iPhone"
            
            return SleepEntry(start_date, end_date, source, device, sample.get("value", "ASLEEP"))
        except:
            return None
    
    def get_iphone_entries(self, entries: List[SleepEntry]) -> List[SleepEntry]:
        return [e for e in entries if e.source == "iPhone"]
    
    def get_withings_entries(self, entries: List[SleepEntry]) -> List[SleepEntry]:
        return [e for e in entries if e.source == "Withings"]
