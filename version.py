# version.py
# ──────────────────────────────────────────────────────────────
# MODULE: version.py
# PURPOSE: Global version metadata for PowerPlay
# VERSION: 2.5.0
# DATE: 2025-11-10
# ──────────────────────────────────────────────────────────────

__app_name__ = "PowerPlay"
__version__ = "2.5.0"
__status__ = "stable"
__build_date__ = "2025-11-10"
__author__ = "David M. Allen"


def version_info():
    """Return formatted version string."""
    return f"{__app_name__} v{__version__} ({__status__}, built {__build_date__})"
