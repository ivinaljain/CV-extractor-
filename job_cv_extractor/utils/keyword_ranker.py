"""
Keyword Ranking Module

Provides TF-based frequency analysis and keyword ranking for ATS optimization.
Combines LLM-extracted keywords with frequency analysis for comprehensive coverage.
"""

import re
from collections import Counter
from typing import List, Dict, Tuple
from dataclasses import dataclass


# Common stop words to filter out
STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
    'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
    'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
    'must', 'shall', 'can', 'need', 'dare', 'ought', 'used', 'this', 'that', 'these',
    'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who',
    'whom', 'whose', 'where', 'when', 'why', 'how', 'all', 'each', 'every', 'both',
    'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
    'same', 'so', 'than', 'too', 'very', 'just', 'also', 'now', 'here', 'there', 'then',
    'if', 'else', 'about', 'into', 'through', 'during', 'before', 'after', 'above',
    'below', 'between', 'under', 'over', 'again', 'further', 'once', 'any', 'our',
    'your', 'their', 'its', 'my', 'his', 'her', 'up', 'down', 'out', 'off', 'while',
    'because', 'until', 'unless', 'although', 'though', 'since', 'whether', 'either',
    'neither', 'yet', 'still', 'already', 'even', 'ever', 'never', 'always', 'often',
    'sometimes', 'usually', 'really', 'quite', 'rather', 'well', 'back', 'way', 'work',
    'working', 'including', 'etc', 'e.g', 'i.e', 'ie', 'eg', 'within', 'across', 'along',
    'around', 'among', 'beside', 'besides', 'beyond', 'upon', 'without', 'according',
    'able', 'ability', 'experience', 'required', 'requirements', 'role', 'position',
    'job', 'candidate', 'candidates', 'team', 'company', 'looking', 'join', 'seeking',
    'strong', 'excellent', 'good', 'great', 'proven', 'solid', 'preferred', 'plus',
    'ideal', 'minimum', 'years', 'year', 'responsibilities', 'qualifications', 'skills',
    'knowledge', 'understanding', 'familiar', 'familiarity', 'proficiency', 'proficient'
}

# Technical terms that should be kept even if common
PRESERVE_TERMS = {
    'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue', 'node',
    'sql', 'nosql', 'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch',
    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'ci/cd', 'git', 'github', 'gitlab',
    'api', 'rest', 'graphql', 'microservices', 'agile', 'scrum', 'devops', 'mlops',
    'machine learning', 'deep learning', 'ai', 'nlp', 'computer vision', 'tensorflow',
    'pytorch', 'keras', 'pandas', 'numpy', 'scikit-learn', 'spark', 'hadoop', 'kafka',
    'linux', 'unix', 'bash', 'shell', 'powershell', 'terraform', 'ansible', 'jenkins',
    'html', 'css', 'sass', 'less', 'webpack', 'babel', 'npm', 'yarn', 'maven', 'gradle',
    'spring', 'django', 'flask', 'fastapi', 'express', 'rails', 'laravel', 'dotnet',
    'c#', 'c++', 'go', 'golang', 'rust', 'scala', 'kotlin', 'swift', 'objective-c',
    'r', 'matlab', 'julia', 'sas', 'spss', 'tableau', 'power bi', 'looker', 'dbt',
    'snowflake', 'databricks', 'airflow', 'luigi', 'dask', 'ray', 'mlflow', 'kubeflow',
    'jira', 'confluence', 'slack', 'teams', 'figma', 'sketch', 'adobe', 'photoshop',
    'b2b', 'b2c', 'saas', 'paas', 'iaas', 'erp', 'crm', 'cms', 'sdk', 'cli', 'oop',
    'tdd', 'bdd', 'solid', 'dry', 'kiss', 'yagni', 'mvc', 'mvvm', 'mvp', 'spa', 'pwa',
    'seo', 'a/b', 'kpi', 'okr', 'roi', 'etl', 'elt', 'olap', 'oltp', 'data warehouse'
}


@dataclass
class RankedKeyword:
    """Represents a ranked keyword with metadata."""
    keyword: str
    frequency: int
    score: float
    is_from_llm: bool
    is_repeated: bool  # Appears multiple times


