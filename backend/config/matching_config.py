# backend/config/matching_config.py
"""
Universal Match Score Configuration
Centralized thresholds for semantic matching across the platform
"""

# ==============================================
# UNIVERSAL MATCH SCORE THRESHOLDS (0-1 scale)
# ==============================================

# Primary threshold for job-to-candidate matching
DEFAULT_MATCH_THRESHOLD = 0.50  # 50% - balanced threshold

# Threshold for candidate-to-job recommendations
CANDIDATE_JOB_THRESHOLD = 0.45  # 45% - slightly lower to show more options

# High confidence threshold for auto-accept/fast-track
HIGH_CONFIDENCE_THRESHOLD = 0.75  # 75% - excellent match

# Minimum viable threshold (below this, don't show)
MINIMUM_VIABLE_THRESHOLD = 0.30  # 30% - absolute minimum


# ==============================================
# SEMANTIC SIMILARITY SCORE WEIGHTS (0-100 scale)
# ==============================================

# Base semantic similarity weight (from vector embedding)
SEMANTIC_BASE_WEIGHT = 60  # Out of 100 total

# Restaurant-specific bonus weights (total max: 40 points)
BONUS_CERTIFICATION_MATCH = 10      # Food safety, alcohol certs
BONUS_CUISINE_EXPERIENCE = 15       # Cuisine type match
BONUS_SHIFT_AVAILABILITY = 5        # Shift preference match
BONUS_EXPERIENCE_LEVEL = 10         # Meets minimum years
BONUS_CUSTOMER_SERVICE = 10          # For front-of-house roles

# Max total bonus
MAX_BONUS_SCORE = 50  # Sum of all bonuses


# ==============================================
# FAISS SIMILARITY SEARCH SETTINGS
# ==============================================

# Number of candidates to fetch before filtering (get extras for bonus scoring)
SEARCH_MULTIPLIER = 2  # top_k * 2

# Maximum candidates to search (cap for performance)
MAX_SEARCH_LIMIT = 20


# ==============================================
# THRESHOLD POLICY
# ==============================================

def get_threshold(context="default"):
    """
    Get appropriate threshold based on context.
    
    Args:
        context: "default", "candidate_search", "high_confidence", "minimum"
    
    Returns:
        float: Threshold value (0-1)
    """
    thresholds = {
        "default": DEFAULT_MATCH_THRESHOLD,
        "candidate_search": CANDIDATE_JOB_THRESHOLD,
        "high_confidence": HIGH_CONFIDENCE_THRESHOLD,
        "minimum": MINIMUM_VIABLE_THRESHOLD
    }
    return thresholds.get(context, DEFAULT_MATCH_THRESHOLD)


def normalize_score(score, max_score=100):
    """
    Normalize score to 0-1 range.
    
    Args:
        score: Score in 0-100 range
        max_score: Maximum possible score (default 100)
    
    Returns:
        float: Normalized score (0-1)
    """
    return min(max(score / max_score, 0.0), 1.0)


def meets_threshold(score, threshold=None, context="default"):
    """
    Check if score meets threshold.
    
    Args:
        score: Score to check (0-1 or 0-100, will normalize)
        threshold: Custom threshold (optional)
        context: Context for default threshold
    
    Returns:
        bool: True if score meets or exceeds threshold
    """
    # Normalize score if it's in 0-100 range
    if score > 1.0:
        score = normalize_score(score)
    
    # Use custom or context-based threshold
    if threshold is None:
        threshold = get_threshold(context)
    
    return score >= threshold
