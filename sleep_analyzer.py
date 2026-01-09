"""Calculate sleep scores and assign emojis."""

from datetime import datetime, timedelta
from typing import List
from apple_health_parser import SleepEntry


class SleepScore:
    """Sleep score with emoji."""
    
    EMOJI_GREEN = "🟢"
    EMOJI_NEUTRAL = "😴"
    EMOJI_RED = "🔴"
    
    def __init__(self, score: float):
        self.score = max(0.0, min(100.0, score))
        self.emoji = self._score_to_emoji()
    
    def _score_to_emoji(self) -> str:
        if self.score >= 70:
            return self.EMOJI_GREEN
        elif self.score >= 50:
            return self.EMOJI_NEUTRAL
        else:
            return self.EMOJI_RED


class SleepAnalyzer:
    """Analyze sleep and calculate scores."""
    
    IDEAL_SLEEP_HOURS = 8.0
    MIN_SLEEP_HOURS = 6.0
    MAX_SLEEP_HOURS = 10.0
    
    def calculate_score(self, entry: SleepEntry) -> SleepScore:
        """Calculate sleep score."""
        hours = entry.duration_minutes / 60
        
        # Duration score (0-100)
        if hours < self.MIN_SLEEP_HOURS:
            duration_score = (hours / self.MIN_SLEEP_HOURS) * 50
        elif hours > self.MAX_SLEEP_HOURS:
            duration_score = max(0, 100 - (hours - self.MAX_SLEEP_HOURS) * 20)
        else:
            # Between min and ideal
            if hours <= self.IDEAL_SLEEP_HOURS:
                duration_score = 50 + (hours - self.MIN_SLEEP_HOURS) / (self.IDEAL_SLEEP_HOURS - self.MIN_SLEEP_HOURS) * 50
            else:
                duration_score = 100 - (hours - self.IDEAL_SLEEP_HOURS) / (self.MAX_SLEEP_HOURS - self.IDEAL_SLEEP_HOURS) * 10
        
        return SleepScore(duration_score)
    
    def merge_entries(self, iphone_entries: List[SleepEntry], withings_entries: List[SleepEntry]) -> List[SleepEntry]:
        """Merge iPhone and Withings entries - prefer Withings."""
        if not iphone_entries:
            return withings_entries
        if not withings_entries:
            return iphone_entries
        
        merged = []
        used_iphone = set()
        
        # For each Withings entry, check if there's an overlapping iPhone entry
        for withings in withings_entries:
            merged.append(withings)
            # Mark overlapping iPhone entries as used
            for i, iphone in enumerate(iphone_entries):
                if self._entries_overlap(withings, iphone):
                    used_iphone.add(i)
        
        # Add non-overlapping iPhone entries
        for i, iphone in enumerate(iphone_entries):
            if i not in used_iphone:
                merged.append(iphone)
        
        merged.sort(key=lambda x: x.start_date)
        return merged
    
    def _entries_overlap(self, entry1: SleepEntry, entry2: SleepEntry) -> bool:
        """Check if two sleep entries overlap."""
        return not (entry1.end_date <= entry2.start_date or entry2.end_date <= entry1.start_date)