def tokenize_text(text: str) -> List[str]:
    """
    Tokenize text into meaningful words and phrases.
    
    Args:
        text: Raw text to tokenize
    
    Returns:
        List of tokens (words and multi-word phrases)
    """
    # Normalize text
    text = text.lower()
    
    # Extract potential multi-word technical terms (2-3 words)
    multi_word_patterns = [
        r'\b[a-z]+[\s-][a-z]+[\s-][a-z]+\b',  # 3-word phrases
        r'\b[a-z]+[\s-][a-z]+\b',  # 2-word phrases
    ]
    
    multi_words = []
    for pattern in multi_word_patterns:
        matches = re.findall(pattern, text)
        multi_words.extend([m.replace('-', ' ').strip() for m in matches])
    
    # Extract single words
    words = re.findall(r'\b[a-z][a-z0-9+#/.]+\b', text)
    
    # Filter and combine
    all_tokens = words + multi_words
    
    return all_tokens


def calculate_term_frequency(tokens: List[str]) -> Dict[str, int]:
    """
    Calculate term frequency for tokens.
    
    Args:
        tokens: List of tokens
    
    Returns:
        Dictionary mapping terms to their frequencies
    """
    # Filter out stop words (unless they're technical terms)
    filtered_tokens = [
        t for t in tokens 
        if (t not in STOP_WORDS or t in PRESERVE_TERMS) and len(t) > 2
    ]
    
    return Counter(filtered_tokens)


def extract_keywords_from_text(text: str, min_frequency: int = 1) -> List[Tuple[str, int]]:
    """
    Extract keywords from text using frequency analysis.
    
    Args:
        text: Text to analyze
        min_frequency: Minimum frequency threshold
    
    Returns:
        List of (keyword, frequency) tuples sorted by frequency
    """
    tokens = tokenize_text(text)
    frequencies = calculate_term_frequency(tokens)
    
    # Filter by minimum frequency and sort
    keywords = [
        (term, freq) 
        for term, freq in frequencies.items() 
        if freq >= min_frequency
    ]
    
    return sorted(keywords, key=lambda x: (-x[1], x[0]))


def rank_keywords(
    text: str,
    llm_keywords: List[str],
    top_n: int = 30
) -> List[RankedKeyword]:
    """
    Combine and rank keywords from LLM extraction and frequency analysis.
    
    Scoring formula:
    - Base score = frequency
    - LLM bonus = +2 (keywords identified by LLM are likely important)
    - Technical term bonus = +1 (known technical skills)
    
    Args:
        text: Original job description text
        llm_keywords: Keywords extracted by LLM
        top_n: Number of top keywords to return
    
    Returns:
        List of RankedKeyword objects, sorted by score
    """
    # Get frequency-based keywords
    freq_keywords = extract_keywords_from_text(text)
    freq_dict = dict(freq_keywords)
    
    # Normalize LLM keywords
    llm_keywords_lower = [k.lower().strip() for k in llm_keywords]
    llm_set = set(llm_keywords_lower)
    
    # Combine all unique keywords
    all_keywords = set(freq_dict.keys()) | llm_set
    
    ranked = []
    for keyword in all_keywords:
        frequency = freq_dict.get(keyword, 0)
        
        # Calculate score
        score = frequency
        is_from_llm = keyword in llm_set
        
        if is_from_llm:
            score += 2
        
        if keyword in PRESERVE_TERMS:
            score += 1
        
        # Ensure minimum score for LLM keywords
        if is_from_llm and score < 1:
            score = 1
        
        if score > 0:
            ranked.append(RankedKeyword(
                keyword=keyword,
                frequency=frequency,
                score=score,
                is_from_llm=is_from_llm,
                is_repeated=frequency > 1
            ))
    
    # Sort by score (descending), then alphabetically
    ranked.sort(key=lambda x: (-x.score, x.keyword))
    
    return ranked[:top_n]


def format_keywords_for_display(keywords: List[RankedKeyword]) -> Dict[str, List[str]]:
    """
    Format ranked keywords for Streamlit display.
    
    Args:
        keywords: List of RankedKeyword objects
    
    Returns:
        Dictionary with categorized keywords
    """
    high_priority = []  # Score >= 3 or repeated
    medium_priority = []  # Score 2
    other = []  # Score 1
    
    for kw in keywords:
        display_text = kw.keyword
        if kw.is_repeated:
            display_text += f" (×{kw.frequency})"
        
        if kw.score >= 3 or kw.is_repeated:
            high_priority.append(display_text)
        elif kw.score >= 2:
            medium_priority.append(display_text)
        else:
            other.append(display_text)
    
    return {
        'high_priority': high_priority,
        'medium_priority': medium_priority,
        'other': other
    }

