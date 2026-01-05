"""
HTML Parser Module

Parses HTML content using BeautifulSoup.
Prioritizes Schema.org JobPosting JSON-LD extraction.
"""

import json
import re
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import logger


def extract_schema_job_posting(html: str) -> Optional[Dict[str, Any]]:
    """
    Extract Schema.org JobPosting JSON-LD from HTML.
    
    This is the most reliable method as it contains structured data
    that the job site explicitly provides for search engines.
    
    Args:
        html: Raw HTML content
    
    Returns:
        Parsed JobPosting data or None if not found
    """
    logger.info("Attempting to extract Schema.org JobPosting JSON-LD")
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all script tags with JSON-LD
    script_tags = soup.find_all('script', type='application/ld+json')
    
    for script in script_tags:
        try:
            content = script.string
            if not content:
                continue
            
            # Parse JSON
            data = json.loads(content)
            
            # Handle array of schemas
            if isinstance(data, list):
                for item in data:
                    if _is_job_posting(item):
                        logger.info("Found JobPosting in JSON-LD array")
                        return _normalize_job_posting(item)
            
            # Handle single schema
            elif isinstance(data, dict):
                if _is_job_posting(data):
                    logger.info("Found JobPosting in JSON-LD")
                    return _normalize_job_posting(data)
                
                # Check @graph structure
                if '@graph' in data:
                    for item in data['@graph']:
                        if _is_job_posting(item):
                            logger.info("Found JobPosting in @graph")
                            return _normalize_job_posting(item)
        
        except json.JSONDecodeError as e:
            logger.debug(f"Failed to parse JSON-LD: {e}")
            continue
        except Exception as e:
            logger.debug(f"Error processing JSON-LD: {e}")
            continue
    
    logger.info("No Schema.org JobPosting found")
    return None


def _is_job_posting(data: Dict[str, Any]) -> bool:
    """Check if a JSON-LD object is a JobPosting."""
    if not isinstance(data, dict):
        return False
    
    schema_type = data.get('@type', '')
    
    if isinstance(schema_type, str):
        return 'JobPosting' in schema_type
    elif isinstance(schema_type, list):
        return any('JobPosting' in t for t in schema_type)
    
    return False


