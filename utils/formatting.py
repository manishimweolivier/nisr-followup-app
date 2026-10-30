"""
Formatting and Presentation Helpers for FollowUp
Ensures consistent clinical typography, status tags, and healthcare date displays.
"""

from datetime import datetime, date
from typing import Optional, Union

def format_date(dt_val: Optional[Union[str, date, datetime]], default: str = "Not Specified") -> str:
    """Format dates into readable standard representation: DD MMM YYYY."""
    if not dt_val:
        return default
    
    if isinstance(dt_val, str):
        dt_clean = dt_val.strip()
        if not dt_clean:
            return default
        try:
            # Handle ISO formats
            if "T" in dt_clean:
                dt_obj = datetime.fromisoformat(dt_clean.replace("Z", "+00:00"))
            else:
                parts = dt_clean.split(" ")[0].split("-")
                if len(parts) == 3:
                    dt_obj = date(int(parts[0]), int(parts[1]), int(parts[2]))
                else:
                    return dt_clean
        except Exception:
            return dt_clean
    elif isinstance(dt_val, datetime):
        dt_obj = dt_val.date()
    elif isinstance(dt_val, date):
        dt_obj = dt_val
    else:
        return str(dt_val)
        
    return dt_obj.strftime("%d %b %Y")

def format_datetime(dt_val: Optional[Union[str, datetime]], default: str = "Not Specified") -> str:
    """Format datetime into DD MMM YYYY, HH:MM."""
    if not dt_val:
        return default
    if isinstance(dt_val, str):
        try:
            dt_obj = datetime.fromisoformat(dt_val.replace("Z", "+00:00"))
        except Exception:
            return dt_val
    elif isinstance(dt_val, datetime):
        dt_obj = dt_val
    else:
        return str(dt_val)
    return dt_obj.strftime("%d %b %Y, %H:%M")

def get_status_badge_html(status: str) -> str:
    """Return a clean, professionally styled inline HTML pill for healthcare statuses."""
    status_clean = (status or "").strip()
    status_lower = status_clean.lower()
    
    bg_color = "#f1f5f9"
    text_color = "#334155"
    border_color = "#cbd5e1"
    
    if "scheduled" in status_lower:
        bg_color = "#eff6ff"
        text_color = "#1d4ed8"
        border_color = "#bfdbfe"
    elif "due" in status_lower:
        bg_color = "#fffbeb"
        text_color = "#b45309"
        border_color = "#fde68a"
    elif "completed" in status_lower or "resolved" in status_lower:
        bg_color = "#ecfdf5"
        text_color = "#047857"
        border_color = "#a7f3d0"
    elif "missed" in status_lower or "urgent" in status_lower or "high continuity risk" in status_lower:
        bg_color = "#fef2f2"
        text_color = "#b91c1c"
        border_color = "#fecaca"
    elif "review" in status_lower or "moderate" in status_lower or "in progress" in status_lower:
        bg_color = "#fff7ed"
        text_color = "#c2410c"
        border_color = "#ffedd5"
    elif "rescheduled" in status_lower:
        bg_color = "#f5f3ff"
        text_color = "#6d28d9"
        border_color = "#ddd6fe"
        
    return (
        f'<span style="display:inline-block; padding: 2px 8px; font-size: 0.78rem; '
        f'font-weight: 600; border-radius: 4px; background-color: {bg_color}; '
        f'color: {text_color}; border: 1px solid {border_color};">{status_clean}</span>'
    )

def clean_text(text: Optional[str]) -> str:
    """Sanitize and format text to ensure no em dashes or double hyphens occur."""
    if not text:
        return ""
    # Replace em dash and en dash with comma or space-hyphen-space
    sanitized = text.replace("—", " - ").replace("–", " - ").replace("--", " - ")
    return sanitized.strip()
