"""
Unit Tests for Keyword Ranker Module

Tests the TF-based keyword extraction and ranking logic.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.keyword_ranker import (
    tokenize_text,
    calculate_term_frequency,
    extract_keywords_from_text,
    rank_keywords,
    format_keywords_for_display,
    RankedKeyword,
    STOP_WORDS,
    PRESERVE_TERMS
)


class TestTokenizeText:
    """Tests for text tokenization."""
    
    def test_basic_tokenization(self):
        """Test basic word tokenization."""
        text = "Python developer with React experience"
        tokens = tokenize_text(text)
        assert "python" in tokens
        assert "react" in tokens
    
    def test_preserves_technical_terms(self):
        """Test that technical terms with special chars are preserved."""
        text = "Experience with C++ and C# programming"
        tokens = tokenize_text(text)
        assert "c++" in tokens
        assert "c#" in tokens
    
    def test_multi_word_phrases(self):
        """Test extraction of multi-word phrases."""
        text = "machine learning and deep learning experience"
        tokens = tokenize_text(text)
        # Should capture multi-word phrases
        multi_word = [t for t in tokens if ' ' in t]
        assert len(multi_word) > 0
    
    def test_lowercase_conversion(self):
        """Test that tokens are lowercased."""
        text = "Python REACT JavaScript"
        tokens = tokenize_text(text)
        assert "python" in tokens
        assert "react" in tokens
        assert "javascript" in tokens
        assert "PYTHON" not in tokens


class TestCalculateTermFrequency:
    """Tests for term frequency calculation."""
    
    def test_basic_frequency(self):
        """Test basic term frequency counting."""
        tokens = ["python", "python", "javascript", "python"]
        freq = calculate_term_frequency(tokens)
        assert freq["python"] == 3
        assert freq["javascript"] == 1
    
    def test_filters_stop_words(self):
        """Test that stop words are filtered out."""
        tokens = ["the", "python", "and", "javascript", "with"]
        freq = calculate_term_frequency(tokens)
        assert "the" not in freq
        assert "and" not in freq
        assert "python" in freq
    
    def test_preserves_technical_terms(self):
        """Test that technical terms in PRESERVE_TERMS are kept."""
        tokens = ["python", "sql", "api"]
        freq = calculate_term_frequency(tokens)
        assert "python" in freq
        assert "sql" in freq
        assert "api" in freq
    
    def test_filters_short_tokens(self):
        """Test that very short tokens are filtered."""
        tokens = ["a", "ab", "abc", "python"]
        freq = calculate_term_frequency(tokens)
        assert "a" not in freq
        assert "ab" not in freq
        assert "abc" in freq
        assert "python" in freq


class TestExtractKeywordsFromText:
    """Tests for keyword extraction from text."""
    
    def test_extract_keywords(self):
        """Test keyword extraction from job description."""
        text = """
        We are looking for a Python developer with experience in Django.
        Python is essential. Django and REST APIs are required.
        Must know SQL and PostgreSQL.
        """
        keywords = extract_keywords_from_text(text)
        
        # Should return list of (keyword, frequency) tuples
        keyword_dict = dict(keywords)
        assert "python" in keyword_dict
        assert keyword_dict["python"] >= 2  # Python appears multiple times
    
    def test_sorted_by_frequency(self):
        """Test that keywords are sorted by frequency."""
        text = "python python python java java javascript"
        keywords = extract_keywords_from_text(text)
        
        # First keyword should have highest frequency
        if keywords:
            assert keywords[0][0] == "python"
            assert keywords[0][1] == 3
    
    def test_min_frequency_filter(self):
        """Test minimum frequency filtering."""
        text = "python python java javascript"
        keywords = extract_keywords_from_text(text, min_frequency=2)
        
        keyword_names = [k[0] for k in keywords]
        assert "python" in keyword_names
        assert "java" not in keyword_names  # Only appears once


class TestRankKeywords:
    """Tests for keyword ranking."""
    
    def test_combines_llm_and_frequency(self):
        """Test that LLM keywords and frequency keywords are combined."""
        text = "Python developer with AWS experience. Python is required."
        llm_keywords = ["Python", "AWS", "Docker"]
        
        ranked = rank_keywords(text, llm_keywords)
        
        keyword_names = [k.keyword for k in ranked]
        assert "python" in keyword_names
        assert "aws" in keyword_names
        assert "docker" in keyword_names  # From LLM even if not in text
    
    def test_llm_keywords_get_bonus(self):
        """Test that LLM-extracted keywords get score bonus."""
        text = "Python developer position"
        llm_keywords = ["Python"]
        
        ranked = rank_keywords(text, llm_keywords)
        python_kw = next(k for k in ranked if k.keyword == "python")
        
        # LLM keywords get +2 bonus
        assert python_kw.is_from_llm is True
        assert python_kw.score >= 2
    
    def test_repeated_keywords_flagged(self):
        """Test that repeated keywords are flagged."""
        text = "Python Python Python developer"
        llm_keywords = []
        
        ranked = rank_keywords(text, llm_keywords)
        python_kw = next((k for k in ranked if k.keyword == "python"), None)
        
        if python_kw:
            assert python_kw.frequency >= 3
            assert python_kw.is_repeated is True
    
    def test_top_n_limit(self):
        """Test that top_n limits results."""
        text = "a b c d e f g h i j k l m n o p q r s t"
        llm_keywords = list("abcdefghijklmnopqrst")
        
        ranked = rank_keywords(text, llm_keywords, top_n=5)
        assert len(ranked) <= 5


class TestFormatKeywordsForDisplay:
    """Tests for display formatting."""
    
    def test_categorizes_by_priority(self):
        """Test that keywords are categorized by priority."""
        keywords = [
            RankedKeyword("python", 3, 5, True, True),   # High priority
            RankedKeyword("aws", 1, 2, True, False),     # Medium priority
            RankedKeyword("docker", 0, 1, True, False),  # Other
        ]
        
        formatted = format_keywords_for_display(keywords)
        
        assert "high_priority" in formatted
        assert "medium_priority" in formatted
        assert "other" in formatted
    
    def test_repeated_keywords_show_count(self):
        """Test that repeated keywords show count in display."""
        keywords = [
            RankedKeyword("python", 3, 5, True, True),
        ]
        
        formatted = format_keywords_for_display(keywords)
        
        # High priority should include the repeated keyword with count
        assert any("×3" in kw for kw in formatted["high_priority"])
    
    def test_empty_keywords(self):
        """Test handling of empty keyword list."""
        formatted = format_keywords_for_display([])
        
        assert formatted["high_priority"] == []
        assert formatted["medium_priority"] == []
        assert formatted["other"] == []


class TestPreserveTerms:
    """Tests for PRESERVE_TERMS constant."""
    
    def test_common_tech_terms_preserved(self):
        """Test that common tech terms are in PRESERVE_TERMS."""
        expected_terms = ["python", "java", "aws", "docker", "kubernetes", "sql"]
        for term in expected_terms:
            assert term in PRESERVE_TERMS, f"{term} should be in PRESERVE_TERMS"
    
    def test_stop_words_not_in_preserve(self):
        """Test that stop words are not in PRESERVE_TERMS."""
        for word in ["the", "and", "or", "is", "are"]:
            assert word not in PRESERVE_TERMS
