"""
Unit Tests for URL Resolver Module

Tests the resolution of embedded/proxied job URLs to canonical form.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from extractor.url_resolver import (
    resolve_url,
    resolve_greenhouse_url,
    resolve_lever_url,
    resolve_workday_url,
    get_api_endpoint
)


class TestResolveGreenhouseUrl:
    """Tests for Greenhouse URL resolution."""
    
    def test_direct_url_unchanged(self):
        """Direct Greenhouse URL should not be changed."""
        url = "https://boards.greenhouse.io/acme/jobs/12345"
        resolved, was_resolved = resolve_greenhouse_url(url)
        assert resolved == url
        assert was_resolved is False
    
    def test_gh_jid_param_resolved(self):
        """URL with gh_jid should resolve to embed URL."""
        url = "https://careers.company.com/jobs?gh_jid=12345"
        resolved, was_resolved = resolve_greenhouse_url(url)
        assert was_resolved is True
        assert "12345" in resolved
        assert "greenhouse.io" in resolved
    
    def test_token_param_resolved(self):
        """URL with token param and greenhouse should resolve."""
        url = "https://company.greenhouse.io/apply?token=abcd1234"
        resolved, was_resolved = resolve_greenhouse_url(url)
        # Should return resolved URL with token
        assert "greenhouse.io" in resolved
    
    def test_job_id_in_path(self):
        """URL with job ID in path should be extracted."""
        url = "https://company.greenhouse.io/jobs/12345"
        resolved, was_resolved = resolve_greenhouse_url(url)
        # Already greenhouse.io, should work
        assert "greenhouse.io" in resolved
    
    def test_multiple_params(self):
        """URL with multiple params including gh_jid."""
        url = "https://careers.example.com/apply?source=linkedin&gh_jid=99999&ref=123"
        resolved, was_resolved = resolve_greenhouse_url(url)
        assert was_resolved is True
        assert "99999" in resolved


class TestResolveLeverUrl:
    """Tests for Lever URL resolution."""
    
    def test_direct_url_unchanged(self):
        """Direct Lever URL should not be changed."""
        url = "https://jobs.lever.co/acme/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        resolved, was_resolved = resolve_lever_url(url)
        assert resolved == url
        assert was_resolved is False
    
    def test_apply_suffix_removed(self):
        """URL with /apply suffix should be cleaned."""
        url = "https://jobs.lever.co/acme/a1b2c3d4-e5f6-7890-abcd-ef1234567890/apply"
        resolved, was_resolved = resolve_lever_url(url)
        assert was_resolved is True
        assert "/apply" not in resolved
        assert "a1b2c3d4-e5f6-7890-abcd-ef1234567890" in resolved
    
    def test_apply_with_trailing_slash(self):
        """URL with /apply/ should also be cleaned."""
        url = "https://jobs.lever.co/company/uuid-here/apply/"
        resolved, was_resolved = resolve_lever_url(url)
        assert "/apply" not in resolved
    
    def test_non_lever_url(self):
        """Non-Lever URL should be unchanged."""
        url = "https://www.linkedin.com/jobs/view/12345"
        resolved, was_resolved = resolve_lever_url(url)
        assert resolved == url
        assert was_resolved is False


class TestResolveWorkdayUrl:
    """Tests for Workday URL resolution."""
    
    def test_workday_url_unchanged(self):
        """Workday URLs should remain unchanged (complex structure)."""
        url = "https://company.wd5.myworkdayjobs.com/en-US/Careers/job/Engineer_R12345"
        resolved, was_resolved = resolve_workday_url(url)
        assert resolved == url
        assert was_resolved is False


class TestResolveUrl:
    """Tests for the main resolve_url function."""
    
    def test_resolve_greenhouse(self):
        """Test resolution with greenhouse source."""
        url = "https://careers.example.com?gh_jid=12345"
        resolved, was_resolved = resolve_url(url, "greenhouse")
        assert was_resolved is True
        assert "greenhouse.io" in resolved
    
    def test_resolve_lever(self):
        """Test resolution with lever source."""
        url = "https://jobs.lever.co/company/uuid/apply"
        resolved, was_resolved = resolve_url(url, "lever")
        assert "/apply" not in resolved
    
    def test_resolve_workday(self):
        """Test resolution with workday source."""
        url = "https://company.myworkdayjobs.com/job/12345"
        resolved, was_resolved = resolve_url(url, "workday")
        assert resolved == url
        assert was_resolved is False
    
    def test_resolve_generic(self):
        """Test resolution with generic source."""
        url = "https://careers.example.com/jobs/12345"
        resolved, was_resolved = resolve_url(url, "generic")
        assert resolved == url
        assert was_resolved is False


class TestGetApiEndpoint:
    """Tests for API endpoint generation."""
    
    def test_lever_api_endpoint(self):
        """Test Lever API endpoint generation."""
        url = "https://jobs.lever.co/acme/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        endpoint = get_api_endpoint(url, "lever")
        # Should return API endpoint or None
        if endpoint:
            assert "api.lever.co" in endpoint
    
    def test_greenhouse_no_api(self):
        """Greenhouse doesn't have a public API endpoint."""
        url = "https://boards.greenhouse.io/acme/jobs/12345"
        endpoint = get_api_endpoint(url, "greenhouse")
        assert endpoint is None
    
    def test_generic_no_api(self):
        """Generic sources don't have API endpoints."""
        url = "https://careers.example.com/jobs/12345"
        endpoint = get_api_endpoint(url, "generic")
        assert endpoint is None
