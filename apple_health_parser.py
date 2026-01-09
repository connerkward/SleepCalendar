"""Parse Apple Health XML export files."""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional
from dateutil import parser as date_parser


class SleepEntry:
    """Sleep entry from Apple Health."""
    
    def __init__(self, start_date: datetime, end_date: datetime, source: str, device: Optional[str] = None, value: str = "ASLEEP"):
        self.start_date = start_date
        self.end_date = end_date
        self.source = source
        self.device = device
        self.value = value
        self.duration_minutes = (end_date - start_date).total_seconds() / 60


class AppleHealthParser:
    """Parse Apple Health XML."""
    
    SLEEP_ANALYSIS_TYPE = "HKCategoryTypeIdentifierSleepAnalysis"
    WITHINGS_KEYWORDS = ["withings", "withings health mate"]
    
    def __init__(self, xml_file_path: str):
        self.xml_file_path = xml_file_path
    
    def parse(self) -> List[SleepEntry]:
        """Extract all sleep entries."""
        tree = ET.parse(self.xml_file_path)
        root = tree.getroot()
        
        entries = []
        for record in root.findall(".//Record"):
            if record.get("type") == self.SLEEP_ANALYSIS_TYPE:
                entry = self._parse_record(record)
                if entry:
                    entries.append(entry)
        
        entries.sort(key=lambda x: x.start_date)
        return entries
    
    def _parse_record(self, record: ET.Element) -> Optional[SleepEntry]:
        try:
            start_date = date_parser.parse(record.get("startDate"))
            end_date = date_parser.parse(record.get("endDate"))
            source_name = record.get("sourceName", "").lower()
            device_name = record.get("device", "").lower()
            
            source = "Withings" if any(kw in f"{source_name} {device_name}" for kw in self.WITHINGS_KEYWORDS) else "iPhone"
            
            return SleepEntry(start_date, end_date, source, record.get("device"), record.get("value", "ASLEEP"))
        except:
            return None
    
    def get_iphone_entries(self, entries: List[SleepEntry]) -> List[SleepEntry]:
        return [e for e in entries if e.source == "iPhone"]
    
    def get_withings_entries(self, entries: List[SleepEntry]) -> List[SleepEntry]:
        return [e for e in entries if e.source == "Withings"]
