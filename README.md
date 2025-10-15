# DSO Law Fetcher

A comprehensive web scraping and legal document analysis system that automatically monitors government websites for new legislation relevant to DSO National Laboratories (Singapore's defence research and development organization).

## Overview

The DSO Law Fetcher is a Python-based web application that:
- Scrapes legislation from multiple government websites and RSS feeds
- Analyzes content for relevance to defence, security, and research topics
- Uses AI (DeepSeek API) to generate summaries and impact assessments
- Stores results in organized markdown files with comprehensive metadata
- Provides a web interface for browsing and searching legislation

## Features

- **Multi-source scraping**: Supports both RSS feeds and content page scraping
- **Keyword-based relevance scoring**: Automatically identifies laws relevant to defence and research
- **AI-powered summarization**: Generates concise summaries using DeepSeek AI
- **Web interface**: Modern, responsive dashboard for browsing laws
- **Category organization**: Laws organized by thematic categories (Defence, Finance, HR, etc.)
- **Search and filtering**: Advanced search capabilities with date and category filters

## System Architecture

```
law_fetcher.py (Flask Server)
├── Web Scraping Engine
│   ├── RSS Feed Parser (feedparser)
│   └── Content Page Scraper (BeautifulSoup)
├── Relevance Engine
│   ├── Keyword Matching
│   └── Scoring Algorithm
├── AI Integration (DeepSeek API)
│   ├── Summarization
│   └── Impact Analysis
└── Markdown Storage
    └── Organized by date and website
```

## Installation

### Prerequisites

- Python 3.7+
- pip (Python package manager)
- DeepSeek API key

### Step 1: Install Dependencies

```bash
# Install required Python packages
pip install flask flask-cors feedparser beautifulsoup4 requests
```

### Step 2: Configure API Key

Edit `config.py` and add your DeepSeek API key:

```python
# DeepSeek API Configuration
DEEPSEEK_API_KEY = "your_deepseek_api_key_here"
```

### Step 3: Configure Keywords (Optional)

Edit `keywords.json` to customize the relevance keywords:

```json
{
  "keywords": [
    "defence", "security", "military", "cybersecurity",
    "finance", "procurement", "research", "technology"
    // Add your custom keywords here
  ]
}
```

## Usage

### Running the Application

#### Method 1: Using the Batch File (Windows)
```bash
run.bat
```

#### Method 2: Manual Execution
```bash
# Install dependencies first
pip install flask flask-cors

# Run the application
python law_fetcher.py
```

The application will start a Flask server on `http://localhost:5000`

### Web Interface

Open your browser and navigate to `http://localhost:5000` to access the web dashboard.

### API Endpoints

- `GET /` - Main web interface
- `GET /api/markdown-files` - Get all markdown files
- `POST /api/scrape` - Scrape specific website
- `POST /api/scrape-all` - Scrape all websites
- `GET /api/websites` - Get available website configurations
- `GET /api/category/{category_name}` - Get laws by category

### Supported Websites

The system monitors multiple government websites including:

- **SSO AGC** (Singapore Statutes Online) - New legislation RSS feed
- **IRAS** - Corporate income tax regulations
- **ACRA** - Corporate compliance and financial reporting
- **MOM** - Employment and workplace safety laws
- **CAAS** - Aviation regulations
- **IMDA** - Telecommunications and spectrum management
- **HSA** - Health sciences and controlled substances
- And many more...

## Configuration

### Website Configuration

Website configurations are defined in `law_fetcher.py` in the `WEBSITE_CONFIGS` dictionary. Each configuration includes:

- `type`: "rss" or "content_page"
- `url`: Target URL to scrape
- `content_selector`: CSS selector for main content
- `title_selector`: CSS selector for page title

### Categories

Laws are organized into categories defined in `WEBSITE_CATEGORIES`:

- **SSO**: Singapore Statutes Online
- **Finance**: Tax, corporate compliance, financial regulations
- **HR**: Employment, manpower, workplace regulations
- **Air**: Aviation and aerospace regulations
- **Guided System**: Missile technology control
- **Frequency EM**: Spectrum management
- **Communications**: Telecommunications
- **Electronics**: Electronic systems and components
- **DMERI**: Defence medical, environmental, research infrastructure

## Output Structure

Scraped laws are saved in the `output/` directory organized by date:

```
output/
├── 2025-09-15/
│   ├── sso_agc_gov_sg.md
│   ├── www_mom_gov_sg.md
│   └── www_acra_gov_sg.md
├── 2025-09-14/
│   └── ...
└── 1mth/ (aggregated monthly views)
```

Each markdown file contains:
- Law title and publication date
- Source URL
- Relevance score
- AI-generated summary
- Keyword matches
- Impact assessment for DSO

## Customization

### Adding New Websites

1. Add website configuration to `WEBSITE_CONFIGS`
2. Add to appropriate category in `WEBSITE_CATEGORIES`
3. Update filename mapping in the web interface code

### Modifying Keywords

Edit `keywords.json` to add or remove relevance keywords. The system will automatically rescore laws based on new keywords.

### Adjusting Relevance Threshold

Modify `MIN_RELEVANCE_SCORE` in `law_fetcher.py` to change the minimum score required for a law to be considered relevant.

## Troubleshooting

### Common Issues

1. **API Key Error**: Ensure `DEEPSEEK_API_KEY` is set in `config.py`
2. **Dependency Issues**: Run `pip install -r requirements.txt` (if available) or install packages manually
3. **SSL Certificate Errors**: The application disables SSL verification for scraping
4. **Network Issues**: Check firewall settings for web scraping

### Logging

Debug information is logged to `law_fetcher_debug.log`

## Development

### File Structure

```
.
├── law_fetcher.py      # Main application (Flask server)
├── config.py           # API key configuration
├── keywords.json       # Relevance keywords
├── index.html          # Web interface
├── app.js              # Frontend JavaScript
├── styles.css          # Styling
├── run.bat             # Windows batch file
└── output/             # Generated markdown files
```

### Adding Features

- **New Scrapers**: Implement new scraping functions following the existing patterns
- **Additional AI Analysis**: Extend the `AI_call` function for new types of analysis
- **Export Formats**: Add support for JSON, CSV, or other export formats
- **Notifications**: Implement email or webhook notifications for new laws


