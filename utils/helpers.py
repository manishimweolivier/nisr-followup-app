"""
General Helper Utilities for FollowUp
Date checks, safe conversions, and CSV export helpers.
"""

from datetime import datetime, date, timedelta
from typing import Optional, Union, List, Dict
import pandas as pd
import io

def parse_iso_date(val: Optional[Union[str, date, datetime]]) -> Optional[date]:
    """Parse string or date into a python date object."""
    if not val:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        val_clean = val.strip().split(" ")[0].split("T")[0]
        try:
            return date.fromisoformat(val_clean)
        except Exception:
            return None
    return None

def is_date_overdue(scheduled_date_str: str, current_reference_date: Optional[date] = None) -> bool:
    """
    Check if a scheduled date is in the past relative to today (or reference date).
    Strict rule: Never consider an appointment overdue before or on its scheduled date.
    """
    target = parse_iso_date(scheduled_date_str)
    if not target:
        return False
    ref = current_reference_date or date.today()
    return target < ref

def is_date_due_today(scheduled_date_str: str, current_reference_date: Optional[date] = None) -> bool:
    """Check if scheduled date is exactly today."""
    target = parse_iso_date(scheduled_date_str)
    if not target:
        return False
    ref = current_reference_date or date.today()
    return target == ref

def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Convert pandas DataFrame to UTF-8 encoded CSV bytes for download."""
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue().encode('utf-8')
