"""
Content Cleaner Module

Removes boilerplate content (navigation, footer, scripts, legal text)
from HTML to extract the main job posting content.
"""

import re
from typing import List, Set
from bs4 import BeautifulSoup, Comment
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import logger


# Tags to completely remove
REMOVE_TAGS = {
    'script', 'style', 'noscript', 'iframe', 'svg', 'canvas',
    'nav', 'header', 'footer', 'aside', 'form', 'button',
    'input', 'select', 'textarea', 'label',
    'advertisement', 'ads', 'ad'
}

# Classes/IDs indicating boilerplate content
BOILERPLATE_PATTERNS = [
    r'nav(igation)?[-_]?',
    r'header[-_]?',
    r'footer[-_]?',
    r'sidebar[-_]?',
    r'menu[-_]?',
    r'cookie[-_]?',
    r'banner[-_]?',
    r'popup[-_]?',
    r'modal[-_]?',
    r'overlay[-_]?',
    r'advertisement[-_]?',
    r'ads?[-_]?',
    r'promo(tion)?[-_]?',
    r'social[-_]?(share|media|links)?',
    r'share[-_]?(button|link)?s?',
    r'related[-_]?(jobs|posts|articles)?',
    r'similar[-_]?(jobs|positions)?',
    r'recommend(ed|ations)?[-_]?',
    r'newsletter[-_]?',
    r'subscribe[-_]?',
    r'sign[-_]?up',
    r'login[-_]?',
    r'register[-_]?',
    r'legal[-_]?',
    r'privacy[-_]?',
    r'terms[-_]?',
    r'disclaimer[-_]?',
    r'copyright[-_]?',
    r'breadcrumb[-_]?',
    r'pagination[-_]?',
    r'search[-_]?(box|form|bar)?',
]

# Compile patterns for efficiency
BOILERPLATE_REGEX = re.compile(
    '|'.join(BOILERPLATE_PATTERNS),
    re.IGNORECASE
)

# Legal/boilerplate text patterns
LEGAL_TEXT_PATTERNS = [
    r'equal\s+opportunity\s+employer',
    r'we\s+are\s+an?\s+e\.?o\.?e\.?',
    r'affirmative\s+action',
    r'(terms\s+(of\s+)?(use|service)|privacy\s+policy)',
    r'©\s*\d{4}',
    r'all\s+rights\s+reserved',
    r'cookie\s+(policy|settings|preferences)',
    r'by\s+(clicking|applying|submitting)',
    r'we\s+use\s+cookies',
    r'this\s+site\s+uses\s+cookies',
]

LEGAL_REGEX = re.compile(
    '|'.join(LEGAL_TEXT_PATTERNS),
    re.IGNORECASE
)


def clean_html_content(html: str) -> str:
    """
    Clean HTML by removing boilerplate content.
    
    Steps:
    1. Remove unwanted tags (scripts, styles, nav, footer, etc.)
    2. Remove elements with boilerplate class/ID patterns
    3. Remove HTML comments
    4. Extract and clean text
    5. Remove legal/boilerplate text sections
    
    Args:
        html: Raw HTML content
    
    Returns:
        Cleaned text content suitable for LLM analysis
    """
    logger.info("Cleaning HTML content")
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Step 1: Remove unwanted tags
    removed_count = 0
    for tag in REMOVE_TAGS:
        for element in soup.find_all(tag):
            element.decompose()
            removed_count += 1
    
    logger.debug(f"Removed {removed_count} unwanted tags")
    
    # Step 2: Remove elements with boilerplate patterns
    _remove_boilerplate_elements(soup)
    
    # Step 3: Remove HTML comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()
    
    # Step 4: Extract text
    text = _extract_clean_text(soup)
    
    # Step 5: Remove legal text sections
    text = _remove_legal_sections(text)
    
    # Final cleanup
    text = _final_cleanup(text)
    
    logger.info(f"Cleaned content: {len(text)} characters")
    
    return text


