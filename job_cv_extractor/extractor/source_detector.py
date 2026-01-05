"""
Job Source Detection Module

Detects the job posting platform (Greenhouse, Lever, Workday, etc.)
from URL patterns and embedded parameters.
"""

import re
from urllib.parse import urlparse, parse_qs
from typing import Literal
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import logger


# Job source type
JobSource = Literal["greenhouse", "lever", "workday", "generic"]


# URL patterns for each platform
GREENHOUSE_PATTERNS = [
    r'boards\.greenhouse\.io',
    r'greenhouse\.io/embed',
    r'[?&]gh_jid=\d+',  # Embedded Greenhouse job ID parameter
    r'job_app\.greenhouse\.io',
]

LEVER_PATTERNS = [
    r'jobs\.lever\.co',
    r'lever\.co/[^/]+/[a-f0-9-]+',
]

WORKDAY_PATTERNS = [
    r'myworkdayjobs\.com',
    r'\.workday\.com/.*?/job/',
    r'wd\d+\.myworkdaysite\.com',
]


def detect_source(url: str) -> JobSource:
    """
    Detect the job posting platform from URL.
    
    Args:
        url: Job posting URL
    
    Returns:
        JobSource enum string indicating the platform
    """
    url_lower = url.lower()
    
    # Check Greenhouse patterns
    if detect_greenhouse(url):
        logger.info("Detected Greenhouse job page")
        return "greenhouse"
    
    # Check Lever patterns
    if detect_lever(url):
        logger.info("Detected Lever job page")
        return "lever"
    
    # Check Workday patterns
    if detect_workday(url):
        logger.info("Detected Workday job page")
        return "workday"
    
    logger.info("Using generic extraction (no specific platform detected)")
    return "generic"


def detect_greenhouse(url: str) -> bool:
    """
    Detect if URL is a Greenhouse job posting.
    
    Checks for:
    - Direct boards.greenhouse.io URLs
    - Embedded job pages with gh_jid parameter
    - Greenhouse embed URLs
    
    Args:
        url: URL to check
    
    Returns:
        True if Greenhouse job posting
    """
    url_lower = url.lower()
    
    for pattern in GREENHOUSE_PATTERNS:
        if re.search(pattern, url_lower):
            logger.debug(f"Greenhouse pattern matched: {pattern}")
            return True
    
    # Also check for gh_jid in query params
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    if 'gh_jid' in query_params:
        logger.debug("Greenhouse gh_jid parameter found")
        return True
    
    return False


def detect_lever(url: str) -> bool:
    """
    Detect if URL is a Lever job posting.
    
    Args:
        url: URL to check
    
    Returns:
        True if Lever job posting
    """
    url_lower = url.lower()
    
    for pattern in LEVER_PATTERNS:
        if re.search(pattern, url_lower):
            logger.debug(f"Lever pattern matched: {pattern}")
            return True
    
    return False


def detect_workday(url: str) -> bool:
    """
    Detect if URL is a Workday job posting.
    
    Args:
        url: URL to check
    
    Returns:
        True if Workday job posting
    """
    url_lower = url.lower()
    
    for pattern in WORKDAY_PATTERNS:
        if re.search(pattern, url_lower):
            logger.debug(f"Workday pattern matched: {pattern}")
            return True
    
    return False


def get_source_display_name(source: JobSource) -> str:
    """
    Get user-friendly display name for job source.
    
    Args:
        source: JobSource enum value
    
    Returns:
        Human-readable platform name
    """
    names = {
        "greenhouse": "Greenhouse",
        "lever": "Lever",
        "workday": "Workday",
        "generic": "Generic Job Site"
    }
    return names.get(source, "Unknown")
