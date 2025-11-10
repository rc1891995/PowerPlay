# PowerPlay Changelog

## v2.5.0 — Sprint 2.5 (Cloud Automation & CI/CD Integration)
**Release Date:** 2025-11-10

### ✨ Highlights
- Implemented SQLite persistence layer (`utils/db_io.py`)
- Verified dual-write integrity with `backfill_powerball.py`
- Added CI/CD workflow (`.github/workflows/powerplay-ci.yml`)
- Cleaned and hardened all utility modules with full docstrings
- Archived and version-tagged PowerPlay v2.4.0_clean.zip
- Established **PowerPlay Zip Rule** for future packaging
- Repo synced to GitHub @ `rc1891995/PowerPlay`

### ⚙️ Technical
- SQLAlchemy ORM integration with unique constraints
- Improved `data_io` normalization and safe JSON/CSV handling
- Expanded logging consistency across modules
- Pinned dependencies in `requirements.txt`

### 🧭 Next Sprint (2.6)
- Replace simulated backfill with real Powerball historical scraper
- Populate CSV + SQLite with 2015–present draws
- Prepare dataset for AI/ML pattern analysis (Sprint 2.7)
