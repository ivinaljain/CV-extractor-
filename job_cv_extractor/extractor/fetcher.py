"""
URL Fetching Module

Handles HTTP requests with browser-like headers and proper error handling.
Designed to work with various job posting sites.
"""

import requests
from typing import Tuple, Optional
from dataclasses import dataclass
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import logger


# Browser-like headers to avoid bot detection
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}

# Request timeout in seconds
REQUEST_TIMEOUT = 30


@dataclass
class FetchResult:
    """Result of a URL fetch operation."""
    success: bool
    html: Optional[str]
    status_code: Optional[int]
    error_message: Optional[str]
    final_url: str  # After redirects


def fetch_url(url: str, timeout: int = REQUEST_TIMEOUT) -> FetchResult:
    """
    Fetch HTML content from a URL with browser-like headers.
    
    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds
    
    Returns:
        FetchResult containing the HTML or error information
    """
    logger.info(f"Fetching URL: {url}")
    
    # Validate URL
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        logger.debug(f"Added https:// prefix, URL is now: {url}")
    
    try:
        # Make request with browser-like headers
        response = requests.get(
            url,
            headers=DEFAULT_HEADERS,
            timeout=timeout,
            allow_redirects=True,
            verify=True  # SSL verification
        )
        
        logger.info(f"Response status: {response.status_code}")
        logger.debug(f"Final URL after redirects: {response.url}")
        
        # Check for successful response
        if response.status_code == 200:
            # Try to detect encoding
            if response.encoding is None or response.encoding == 'ISO-8859-1':
                # Try to detect from content
                response.encoding = response.apparent_encoding
            
            html_content = response.text
            logger.info(f"Successfully fetched {len(html_content)} characters")
            
            return FetchResult(
                success=True,
                html=html_content,
                status_code=response.status_code,
                error_message=None,
                final_url=response.url
            )
        else:
            error_msg = f"HTTP {response.status_code}: {response.reason}"
            logger.warning(error_msg)
            
            return FetchResult(
                success=False,
                html=None,
                status_code=response.status_code,
                error_message=error_msg,
                final_url=response.url
            )
    
    except requests.exceptions.Timeout:
        error_msg = f"Request timed out after {timeout} seconds"
        logger.error(error_msg)
        return FetchResult(
            success=False,
            html=None,
            status_code=None,
            error_message=error_msg,
            final_url=url
        )
    
    except requests.exceptions.SSLError as e:
        error_msg = f"SSL certificate error: {str(e)}"
        logger.error(error_msg)
        return FetchResult(
            success=False,
            html=None,
            status_code=None,
            error_message=error_msg,
            final_url=url
        )
    
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection error: Could not connect to the server"
        logger.error(f"{error_msg}: {str(e)}")
        return FetchResult(
            success=False,
            html=None,
            status_code=None,
            error_message=error_msg,
            final_url=url
        )
    
    except requests.exceptions.TooManyRedirects:
        error_msg = "Too many redirects - the URL may be invalid"
        logger.error(error_msg)
        return FetchResult(
            success=False,
            html=None,
            status_code=None,
            error_message=error_msg,
            final_url=url
        )
    
    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {str(e)}"
        logger.error(error_msg)
        return FetchResult(
            success=False,
            html=None,
            status_code=None,
            error_message=error_msg,
            final_url=url
        )
    
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.exception(error_msg)
        return FetchResult(
            success=False,
            html=None,
            status_code=None,
            error_message=error_msg,
            final_url=url
        )


def is_valid_job_url(url: str) -> Tuple[bool, str]:
    """
    Basic validation for job posting URLs.
    
    Args:
        url: URL to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url or not url.strip():
        return False, "URL cannot be empty"
    
    url = url.strip()
    
    # Check for basic URL structure
    if not ('.' in url):
        return False, "Invalid URL format"
    
    # Check for common job sites (optional, just for logging)
    known_job_sites = [
        'linkedin.com', 'indeed.com', 'glassdoor.com', 'monster.com',
        'ziprecruiter.com', 'dice.com', 'careerbuilder.com', 'lever.co',
        'greenhouse.io', 'workday.com', 'smartrecruiters.com', 'jobs.lever.co',
        'boards.greenhouse.io', 'angel.co', 'wellfound.com', 'simplyhired.com',
        'hired.com', 'builtin.com', 'theladders.com', 'flexjobs.com'
    ]
    
    url_lower = url.lower()
    is_known_site = any(site in url_lower for site in known_job_sites)
    
    if is_known_site:
        logger.debug(f"Recognized as known job site")
    else:
        logger.debug(f"URL is not from a known job site, but will attempt extraction")
    
    return True, ""

