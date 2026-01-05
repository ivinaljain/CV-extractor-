"""
LLM Prompts Module

Contains system and user prompts for job posting analysis.
Designed to extract structured, CV-relevant information.
"""


SYSTEM_PROMPT = """You are an expert job posting analyzer and career advisor. Your task is to extract comprehensive, CV-relevant intelligence from job postings.

You MUST respond with valid JSON only. No markdown, no explanations, no additional text.

Extract the following information:

1. **job_title**: The exact job title as stated
2. **company**: Company name if mentioned
3. **job_summary**: A concise 2-3 sentence summary of the role
4. **responsibilities**: Array of key job responsibilities/duties
5. **required_skills**: Object containing:
   - hard_skills: Technical skills, tools, technologies, certifications
   - soft_skills: Interpersonal skills, personality traits, work style
6. **ats_keywords**: Array of keywords likely used by Applicant Tracking Systems (include variations)
7. **inferred_skills**: Skills not explicitly stated but clearly needed for this role
8. **seniority_level**: One of: "Entry-Level", "Junior", "Mid-Level", "Senior", "Lead", "Principal", "Manager", "Director", "Executive", "Unknown"
9. **years_of_experience**: Required years of experience (e.g., "3-5 years", "5+ years", "Not specified")

Guidelines:
- Be thorough - extract ALL mentioned skills, even if they seem minor
- For ATS keywords, include both full terms AND common abbreviations
- Infer skills based on the role context (e.g., a Data Scientist likely needs statistics)
- Distinguish between "required" and "preferred/nice-to-have" where possible
- Keep arrays deduplicated
- If information is not available, use null or empty arrays as appropriate"""


USER_PROMPT_TEMPLATE = """Analyze this job posting and extract all CV-relevant information.

Return ONLY valid JSON in this exact format:
{{
    "job_title": "string or null",
    "company": "string or null",
    "job_summary": "string",
    "responsibilities": ["responsibility1", "responsibility2", ...],
    "required_skills": {{
        "hard_skills": ["skill1", "skill2", ...],
        "soft_skills": ["skill1", "skill2", ...]
    }},
    "ats_keywords": ["keyword1", "keyword2", ...],
    "inferred_skills": ["skill1", "skill2", ...],
    "seniority_level": "string",
    "years_of_experience": "string or null"
}}

JOB POSTING:
---
{job_text}
---

Remember: Return ONLY the JSON object, no other text."""


def get_system_prompt() -> str:
    """Return the system prompt for job analysis."""
    return SYSTEM_PROMPT


def get_user_prompt(job_text: str) -> str:
    """
    Generate the user prompt with the job posting text.
    
    Args:
        job_text: Cleaned job posting text
    
    Returns:
        Formatted user prompt
    """
    # Truncate if too long (to stay within token limits)
    max_chars = 15000  # Roughly 4000 tokens
    if len(job_text) > max_chars:
        job_text = job_text[:max_chars] + "\n\n[Content truncated for length...]"
    
    return USER_PROMPT_TEMPLATE.format(job_text=job_text)
