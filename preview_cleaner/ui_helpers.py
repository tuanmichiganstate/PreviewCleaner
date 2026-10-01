"""Presentation helpers shared by the comparison and full-screen views."""
from datetime import datetime, timedelta, timezone
import re


def page_number(value, count, current):
    """Clamp numeric entries; preserve the current page for invalid input."""
    try:
        return min(max(int(value.strip()), 1), count) - 1
    except (ValueError, AttributeError):
        return current


def result_notice(report, page):
    if not report:
        return "", False
    unsupported = report.get("unsupported_pages", [])
    if page + 1 in unsupported:
        return f"Page {page + 1}: unsupported content remains unchanged. Review verification details.", True
    if unsupported:
        pages = ", ".join(map(str, unsupported[:8])) + (", …" if len(unsupported) > 8 else "")
        return f"Review needed on pages {pages}. Unsupported content remains unchanged.", True
    if not report.get("removed_count") and report.get("target"):
        return "No supported overlay removed. Review the preview; other marks may remain.", True
    return "Printable copy ready. Review the preview before saving.", False


def format_pdf_date(value):
    """Display complete PDF dates with their actual offset; retain unknown forms."""
    if not value:
        return "Not specified"
    match = re.fullmatch(r"(?:D:)?(\d{14})(Z|[+-]\d{2}'?\d{2}'?)?", value)
    if not match:
        return value
    try:
        date = datetime.strptime(match[1], "%Y%m%d%H%M%S")
        offset = match[2]
        if offset:
            if offset == "Z":
                tz = timezone.utc
            else:
                digits = offset[1:].replace("'", "")
                hours, minutes = int(digits[:2]), int(digits[2:])
                if hours > 23 or minutes > 59:
                    return value
                tz = timezone((1 if offset[0] == "+" else -1) * timedelta(hours=hours, minutes=minutes))
            date = date.replace(tzinfo=tz)
            return date.strftime("%d %b %Y, %H:%M:%S UTC%z")
        return date.strftime("%d %b %Y, %H:%M:%S") + " (time zone unspecified)"
    except ValueError:
        return value