def _remove_boilerplate_elements(soup: BeautifulSoup) -> None:
    """Remove elements that match boilerplate patterns."""
    removed = 0
    
    for element in soup.find_all(True):  # All tags
        # Skip elements without attrs (can happen with some parsers)
        if not hasattr(element, 'attrs') or element.attrs is None:
            continue
        
        # Check class attribute
        classes = element.get('class', [])
        if isinstance(classes, list):
            class_str = ' '.join(classes)
        else:
            class_str = str(classes) if classes else ''
        
        # Check id attribute
        elem_id = element.get('id', '') or ''
        
        # Check role attribute
        role = element.get('role', '') or ''
        
        # Combine for pattern matching
        combined = f"{class_str} {elem_id} {role}"
        
        if BOILERPLATE_REGEX.search(combined):
            element.decompose()
            removed += 1
    
    logger.debug(f"Removed {removed} boilerplate elements")


def _extract_clean_text(soup: BeautifulSoup) -> str:
    """Extract text while preserving some structure."""
    # Get all text blocks
    texts = []
    
    # Find main content area if possible
    main_content = (
        soup.find('main') or
        soup.find('article') or
        soup.find(attrs={'role': 'main'}) or
        soup.find(class_=re.compile(r'job|content|description', re.I)) or
        soup.find('body') or
        soup
    )
    
    # Extract text with newlines for structure
    text = main_content.get_text(separator='\n', strip=True)
    
    return text


def _remove_legal_sections(text: str) -> str:
    """Remove legal disclaimer sections."""
    lines = text.split('\n')
    cleaned_lines = []
    skip_until_section = False
    
    for line in lines:
        line_stripped = line.strip()
        
        # Skip empty lines but preserve some spacing
        if not line_stripped:
            if cleaned_lines and cleaned_lines[-1] != '':
                cleaned_lines.append('')
            continue
        
        # Check if this line starts a legal section
        if LEGAL_REGEX.search(line_stripped):
            # If it's a short line, it might be a section header - skip subsequent lines
            if len(line_stripped) < 100:
                skip_until_section = True
            continue
        
        # Reset skip flag on new apparent section (header-like text)
        if skip_until_section and len(line_stripped) < 60 and line_stripped.endswith(':'):
            skip_until_section = False
        
        if not skip_until_section:
            cleaned_lines.append(line_stripped)
    
    return '\n'.join(cleaned_lines)


def _final_cleanup(text: str) -> str:
    """Final text cleanup."""
    # Remove multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove lines that are just punctuation or very short
    lines = text.split('\n')
    cleaned = []
    
    for line in lines:
        # Skip lines that are just punctuation/symbols
        if line and not re.match(r'^[\s\-•·*|/\\]+$', line):
            # Skip very short lines that aren't meaningful
            if len(line.strip()) > 2 or line.strip() == '':
                cleaned.append(line)
    
    text = '\n'.join(cleaned)
    
    # Remove excessive whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Normalize newlines
    text = re.sub(r'\n ', '\n', text)
    
    return text.strip()


def is_meaningful_content(text: str, min_length: int = 200) -> bool:
    """
    Check if extracted content is meaningful.
    
    Args:
        text: Extracted text content
        min_length: Minimum character length for valid content
    
    Returns:
        True if content appears to be a valid job posting
    """
    if len(text) < min_length:
        logger.warning(f"Content too short: {len(text)} chars (min: {min_length})")
        return False
    
    # Check for job-related keywords
    job_keywords = [
        'responsibilities', 'qualifications', 'requirements',
        'experience', 'skills', 'benefits', 'salary', 'location',
        'apply', 'position', 'role', 'team', 'opportunity',
        'job description', 'about the role', 'what you\'ll do',
        'what we\'re looking for', 'who you are', 'about you'
    ]
    
    text_lower = text.lower()
    matches = sum(1 for kw in job_keywords if kw in text_lower)
    
    if matches < 2:
        logger.warning(f"Content may not be a job posting (only {matches} job keywords found)")
        return False
    
    logger.debug(f"Content appears valid ({matches} job keywords found)")
    return True

