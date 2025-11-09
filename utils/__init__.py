# ──────────────────────────────────────────────────────────────
# PACKAGE: utils
# PURPOSE: Shared utilities for PowerPlay (I/O, logging, S3, scraping, etc.).
# UPDATED: Sprint 2.3.4 – Adds metadata and safe imports.
# ──────────────────────────────────────────────────────────────
"""
PowerPlay – Utilities Layer

Provides shared utility functions for the PowerPlay ecosystem:
    • data_io          – Safe CSV/JSON I/O and normalization
    • logger           – Project-wide logging setup
    • s3_io            – Cloud upload/download utilities
    • scraper_powerball – Web scraper for live Powerball results
"""

__version__ = "2.3.4"
__author__ = "David M. Allen"
__project__ = "PowerPlay"

from . import data_io, logger, s3_io, scraper_powerball

__all__ = ["data_io", "logger", "s3_io", "scraper_powerball"]
