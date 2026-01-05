"""
Tests for Schema.org JobPosting Extraction

Tests parsing of JSON-LD structured data from HTML.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from extractor.html_parser import extract_schema_job_posting


class TestExtractSchemaJobPosting:
    """Tests for Schema.org JobPosting extraction."""
    
    def test_extracts_from_greenhouse_html(self, greenhouse_html):
        """Test extraction from Greenhouse HTML with JSON-LD."""
        result = extract_schema_job_posting(greenhouse_html)
        
        assert result is not None
        assert result["title"] == "Senior Software Engineer"
        assert result["company"] == "Acme Corp"
        assert "description" in result
    
    def test_extracts_from_schema_org_graph(self, schema_org_html):
        """Test extraction from HTML with @graph structure."""
        result = extract_schema_job_posting(schema_org_html)
        
        assert result is not None
        assert result["title"] == "DevOps Engineer"
        assert "skills" in result
        assert "Kubernetes" in result["skills"]
    
    def test_extracts_from_lever_html(self, lever_html):
        """Test extraction from Lever HTML."""
        result = extract_schema_job_posting(lever_html)
        
        assert result is not None
        assert result["title"] == "Product Manager"
        assert result["company"] == "TechStart Inc."
    
    def test_returns_none_for_no_schema(self, workday_html):
        """Test that None is returned when no Schema.org data exists."""
        result = extract_schema_job_posting(workday_html)
        
        # Workday fixture doesn't have JSON-LD
        assert result is None
    
    def test_returns_none_for_minimal_html(self, minimal_html):
        """Test that None is returned for minimal HTML without schema."""
        result = extract_schema_job_posting(minimal_html)
        assert result is None
    
    def test_extracts_location(self, greenhouse_html):
        """Test that job location is extracted."""
        result = extract_schema_job_posting(greenhouse_html)
        
        assert result is not None
        assert "location" in result
        assert "San Francisco" in result["location"]
    
    def test_extracts_salary_info(self, greenhouse_html):
        """Test that salary information is extracted."""
        result = extract_schema_job_posting(greenhouse_html)
        
        assert result is not None
        assert "salary" in result
        assert "USD" in result["salary"]
    
    def test_extracts_employment_type(self, greenhouse_html):
        """Test that employment type is extracted."""
        result = extract_schema_job_posting(greenhouse_html)
        
        assert result is not None
        assert "employment_type" in result
        assert "FULL_TIME" in result["employment_type"]
    
    def test_handles_malformed_json(self):
        """Test handling of malformed JSON-LD."""
        html = '''
        <html>
        <script type="application/ld+json">
        { "invalid json": }
        </script>
        </html>
        '''
        result = extract_schema_job_posting(html)
        assert result is None
    
    def test_handles_non_job_posting_schema(self):
        """Test handling of JSON-LD that isn't JobPosting."""
        html = '''
        <html>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "Acme Corp"
        }
        </script>
        </html>
        '''
        result = extract_schema_job_posting(html)
        assert result is None
    
    def test_handles_array_of_schemas(self):
        """Test handling of JSON-LD array with multiple schemas."""
        html = '''
        <html>
        <script type="application/ld+json">
        [
            {"@type": "Organization", "name": "Acme"},
            {"@type": "JobPosting", "title": "Test Job", "description": "Test"}
        ]
        </script>
        </html>
        '''
        result = extract_schema_job_posting(html)
        
        assert result is not None
        assert result["title"] == "Test Job"


class TestSchemaDataNormalization:
    """Tests for Schema.org data normalization."""
    
    def test_normalizes_hiring_organization(self):
        """Test normalization of different hiringOrganization formats."""
        # Test with nested organization
        html = '''
        <html>
        <script type="application/ld+json">
        {
            "@type": "JobPosting",
            "title": "Engineer",
            "description": "Test",
            "hiringOrganization": {
                "@type": "Organization",
                "name": "Nested Corp"
            }
        }
        </script>
        </html>
        '''
        result = extract_schema_job_posting(html)
        assert result["company"] == "Nested Corp"
    
    def test_normalizes_skills_array(self, schema_org_html):
        """Test that skills array is properly extracted."""
        result = extract_schema_job_posting(schema_org_html)
        
        assert "skills" in result
        assert isinstance(result["skills"], list)
        assert len(result["skills"]) > 0
    
    def test_handles_employment_type_array(self, schema_org_html):
        """Test handling of employment type as array."""
        result = extract_schema_job_posting(schema_org_html)
        
        # Schema.org fixture has ["FULL_TIME", "REMOTE"]
        assert "employment_type" in result
