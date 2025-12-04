"""Shared constants for SEO Scorer Service."""

# Default SEO checklist structure
# Each item represents an SEO check with True = passed, False = not passed
DEFAULT_CHECKLIST = {
    "title_contains_keyword": False,
    "h1_present": False,
    "h2_count_adequate": False,
    "keyword_density_ok": False,
    "images_have_alt": False,
    "meta_description": False,
    "internal_links": False,
    "external_links": False,
    "word_count_adequate": False,
    "readability_ok": False,
}

# SEO Score status options
SCORE_STATUS_PENDING = "pending"
SCORE_STATUS_COMPLETED = "completed"
SCORE_STATUS_REVIEWED = "reviewed"

VALID_STATUSES = [SCORE_STATUS_PENDING, SCORE_STATUS_COMPLETED, SCORE_STATUS_REVIEWED]

# Auto-scoring thresholds (PHASE-010)
AUTO_SCORE_THRESHOLD_APPROVED = 80
AUTO_SCORE_THRESHOLD_NEEDS_REVIEW = 60

# Tactical correction settings
MAX_CORRECTION_ATTEMPTS = 3

# Minimum word count for adequate content
MIN_WORD_COUNT = 300
RECOMMENDED_WORD_COUNT = 1500

# Keyword density range (percentage)
MIN_KEYWORD_DENSITY = 0.5
MAX_KEYWORD_DENSITY = 3.0