def _normalize_job_posting(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize JobPosting data to a consistent format.
    
    Extracts key fields and handles variations in Schema.org implementation.
    """
    normalized = {
        'title': _extract_value(data, ['title', 'name']),
        'description': _extract_value(data, ['description']),
        'company': _extract_company(data),
        'location': _extract_location(data),
        'employment_type': _extract_value(data, ['employmentType']),
        'date_posted': _extract_value(data, ['datePosted']),
        'valid_through': _extract_value(data, ['validThrough']),
        'salary': _extract_salary(data),
        'experience': _extract_value(data, ['experienceRequirements']),
        'education': _extract_value(data, ['educationRequirements']),
        'skills': _extract_skills(data),
        'industry': _extract_value(data, ['industry']),
    }
    
    return {k: v for k, v in normalized.items() if v}


def _extract_value(data: Dict, keys: List[str]) -> Optional[str]:
    """Extract first matching value from a list of possible keys."""
    for key in keys:
        value = data.get(key)
        if value:
            if isinstance(value, str):
                return value.strip()
            elif isinstance(value, dict):
                # Try common sub-keys
                for sub_key in ['@value', 'name', 'value']:
                    if sub_key in value:
                        return str(value[sub_key]).strip()
            elif isinstance(value, list):
                return ', '.join(str(v) for v in value if v)
    return None


def _extract_company(data: Dict) -> Optional[str]:
    """Extract company name from hiringOrganization."""
    org = data.get('hiringOrganization')
    if not org:
        return None
    
    if isinstance(org, str):
        return org
    elif isinstance(org, dict):
        return org.get('name') or org.get('legalName')
    
    return None


def _extract_location(data: Dict) -> Optional[str]:
    """Extract job location."""
    location = data.get('jobLocation')
    if not location:
        return None
    
    if isinstance(location, str):
        return location
    
    if isinstance(location, list):
        locations = []
        for loc in location:
            loc_str = _parse_location_object(loc)
            if loc_str:
                locations.append(loc_str)
        return '; '.join(locations) if locations else None
    
    if isinstance(location, dict):
        return _parse_location_object(location)
    
    return None


def _parse_location_object(loc: Dict) -> Optional[str]:
    """Parse a single location object."""
    if not isinstance(loc, dict):
        return str(loc) if loc else None
    
    address = loc.get('address')
    if address:
        if isinstance(address, str):
            return address
        elif isinstance(address, dict):
            parts = []
            for key in ['streetAddress', 'addressLocality', 'addressRegion', 'postalCode', 'addressCountry']:
                val = address.get(key)
                if val:
                    if isinstance(val, dict):
                        val = val.get('name', str(val))
                    parts.append(str(val))
            return ', '.join(parts) if parts else None
    
    # Try name field
    return loc.get('name')


def _extract_salary(data: Dict) -> Optional[str]:
    """Extract salary information."""
    salary = data.get('baseSalary') or data.get('estimatedSalary')
    if not salary:
        return None
    
    if isinstance(salary, str):
        return salary
    
    if isinstance(salary, dict):
        value = salary.get('value')
        currency = salary.get('currency', 'USD')
        
        if isinstance(value, dict):
            min_val = value.get('minValue')
            max_val = value.get('maxValue')
            unit = value.get('unitText', 'YEAR')
            
            if min_val and max_val:
                return f"{currency} {min_val:,} - {max_val:,} per {unit}"
            elif min_val:
                return f"{currency} {min_val:,}+ per {unit}"
        elif value:
            return f"{currency} {value}"
    
    return None


def _extract_skills(data: Dict) -> List[str]:
    """Extract required skills."""
    skills = data.get('skills') or data.get('qualifications')
    if not skills:
        return []
    
    if isinstance(skills, str):
        return [skills]
    elif isinstance(skills, list):
        return [str(s) for s in skills if s]
    
    return []


def parse_html(html: str) -> Dict[str, Any]:
    """
    Parse HTML and extract job-related content.
    
    Uses BeautifulSoup to extract text from common job posting patterns.
    
    Args:
        html: Raw HTML content
    
    Returns:
        Dictionary with extracted content
    """
    logger.info("Parsing HTML content with BeautifulSoup")
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract page title
    title_tag = soup.find('title')
    page_title = title_tag.get_text().strip() if title_tag else None
    
    # Extract meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    meta_description = meta_desc.get('content', '').strip() if meta_desc else None
    
    # Try to find main job content container
    main_content = _find_main_content(soup)
    
    # Extract text from main content
    if main_content:
        content_text = _extract_text_from_element(main_content)
    else:
        # Fallback: extract from body
        body = soup.find('body')
        content_text = _extract_text_from_element(body) if body else ""
    
    return {
        'page_title': page_title,
        'meta_description': meta_description,
        'content': content_text,
        'html_length': len(html)
    }


def _find_main_content(soup: BeautifulSoup) -> Optional[Any]:
    """
    Find the main content container for job description.
    
    Tries various common patterns used by job sites.
    """
    # Common job content selectors
    selectors = [
        # Semantic selectors
        {'name': 'main'},
        {'name': 'article'},
        {'role': 'main'},
        
        # Common class patterns
        {'class_': re.compile(r'job[-_]?description', re.I)},
        {'class_': re.compile(r'job[-_]?details', re.I)},
        {'class_': re.compile(r'job[-_]?content', re.I)},
        {'class_': re.compile(r'posting[-_]?content', re.I)},
        {'class_': re.compile(r'description[-_]?content', re.I)},
        
        # ID patterns
        {'id': re.compile(r'job[-_]?description', re.I)},
        {'id': re.compile(r'job[-_]?details', re.I)},
        {'id': re.compile(r'job[-_]?content', re.I)},
        
        # Data attributes (common in React/Vue apps)
        {'attrs': {'data-testid': re.compile(r'job', re.I)}},
    ]
    
    for selector in selectors:
        element = soup.find(**selector)
        if element:
            logger.debug(f"Found content using selector: {selector}")
            return element
    
    return None


def _extract_text_from_element(element) -> str:
    """
    Extract clean text from an HTML element.
    
    Preserves some structure (paragraphs, lists) while removing noise.
    """
    if not element:
        return ""
    
    # Get text with newlines preserved
    text = element.get_text(separator='\n', strip=True)
    
    # Clean up multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Clean up multiple spaces
    text = re.sub(r'[ \t]+', ' ', text)
    
    return text.strip()

