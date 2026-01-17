#!/usr/bin/env python3
"""Delete all events from the Sleep Calendar."""

from sleep_data import SleepCalendar

cal = SleepCalendar()
cal.delete_all_events()
