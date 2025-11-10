"""
version.py — PowerPlay unified version metadata
"""

from datetime import datetime

__app_name__ = "PowerPlay"
__version__ = "2.4.0"
__build__ = datetime.now().strftime("%Y-%m-%d %H:%M")
__author__ = "David Allen"
__license__ = "MIT"
__description__ = (
    "PowerPlay: Powerball analytics, trend visualization, and recommendations."
)


def get_version_info() -> str:
    """Return formatted version string for CLI and dashboard."""
    return f"{__app_name__} v{__version__} (Build {__build__})"
