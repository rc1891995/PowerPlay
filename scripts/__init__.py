# ──────────────────────────────────────────────────────────────
# PACKAGE: scripts
# PURPOSE: Core PowerPlay logic and analysis scripts.
# UPDATED: Sprint 2.3.4 – Adds unified metadata and import shortcuts.
# ──────────────────────────────────────────────────────────────
"""
PowerPlay – Script Layer

Contains the main operational modules for PowerPlay:
    • fetch_powerball       – Data ingestion and scraping
    • analyze_powerball     – Frequency analysis logic
    • analyze_visuals       – Chart generation for results
    • analyze_patterns_ext  – Statistical randomness analysis
    • recommend_powerball   – Pick generation logic
    • plot_patterns/trends  – Rolling visualizations
    • view_logs             – CLI log viewer
"""

__version__ = "2.3.4"
__author__ = "David M. Allen"
__project__ = "PowerPlay"

# Optional convenience imports for developers
from . import (
    fetch_powerball,
    analyze_powerball,
    analyze_visuals,
    analyze_patterns_extended,
    recommend_powerball,
    plot_patterns,
    plot_trends,
    view_logs,
)

__all__ = [
    "fetch_powerball",
    "analyze_powerball",
    "analyze_visuals",
    "analyze_patterns_extended",
    "recommend_powerball",
    "plot_patterns",
    "plot_trends",
    "view_logs",
]
