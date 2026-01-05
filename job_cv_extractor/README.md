# Job Intelligence Extractor

A local Streamlit application that extracts CV-relevant intelligence from job posting URLs.

## Features

- **Universal URL Support**: Works with any job posting URL (LinkedIn, Indeed, Greenhouse, Lever, etc.)
- **Multi-Layer Extraction**:
  - Schema.org JobPosting JSON-LD parsing
  - HTML parsing with BeautifulSoup
  - Trafilatura fallback for difficult pages
- **LLM-Powered Analysis**: Uses OpenAI to extract structured information
- **ATS Keyword Ranking**: Frequency-based keyword prioritization
- **Clean UI**: Collapsible sections, skill tags, and progress indicators

## Extracted Information

- Job Title & Company
- Job Summary
- Responsibilities
- Required Skills (Hard & Soft)
- ATS Keywords (prioritized)
- Inferred/Implied Skills
- Seniority Level
- Years of Experience

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set OpenAI API Key

Option A: Environment variable
```bash
# Windows PowerShell
$env:OPENAI_API_KEY = "your-api-key-here"

# Linux/Mac
export OPENAI_API_KEY="your-api-key-here"
```

Option B: Enter in the app sidebar

### 3. Run the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

1. Paste a job posting URL in the input field
2. Click "Extract"
3. Wait for the extraction and analysis
4. Review the extracted information in collapsible sections

## Project Structure

```
job_cv_extractor/
├── app.py                      # Streamlit entry point
├── extractor/
│   ├── fetcher.py              # URL fetching with browser headers
│   ├── html_parser.py          # BeautifulSoup + Schema.org parsing
│   ├── content_cleaner.py      # Boilerplate removal
│   └── fallback_extractor.py   # Trafilatura fallback
├── llm/
│   ├── prompts.py              # LLM system + user prompts
│   └── analyzer.py             # OpenAI API integration
├── utils/
│   ├── keyword_ranker.py       # TF-based keyword ranking
│   └── logger.py               # Logging configuration
├── logs/
│   └── app.log                 # Application logs
├── requirements.txt
└── README.md
```

## Notes

- This app is for **personal use only**
- No data is stored or transmitted beyond OpenAI API calls
- Uses `gpt-4o-mini` by default for cost efficiency
- Logs are saved to `logs/app.log` for debugging

## Troubleshooting

### "Could not fetch URL"
- Check if the URL is accessible in your browser
- Some sites may block automated requests

### "Could not extract meaningful content"
- The page may require JavaScript rendering
- Try a different job posting from the same company

### "OpenAI API error"
- Verify your API key is correct
- Check your OpenAI account has available credits
