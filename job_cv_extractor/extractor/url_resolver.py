"""
Canonical URL Resolver Module

Resolves embedded or proxied job URLs to their canonical form
for reliable content extraction.
"""

import re
from urllib.parse import urlparse, parse_qs, urlencode
from typing import Optional, Tuple
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import logger
from .source_detector import JobSource


def resolve_url(url: str, source: JobSource) -> Tuple[str, bool]:
    """
    Resolve URL to canonical form based on detected source.
    
    Args:
        url: Original job posting URL
        source: Detected job source platform
    
    Returns:
        Tuple of (resolved_url, was_resolved)
        was_resolved is True if URL was modified
    """
    if source == "greenhouse":
        return resolve_greenhouse_url(url)
    elif source == "lever":
        return resolve_lever_url(url)
    elif source == "workday":
        return resolve_workday_url(url)
    else:
        return url, False


def resolve_greenhouse_url(url: str) -> Tuple[str, bool]:
    """
    Resolve Greenhouse job URL to canonical boards.greenhouse.io format.
    
    Handles:
    - Embedded jobs with gh_jid parameter
    - Company career pages proxying Greenhouse
    - Already canonical URLs
    
    Args:
        url: Original URL
    
    Returns:
        Tuple of (canonical_url, was_resolved)
    """
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    # Check if already a direct Greenhouse URL
    if 'boards.greenhouse.io' in parsed.netloc.lower():
        logger.debug("URL is already canonical Greenhouse format")
        return url, False
    
    # Check for gh_jid parameter (embedded Greenhouse job)
    if 'gh_jid' in query_params:
        job_id = query_params['gh_jid'][0]
        
        # Try to extract company token from URL or use generic approach
        company_token = _extract_greenhouse_company(url, query_params)
        
        if company_token:
            canonical_url = f"https://boards.greenhouse.io/{company_token}/jobs/{job_id}"
            logger.info(f"Resolved Greenhouse URL: {canonical_url}")
            return canonical_url, True
        else:
            # Fallback: use embed endpoint which doesn't require company token
            canonical_url = f"https://boards.greenhouse.io/embed/job_app?token={job_id}"
            logger.info(f"Resolved to Greenhouse embed URL: {canonical_url}")
            return canonical_url, True
    
    # Check for token parameter (another Greenhouse embed format)
    if 'token' in query_params and 'greenhouse' in url.lower():
        token = query_params['token'][0]
        canonical_url = f"https://boards.greenhouse.io/embed/job_app?token={token}"
        logger.info(f"Resolved Greenhouse token URL: {canonical_url}")
        return canonical_url, True
    
    # Try to extract job ID from URL path
    job_id_match = re.search(r'/jobs?/(\d+)', url)
    if job_id_match:
        job_id = job_id_match.group(1)
        company_token = _extract_greenhouse_company(url, query_params)
        
        if company_token:
            canonical_url = f"https://boards.greenhouse.io/{company_token}/jobs/{job_id}"
            logger.info(f"Resolved Greenhouse URL from path: {canonical_url}")
            return canonical_url, True
    
    # Cannot resolve further
    logger.debug("Greenhouse URL resolution not possible, using original")
    return url, False


def _extract_greenhouse_company(url: str, query_params: dict) -> Optional[str]:
    """
    Try to extract Greenhouse company token from URL or params.
    
    Args:
        url: Original URL
        query_params: Parsed query parameters
    
    Returns:
        Company token or None
    """
    # Check for gh_src parameter which sometimes contains company info
    if 'for' in query_params:
        return query_params['for'][0]
    
    # Try to extract from boards.greenhouse.io path
    match = re.search(r'boards\.greenhouse\.io/([^/]+)', url)
    if match:
        return match.group(1)
    
    # Try to extract from embed URL
    match = re.search(r'greenhouse\.io/embed/job_board/js\?for=([^&]+)', url)
    if match:
        return match.group(1)
    
    return None


def resolve_lever_url(url: str) -> Tuple[str, bool]:
    """
    Resolve Lever job URL and optionally get JSON endpoint.
    
    Lever provides a JSON API at /apply endpoint which can be useful
    for structured data extraction.
    
    Args:
        url: Original URL
    
    Returns:
        Tuple of (resolved_url, was_resolved)
    """
    parsed = urlparse(url)
    
    # Check if already a Lever URL
    if 'lever.co' not in parsed.netloc.lower():
        logger.debug("Not a direct Lever URL")
        return url, False
    
    # Lever URLs are typically already in good format
    # Format: https://jobs.lever.co/{company}/{job_id}
    
    # Remove any trailing /apply if present (we want the main job page)
    clean_path = re.sub(r'/apply/?$', '', parsed.path)
    
    if clean_path != parsed.path:
        clean_url = f"{parsed.scheme}://{parsed.netloc}{clean_path}"
        logger.info(f"Cleaned Lever URL: {clean_url}")
        return clean_url, True
    
    logger.debug("Lever URL already in canonical form")
    return url, False


def resolve_workday_url(url: str) -> Tuple[str, bool]:
    """
    Resolve Workday job URL.
    
    Workday URLs are complex and typically require the original URL.
    This function mainly validates and cleans the URL.
    
    Args:
        url: Original URL
    
    Returns:
        Tuple of (resolved_url, was_resolved)
    """
    # Workday URLs are notoriously complex
    # For now, return as-is since they usually work with direct fetch
    logger.debug("Workday URL - using original (no resolution needed)")
    return url, False


def get_api_endpoint(url: str, source: JobSource) -> Optional[str]:
    """
    Get API endpoint for structured data if available.
    
    Some platforms provide JSON APIs that are easier to parse.
    
    Args:
        url: Resolved job URL
        source: Job source platform
    
    Returns:
        API endpoint URL or None
    """
    if source == "lever":
        # Lever provides JSON at /apply endpoint
        parsed = urlparse(url)
        # Extract job ID from path
        match = re.search(r'/([a-f0-9-]{36})/?$', parsed.path)
        if match:
            job_id = match.group(1)
            company_match = re.search(r'lever\.co/([^/]+)', url)
            if company_match:
                company = company_match.group(1)
                return f"https://api.lever.co/v0/postings/{company}/{job_id}"
    
    return None
