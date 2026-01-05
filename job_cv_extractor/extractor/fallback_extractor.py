"""
Fallback Extractor Module

Uses trafilatura for extracting main readable content when other methods fail.
This is the last resort for difficult-to-parse pages.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import logger

try:
    import trafilatura
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False
    logger.warning("trafilatura not available, fallback extraction disabled")


def extract_with_fallback(html: str, url: str = None) -> str:
    """
    Extract main content using trafilatura.
    
    Trafilatura is designed to extract the main readable content from web pages,
    removing boilerplate, navigation, and other non-content elements.
    
    Args:
        html: Raw HTML content
        url: Original URL (optional, helps trafilatura with relative links)
    
    Returns:
        Extracted text content, or empty string if extraction fails
    """
    if not TRAFILATURA_AVAILABLE:
        logger.error("trafilatura is not installed. Install with: pip install trafilatura")
        return ""
    
    logger.info("Using trafilatura for content extraction (fallback method)")
    
    try:
        # Extract with trafilatura
        # favor_precision=True prioritizes quality over quantity
        # include_comments=False removes user comments
        # include_tables=True keeps tabular data which might have job details
        extracted = trafilatura.extract(
            html,
            url=url,
            favor_precision=True,
            include_comments=False,
            include_tables=True,
            include_links=False,
            include_images=False,
            deduplicate=True,
            no_fallback=False,  # Allow fallback to justext/readability
        )
        
        if extracted:
            logger.info(f"Trafilatura extracted {len(extracted)} characters")
            return extracted
        else:
            logger.warning("Trafilatura returned empty content")
            return ""
    
    except Exception as e:
        logger.error(f"Trafilatura extraction failed: {str(e)}")
        return ""


def extract_with_newspaper(html: str, url: str) -> str:
    """
    Alternative fallback using newspaper3k.
    
    Note: newspaper3k is optional and may not be installed.
    
    Args:
        html: Raw HTML content
        url: Original URL
    
    Returns:
        Extracted text content
    """
    try:
        from newspaper import Article
        
        logger.info("Using newspaper3k for content extraction")
        
        article = Article(url)
        article.download(input_html=html)
        article.parse()
        
        text = article.text
        
        if text:
            logger.info(f"Newspaper3k extracted {len(text)} characters")
            return text
        else:
            logger.warning("Newspaper3k returned empty content")
            return ""
    
    except ImportError:
        logger.debug("newspaper3k not available")
        return ""
    except Exception as e:
        logger.error(f"Newspaper3k extraction failed: {str(e)}")
        return ""


def get_best_extraction(html: str, url: str = None) -> str:
    """
    Try multiple extraction methods and return the best result.
    
    Priority:
    1. trafilatura (best for article-like content)
    2. newspaper3k (fallback)
    
    Args:
        html: Raw HTML content
        url: Original URL
    
    Returns:
        Best extracted content
    """
    # Try trafilatura first
    content = extract_with_fallback(html, url)
    
    if content and len(content) > 200:
        return content
    
    # Try newspaper3k as fallback
    if url:
        newspaper_content = extract_with_newspaper(html, url)
        if newspaper_content and len(newspaper_content) > len(content or ""):
            return newspaper_content
    
    return content or ""
