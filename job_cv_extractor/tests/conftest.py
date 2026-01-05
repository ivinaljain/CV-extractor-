"""
Pytest Configuration and Shared Fixtures

Provides common fixtures for testing the Job Intelligence Extractor.
All fixtures use mocked data - no real HTTP or OpenAI calls.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import Optional


# Path to fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ============================================================
# HTML Fixture Loaders
# ============================================================

@pytest.fixture
def fixtures_path():
    """Return path to fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def greenhouse_html():
    """Load sample Greenhouse job posting HTML."""
    return (FIXTURES_DIR / "greenhouse_job.html").read_text(encoding="utf-8")


@pytest.fixture
def lever_html():
    """Load sample Lever job posting HTML."""
    return (FIXTURES_DIR / "lever_job.html").read_text(encoding="utf-8")


@pytest.fixture
def workday_html():
    """Load sample Workday job posting HTML."""
    return (FIXTURES_DIR / "workday_job.html").read_text(encoding="utf-8")


@pytest.fixture
def generic_html():
    """Load sample generic job posting HTML."""
    return (FIXTURES_DIR / "generic_job.html").read_text(encoding="utf-8")


@pytest.fixture
def minimal_html():
    """Load minimal HTML for fallback testing."""
    return (FIXTURES_DIR / "minimal_job.html").read_text(encoding="utf-8")


@pytest.fixture
def schema_org_html():
    """Load HTML with Schema.org JobPosting JSON-LD."""
    return (FIXTURES_DIR / "schema_org_job.html").read_text(encoding="utf-8")


# ============================================================
# URL Fixtures
# ============================================================

@pytest.fixture
def greenhouse_urls():
    """Sample Greenhouse URLs for testing."""
    return {
        "direct": "https://boards.greenhouse.io/acme/jobs/12345",
        "embedded": "https://careers.acme.com/jobs?gh_jid=12345",
        "embed_js": "https://acme.greenhouse.io/embed/job_board/js?for=acme",
        "with_token": "https://acme.com/apply?token=12345&gh_jid=67890",
    }


@pytest.fixture
def lever_urls():
    """Sample Lever URLs for testing."""
    return {
        "direct": "https://jobs.lever.co/acme/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "with_apply": "https://jobs.lever.co/acme/a1b2c3d4-e5f6-7890-abcd-ef1234567890/apply",
    }


@pytest.fixture
def workday_urls():
    """Sample Workday URLs for testing."""
    return {
        "direct": "https://acme.wd5.myworkdayjobs.com/en-US/Careers/job/Software-Engineer_R12345",
        "alternative": "https://www.myworkdayjobs.com/acme/job/Engineering/Senior-Developer",
    }


@pytest.fixture
def generic_urls():
    """Sample generic job URLs for testing."""
    return {
        "linkedin": "https://www.linkedin.com/jobs/view/12345",
        "indeed": "https://www.indeed.com/viewjob?jk=abc123",
        "company": "https://careers.techcorp.com/jobs/software-engineer",
    }


# ============================================================
# Mock HTTP Response Fixtures
# ============================================================

@dataclass
class MockResponse:
    """Mock HTTP response object."""
    status_code: int
    text: str
    url: str
    encoding: Optional[str] = "utf-8"
    apparent_encoding: str = "utf-8"
    
    @property
    def content(self):
        return self.text.encode(self.encoding or "utf-8")


@pytest.fixture
def mock_fetch_success(greenhouse_html):
    """Mock successful HTTP fetch."""
    def _mock_get(url, **kwargs):
        return MockResponse(
            status_code=200,
            text=greenhouse_html,
            url=url
        )
    return _mock_get


@pytest.fixture
def mock_fetch_failure():
    """Mock failed HTTP fetch."""
    def _mock_get(url, **kwargs):
        return MockResponse(
            status_code=404,
            text="Not Found",
            url=url
        )
    return _mock_get


# ============================================================
# Mock OpenAI Response Fixtures
# ============================================================

@pytest.fixture
def valid_llm_response():
    """Valid LLM JSON response for job analysis."""
    return {
        "job_title": "Senior Software Engineer",
        "company": "Acme Corp",
        "job_summary": "We are looking for a Senior Software Engineer to join our growing team.",
        "responsibilities": [
            "Design and develop scalable software solutions",
            "Mentor junior developers",
            "Participate in code reviews"
        ],
        "required_skills": {
            "hard_skills": ["Python", "AWS", "Docker", "PostgreSQL", "REST APIs"],
            "soft_skills": ["Communication", "Problem-solving", "Teamwork"]
        },
        "ats_keywords": ["Python", "AWS", "Docker", "microservices", "CI/CD", "agile"],
        "inferred_skills": ["Git", "Linux", "Testing", "Documentation"],
        "seniority_level": "Senior",
        "years_of_experience": "5+ years"
    }


@pytest.fixture
def malformed_llm_response():
    """Malformed LLM response (invalid JSON)."""
    return "I'll help you analyze this job posting. Here's what I found:\n{invalid json"


@pytest.fixture
def partial_llm_response():
    """Partial LLM response (missing some fields)."""
    return {
        "job_title": "Software Engineer",
        "company": None,
        "job_summary": "A software engineering role.",
        "responsibilities": [],
        "required_skills": {
            "hard_skills": ["Python"],
            "soft_skills": []
        },
        "ats_keywords": [],
        "inferred_skills": [],
        "seniority_level": "Unknown",
        "years_of_experience": None
    }


@pytest.fixture
def mock_openai_success(valid_llm_response):
    """Mock successful OpenAI API call."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(valid_llm_response)
    mock_response.usage = MagicMock()
    mock_response.usage.total_tokens = 500
    mock_response.usage.prompt_tokens = 400
    mock_response.usage.completion_tokens = 100
    return mock_response


@pytest.fixture
def mock_openai_malformed(malformed_llm_response):
    """Mock OpenAI API returning malformed response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = malformed_llm_response
    mock_response.usage = MagicMock()
    mock_response.usage.total_tokens = 100
    return mock_response


# ============================================================
# Sample Job Text Fixtures
# ============================================================

@pytest.fixture
def sample_job_text():
    """Sample cleaned job description text."""
    return """
    Job Title: Senior Software Engineer
    Company: Acme Corp
    Location: San Francisco, CA (Remote OK)
    
    About the Role:
    We are looking for a Senior Software Engineer to join our Platform team.
    You will be responsible for designing and building scalable microservices.
    
    Responsibilities:
    - Design and develop scalable software solutions using Python and AWS
    - Build and maintain RESTful APIs and microservices
    - Mentor junior developers and participate in code reviews
    - Collaborate with product and design teams
    - Implement CI/CD pipelines and DevOps practices
    
    Requirements:
    - 5+ years of software engineering experience
    - Strong proficiency in Python
    - Experience with AWS services (EC2, Lambda, S3, RDS)
    - Experience with Docker and Kubernetes
    - Familiarity with PostgreSQL or similar databases
    - Excellent communication and problem-solving skills
    
    Nice to Have:
    - Experience with Terraform
    - Knowledge of machine learning concepts
    - Previous startup experience
    
    Benefits:
    - Competitive salary and equity
    - Health, dental, and vision insurance
    - Unlimited PTO
    - Remote work flexibility
    """


@pytest.fixture
def short_job_text():
    """Short job description that may fail content validation."""
    return "Software Engineer position available. Apply now!"


# ============================================================
# Utility Fixtures
# ============================================================

@pytest.fixture
def reset_logger():
    """Reset the Streamlit log handler between tests."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.logger import clear_streamlit_logs
    clear_streamlit_logs()
    yield
    clear_streamlit_logs()
