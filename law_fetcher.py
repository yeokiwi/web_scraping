import feedparser
import re
import logging
import requests
import json
import os
import datetime
from urllib.parse import urlparse
import ssl
from bs4 import BeautifulSoup
from config import DEEPSEEK_API_KEY
import urllib3
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import glob

# Load keywords
with open("keywords.json", "r", encoding="utf-8") as f:
    data = json.load(f)
DSO_KEYWORDS = data["keywords"]

# =========================
# Constants / Globals
# =========================
WEBSITE_CONFIGS = {
    "sso_agc": {
        "type": "rss",
        "url": "https://sso.agc.gov.sg/What%27s-New/New-Legislation/RSS",
        "content_selector": "div#legisContent, div.legis-content, div.content, main",
        "title_selector": "h1, title"
    },
    "iras_cit": {
        "type": "content_page",
        "url": "https://www.iras.gov.sg/taxes/corporate-income-tax",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "acra_main": {
        "type": "content_page",
        "url": "https://www.acra.gov.sg/",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "acra_frs": {
        "type": "content_page",
        "url": "https://www.acra.gov.sg/accountancy/accounting-standards/pronouncements/financial-reporting-standards/2023-volume",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "singstat": {
        "type": "content_page",
        "url": "https://www.singstat.gov.sg/",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "mom_employment": {
        "type": "content_page",
        "url": "https://www.mom.gov.sg/employment-practices/employment-act",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "mom_wic": {
        "type": "content_page",
        "url": "https://www.mom.gov.sg/workplace-safety-and-health/work-injury-compensation",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "profamily_leave": {
        "type": "content_page",
        "url": "https://www.profamilyleave.msf.gov.sg",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "cpf": {
        "type": "content_page",
        "url": "https://www.cpf.gov.sg",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "mom_retirement": {
        "type": "content_page",
        "url": "https://www.mom.gov.sg/employment-practices/retirement",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "mom_reemployment": {
        "type": "content_page",
        "url": "https://www.mom.gov.sg/employment-practices/re-employment",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "caas_air_nav": {
        "type": "content_page",
        "url": "https://www.caas.gov.sg/legislation-regulations/legislation/air-navigation-act",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "caas_air_nav_order": {
        "type": "content_page",
        "url": "https://www.caas.gov.sg/docs/default-source/pdf/air-navigation-order_.pdf",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "ecfr_part_21": {
        "type": "content_page",
        "url": "https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-21",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "ecfr_part_23": {
        "type": "content_page",
        "url": "https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-23",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "ecfr_part_25": {
        "type": "content_page",
        "url": "https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-25?toc=1",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "ecfr_part_29": {
        "type": "content_page",
        "url": "https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-29",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "ecfr_part_31": {
        "type": "content_page",
        "url": "https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-31?toc=1",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "ecfr_part_39": {
        "type": "content_page",
        "url": "https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-39",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "ecfr_part_91": {
        "type": "content_page",
        "url": "https://www.ecfr.gov/current/title-14/chapter-I/subchapter-F/part-91",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "mtcr_annex": {
        "type": "content_page",
        "url": "https://www.mtcr.info/en/mtcr-annex",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "imda_spectrum": {
        "type": "content_page",
        "url": "https://www.imda.gov.sg/-/media/imda/files/regulation-licensing-and-consultations/frameworks-and-policies/spectrum-management-and-coordination/spectrummgmthb.pdf",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "imda_telecom": {
        "type": "content_page",
        "url": "https://www.imda.gov.sg/regulations-and-licensing-listing/telecommunications-act-1999",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "nas_gov_records": {
        "type": "content_page",
        "url": "https://www.nas.gov.sg/archivesonline/government_records/record-details/0f5f57c3-4d57-11e7-9199-0050568939ad",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "nas_gov_pdf": {
        "type": "content_page",
        "url": "https://www.nas.gov.sg/archivesonline/government_records/docs/0f8018f7-4d57-11e7-9199-0050568939ad/S.18of2001.pdf",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "nparks_animals": {
        "type": "content_page",
        "url": "https://www.nparks.gov.sg/avs/resources/legislation/animals-and-birds-act-chapter-7",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "nparks_naclar": {
        "type": "content_page",
        "url": "https://www.nparks.gov.sg/avs/animals/animals-in-scientific-research/naclar-guidelines/naclar-guidelines",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "nparks_animals_page2": {
        "type": "content_page",
        "url": "https://www.nparks.gov.sg/avs/resources/legislation/animals-and-birds-act-chapter-7?page=2",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "moh_biosafety": {
        "type": "content_page",
        "url": "https://www.moh.gov.sg/biosafety/home",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "opcw_cwc": {
        "type": "content_page",
        "url": "https://www.opcw.org/chemical-weapons-convention",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "gmac_news": {
        "type": "content_page",
        "url": "https://www.gmac.sg/news",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "moh_medical_acts": {
        "type": "content_page",
        "url": "https://hpp.moh.gov.sg/medical-acts-statutes/",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "hsa_poisons": {
        "type": "content_page",
        "url": "https://hsa.gov.sg/poisons",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "hsa_controlled_drugs": {
        "type": "content_page",
        "url": "https://www.hsa.gov.sg/controlled-drugs-psychotropic-substances/controlled-drugs/apply",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "moh_hcsa": {
        "type": "content_page",
        "url": "https://www.moh.gov.sg/hcsa/resources",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    },
    "mom_wsh": {
        "type": "content_page",
        "url": "https://mom.gov.sg/workplace-safety-and-health/workplace-safety-and-health-act",
        "content_selector": "main",
        "title_selector": "h1",
        "section_selectors": ["h2"]
    }
}

DEFAULT_WEBSITE = "sso_agc"
DEBUG_LOG = "law_fetcher_debug.log"

WEBSITE_CATEGORIES = {
    "All": [
        "sso_agc", "iras_cit", "acra_main", "acra_frs", "singstat",
        "mom_employment", "mom_wic", "profamily_leave", "cpf",
        "mom_retirement", "mom_reemployment",
        "caas_air_nav", "caas_air_nav_order", "ecfr_part_21",
        "ecfr_part_23", "ecfr_part_25", "ecfr_part_29",
        "ecfr_part_31", "ecfr_part_39", "ecfr_part_91",
        "mtcr_annex","imda_spectrum", "imda_telecom",
        "nas_gov_records", "nas_gov_pdf",
        "nparks_animals", "nparks_naclar", "nparks_animals_page2",
        "moh_biosafety", "opcw_cwc", "gmac_news", "moh_medical_acts",
        "hsa_poisons", "hsa_controlled_drugs", "moh_hcsa", "mom_wsh"

    ],
    "SSO": ["sso_agc"],
    "finance": [
        "iras_cit", "acra_main", "acra_frs", "singstat"
    ],
    "hr": [
        "mom_employment", "mom_wic", "profamily_leave", "cpf",
        "mom_retirement", "mom_reemployment"
    ],
    "air": [
        "caas_air_nav", "caas_air_nav_order", "ecfr_part_21",
        "ecfr_part_23", "ecfr_part_25", "ecfr_part_29",
        "ecfr_part_31", "ecfr_part_39", "ecfr_part_91"
    ],
    "guided_system": ["mtcr_annex"],
    "frequency_em": ["imda_spectrum"],
    "communications": ["imda_telecom"],
    "electronics": ["nas_gov_records", "nas_gov_pdf"],
    "dmeri": [
        "nparks_animals", "nparks_naclar", "nparks_animals_page2",
        "moh_biosafety", "opcw_cwc", "gmac_news", "moh_medical_acts",
        "hsa_poisons", "hsa_controlled_drugs", "moh_hcsa", "mom_wsh"
    ]
}


# Validate API key
if not DEEPSEEK_API_KEY:
    raise ValueError("Please set your DeepSeek API key in config.py (DEEPSEEK_API_KEY)")

# =========================
# Logging
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(DEBUG_LOG, encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

logger.info("=== Starting Law Fetcher (Markdown Only) ===")
logger.info(f"Timestamp: {datetime.datetime.now().isoformat()}")

print("=== Starting Law Fetcher (Markdown Only) ===")
print(f"Current time: {datetime.datetime.now().isoformat()}")
print("Debug logging enabled - check law_fetcher_debug.log for details")

# =========================
# SSL / HTTP Clients
# =========================
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.packages.urllib3.disable_warnings()


# Headers to look like a real browser
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# =========================
# Relevance Scoring Config
# =========================
MIN_RELEVANCE_SCORE = 1.0
KEYWORD_BASE_WEIGHT = 1.0
TITLE_WEIGHT_MULTIPLIER = 2.0

# =========================
# Helpers: Keywords
# =========================
def load_keywords():
    """Load keywords from keywords.json"""
    try:
        if os.path.exists("keywords.json"):
            with open("keywords.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "keywords" in data:
                return [kw.strip() for kw in data["keywords"] if isinstance(kw, str) and kw.strip()]
            if isinstance(data, list):
                return [kw.strip() for kw in data if isinstance(kw, str) and kw.strip()]
        return list(DSO_KEYWORDS)
    except Exception as e:
        logger.warning(f"Failed to load keywords: {e}. Using defaults.")
        return list(DSO_KEYWORDS)



# =========================
# Content Scraping
# =========================
def scrape_content_page(config):
    """Scrape content from a single content page, digging deeper for legislation updates"""
    url = config.get("url")
    if not url:
        logger.error("No URL specified in config")
        return []
    
    try:
        response = requests.get(url, headers=BROWSER_HEADERS, timeout=6000, verify=False)
        if response.status_code != 200:
            logger.error(f"Failed to fetch {url}: Status {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract main content
        content_selectors = config.get("content_selector", "").split(", ")
        content_element = None
        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                break
        
        if not content_element:
            content_element = soup.find('main') or soup.find('article') or soup
        
        # Extract title
        title_selectors = config.get("title_selector", "").split(", ")
        title = None
        for selector in title_selectors:
            title_element = soup.select_one(selector)
            if title_element:
                title = title_element.get_text(strip=True)
                break
        
        if not title:
            title = soup.title.get_text(strip=True) if soup.title else "Untitled Content"
        
        # Get base content first
        content_text = content_element.get_text(separator="\n", strip=True)[:20000]
        
        # Try to extract actual publication/amendment date from content
        published_date = datetime.datetime.now().isoformat()
        
        # Look for date patterns in the content (e.g., "August 28, 2025", "2025-08-28")
        date_patterns = [
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}',
            r'\d{4}-\d{2}-\d{2}',
            r'amended.*\d{4}',
            r'effective.*\d{4}',
            r'last.*updated.*\d{4}'
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, content_text, re.IGNORECASE)
            if date_match:
                try:
                    # Try to parse the found date
                    date_str = date_match.group(0)
                    # Convert month names to numbers if needed
                    if re.search(r'(?:January|February|March|April|May|June|July|August|September|October|November|December)', date_str, re.IGNORECASE):
                        published_date = datetime.datetime.strptime(date_str, '%B %d, %Y').isoformat()
                    elif re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                        published_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').isoformat()
                    break
                except ValueError:
                    continue
        
        # Look for legislation-related links to dig deeper
        legislation_updates = []
        
        # Look for common patterns that might indicate legislation updates
        legislation_patterns = [
            r'legislation', r'act', r'regulation', r'law', r'bill', 
            r'what\'s new', r'latest updates', r'recent changes', r'amendment',
            r'circular', r'notice', r'guideline', r'policy'
        ]
        
        # Check for links that might contain legislation updates
        potential_links = []
        for link in soup.find_all('a', href=True):
            link_text = link.get_text(strip=True).lower()
            link_href = link['href']
            
            # Convert relative URLs to absolute
            if link_href.startswith('/'):
                parsed_url = urlparse(url)
                link_href = f"{parsed_url.scheme}://{parsed_url.netloc}{link_href}"
            elif not link_href.startswith(('http://', 'https://')):
                link_href = f"{url}/{link_href}"
            
            # Check if link text suggests legislation content
            for pattern in legislation_patterns:
                if re.search(pattern, link_text, re.IGNORECASE):
                    potential_links.append((link_text, link_href))
                    break
        
        # Follow up to 3 most promising links to get deeper content
        followed_content = ""
        for i, (link_text, link_url) in enumerate(potential_links[:3]):
            try:
                logger.info(f"Following legislation link: {link_text} -> {link_url}")
                link_response = requests.get(link_url, headers=BROWSER_HEADERS, timeout=6000, verify=False)
                if link_response.status_code == 200:
                    link_soup = BeautifulSoup(link_response.text, 'html.parser')
                    link_content_element = link_soup.find('main') or link_soup.find('article') or link_soup
                    if link_content_element:
                        link_content = link_content_element.get_text(separator="\n", strip=True)[:5000]
                        followed_content += f"\n\n--- Legislation Update from {link_text} ---\n{link_content}"
            except Exception as e:
                logger.debug(f"Error following link {link_url}: {e}")
        
        # Combine main content with followed legislation content
        if followed_content:
            content_text += followed_content
        
        return [{
            "title": title,
            "link": url,
            "published": published_date,
            "description": f"Content from {url} with legislation updates",
            "content": content_text
        }]
        
    except Exception as e:
        logger.error(f"Error scraping content page {url}: {e}")
        return []

def scrape_rss_feed(config):
    """Scrape content from RSS feed"""
    url = config.get("url")
    if not url:
        logger.error("No RSS URL specified in config")
        return []
    
    try:
        response = requests.get(url, headers=BROWSER_HEADERS, timeout=6000, verify=False)
        if response.status_code != 200:
            logger.error(f"Failed to fetch RSS: Status {response.status_code}")
            return []
        
        feed = feedparser.parse(response.text)
        if not feed.entries:
            logger.error("No entries in RSS feed")
            return []
        
        results = []
        for entry in feed.entries:
            try:
                title = entry.get("title", "")
                link = entry.get("link", "")
                description = entry.get("summary", "") or entry.get("description", "")
                
                # Fetch full content
                content_text = ""
                try:
                    r = requests.get(link, headers=BROWSER_HEADERS, timeout=6000, verify=False)
                    if r.status_code == 200:
                        soup = BeautifulSoup(r.text, 'html.parser')
                        content_selectors = config.get("content_selector", "").split(", ")
                        content_element = None
                        for selector in content_selectors:
                            content_element = soup.select_one(selector)
                            if content_element:
                                break
                        if not content_element:
                            content_element = soup.find('main') or soup
                        content_text = content_element.get_text(separator="\n", strip=True)[:20000]
                except Exception as e:
                    logger.debug(f"Full content fetch failed: {e}")
                    content_text = description
                
                results.append({
                    "title": title,
                    "link": link,
                    "published": entry.get("published"),
                    "description": description,
                    "content": content_text
                })
            except Exception as e:
                logger.warning(f"Error processing RSS entry: {e}")
        
        return results
        
    except Exception as e:
        logger.error(f"RSS scraping failed: {e}")
        return []

# =========================
# AI Connectivity
# =========================
def AI_call(user_input, system_msg=None):
    """Summarize content via DeepSeek using direct HTTP requests"""
    try:
        response = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'deepseek-chat',
                'messages': [
                    {
                        'role': 'system',
                        'content': (system_msg or "You are a helpful summary assistant. Summarize this legal document, focus only on changes made. Limit to one concise paragraph.")[:10000]
                    },
                    {
                        'role': 'user', 
                        'content': (user_input or "")[:10000]
                    },
                ],
                'max_tokens': 3000,
                'temperature': 0.3
            },
            timeout=30,
            verify=False
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('choices'):
                return result['choices'][0]['message']['content'].strip() or "Summary unavailable."
            return "Summary unavailable."
        else:
            logger.warning(f"AI call failed: Status {response.status_code} - {response.text}")
            return "New legislation update available"
            
    except Exception as e:
        logger.warning(f"AI call failed: {e}")
        return "New legislation update available"

# =========================
# Relevance Calculation
# =========================
def calculate_relevance_score(title, description, content, keywords):
    score = 0.0
    matches = []
    title_lower = (title or "").lower()
    description_lower = (description or "").lower()
    content_lower = (content or "").lower()

    for kw in keywords:
        k = kw.lower()
        kw_score = 0.0

        t = len(re.findall(rf"\b{re.escape(k)}\b", title_lower))
        if t:
            kw_score += t * KEYWORD_BASE_WEIGHT * TITLE_WEIGHT_MULTIPLIER
            matches.append(f"{kw} (title: {t})")

        d = len(re.findall(rf"\b{re.escape(k)}\b", description_lower))
        if d:
            kw_score += d * KEYWORD_BASE_WEIGHT
            if kw not in [m.split(" (")[0] for m in matches]:
                matches.append(f"{kw} (desc: {d})")

        c = len(re.findall(rf"\b{re.escape(k)}\b", content_lower))
        if c:
            kw_score += c * KEYWORD_BASE_WEIGHT * 0.5
            if kw not in [m.split(" (")[0] for m in matches]:
                matches.append(f"{kw} (content: {c})")

        score += kw_score

    return score, matches

# =========================
# Previous Day Check Functions
# =========================
def get_last_saved_date():
    """Get the date string for the last saved date before today"""
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    output_dirs = [d for d in os.listdir('output') 
                  if os.path.isdir(os.path.join('output', d)) 
                  and re.match(r'\d{4}-\d{2}-\d{2}', d)
                  and d < today]  # Only consider dates before today
                  
    if not output_dirs:
        # If no saved dates, use yesterday as fallback
        previous_day = datetime.datetime.now() - datetime.timedelta(days=1)
        return previous_day.strftime('%Y-%m-%d')
    
    # Sort dates and get the most recent one before today
    sorted_dates = sorted(output_dirs, reverse=True)
    return sorted_dates[0] if sorted_dates else ''

def parse_markdown_file(filepath):
    """
    Parse a markdown file and extract laws/legislation information
    Returns a list of dictionaries with law data
    """
    laws = []
    try:
        if not os.path.exists(filepath):
            return laws
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split content by law sections (separated by --- with optional newlines)
        # Handle both ---\n\n and ---\n patterns
        law_sections = re.split(r'---\s*\n', content)
        
        for section in law_sections:
            if not section.strip():
                continue
                
            law_data = {}
            lines = section.strip().split('\n')
            
            # Extract title (starts with ##)
            for line in lines:
                if line.startswith('## '):
                    law_data['title'] = line[3:].strip()
                    break
            
            # Extract link from metadata - handle different formats
            for line in lines:
                if line.startswith('- **Link:** '):
                    law_data['link'] = line[11:].strip()
                    break
                elif line.startswith('**Link:** '):
                    law_data['link'] = line[9:].strip()
                    break
                elif line.startswith('Link: '):
                    law_data['link'] = line[6:].strip()
                    break
            
            # Extract is_new status (only present in newer files)
            for line in lines:
                if line.startswith('- **Is New:** '):
                    is_new_str = line[13:].strip().lower()
                    law_data['is_new'] = (is_new_str == 'true')
                    break
            
            # For older files without is_new field, assume it's not new
            if 'is_new' not in law_data:
                law_data['is_new'] = False
            
            if 'title' in law_data and 'link' in law_data:
                laws.append(law_data)
                
    except Exception as e:
        logger.warning(f"Error parsing markdown file {filepath}: {e}")
    
    return laws

def check_previous_day_law_exists(current_law_data):
    """
    Check if a law exists in any previous output folders
    Returns True if law exists in any previous record, False if it's completely new
    """
    website_url = current_law_data.get("link", "")
    parsed_url = urlparse(website_url)
    domain = parsed_url.netloc.replace('.', '_')
    current_title = current_law_data.get('title', '').lower()
    current_link = current_law_data.get('link', '')
    
    # Get all date folders, sorted ascending for consistency
    output_dirs = sorted([d for d in os.listdir('output') if os.path.isdir(os.path.join('output', d)) and re.match(r'\d{4}-\d{2}-\d{2}', d)])
    today = datetime.datetime.now().strftime('%Y-%m-%d')

    # Check all folders except today's
    for date_folder in output_dirs:
        if date_folder >= today:  # Skip current/future dates
            continue

        filepath = os.path.join('output', date_folder, f"{domain}.md")
        if not os.path.exists(filepath):
            continue

        previous_laws = parse_markdown_file(filepath)

        # Check each law in the current file
        for prev_law in previous_laws:
            prev_title = prev_law.get('title', '').lower()
            prev_link = prev_law.get('link', '')

            # Check if title and link match (link is more reliable)
            if current_link and prev_link and current_link == prev_link:
                return True
            # Fallback: check if titles are similar (fuzzy match)
            elif current_title and prev_title and current_title == prev_title:
                return True

    return False

def find_earliest_law_record(law_data):
    """
    Search through all output folders to find the earliest occurrence of a law
    Returns the date string of the earliest occurrence, or None if not found
    """
    website_url = law_data.get("link", "")
    parsed_url = urlparse(website_url)
    domain = parsed_url.netloc.replace('.', '_')
    current_title = law_data.get('title', '').lower()
    current_link = law_data.get('link', '')
    
    # Get all date folders
    output_dirs = [d for d in os.listdir('output') if os.path.isdir(os.path.join('output', d)) and re.match(r'\d{4}-\d{2}-\d{2}', d)]
    if not output_dirs:
        return None
    
    # Sort dates in ascending order (oldest first)
    sorted_dates = sorted(output_dirs)
    
    earliest_date = None
    
    for date in sorted_dates:
        filepath = os.path.join('output', date, f"{domain}.md")
        if not os.path.exists(filepath):
            continue
            
        # Parse the markdown file
        laws = parse_markdown_file(filepath)
        
        for law in laws:
            prev_title = law.get('title', '').lower()
            prev_link = law.get('link', '')
            
            # Check if this is the same law (link is more reliable)
            if current_link and prev_link and current_link == prev_link:
                earliest_date = date
                break
            # Fallback: check if titles are similar
            elif current_title and prev_title and current_title == prev_title:
                earliest_date = date
                break
                
        if earliest_date:
            break
    
    return earliest_date

# =========================
# Save results to markdown
# =========================
def save_to_markdown(law_data, summary_text, laws_affected, DSO_relevance):
    """
    Save law details to markdown file in output folder with comprehensive data
    """
    # Create dated folder path
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    output_folder = os.path.join('output', today)
    os.makedirs(output_folder, exist_ok=True)

    # Create file name from website domain
    website_url = law_data.get("link", "")
    parsed_url = urlparse(website_url)
    domain = parsed_url.netloc.replace('.', '_')
    filename = f"{domain}.md"
    filepath = os.path.join(output_folder, filename)

    # Check if law exists in any previous record - if it exists anywhere, then it's NOT new
    law_exists_in_previous = check_previous_day_law_exists(law_data)
    is_new = not law_exists_in_previous
    
    # Additional date-based logic for is_new flag

    published_date = law_data.get('published', 'Unknown')
    # Normalize published_date to ISO format (YYYY-MM-DD)
    def normalize_date(date_str):
        if not date_str or date_str == 'Unknown':
            return datetime.datetime.now().strftime('%Y-%m-%d')
        try:
            # Try ISO format first
            return datetime.datetime.fromisoformat(date_str).strftime('%Y-%m-%d')
        except Exception:
            pass
        try:
            # Try RFC 2822 (e.g. 'Mon, 02 Jun 2025 00:00:00 +0800')
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str).strftime('%Y-%m-%d')
        except Exception:
            pass
        # Try to extract YYYY-MM-DD from string
        import re
        m = re.search(r'(\d{4}-\d{2}-\d{2})', date_str)
        if m:
            return m.group(1)
        # Fallback: today
        return datetime.datetime.now().strftime('%Y-%m-%d')

    published_date = normalize_date(published_date)
    law_data['published'] = published_date

    # Update is_new logic with normalized date
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    is_new = is_new or (published_date >= today)
    law_data["is_new"] = is_new

    # Handle publish date logic for existing records
    if not is_new and (not published_date or published_date == 'Unknown'):
        earliest_date = find_earliest_law_record(law_data)
        if earliest_date:
            published_date = normalize_date(earliest_date)
            law_data["published"] = published_date

    # Write/append markdown content
    mode = 'a' if os.path.exists(filepath) else 'w'
    with open(filepath, mode, encoding='utf-8') as f:
        if mode == 'w':
            # Write header for new file
            f.write(f"# Laws from {parsed_url.netloc}\n")
            f.write(f"**Date:** {today}\n\n")
        
        # Write comprehensive law details
        f.write(f"## {law_data.get('title', 'Untitled Legislation')}\n\n")
        
        # Basic metadata
        f.write("### Metadata\n")
        f.write(f"- **Published:** {published_date}\n")
        f.write(f"- **Link:** {website_url}\n")
        f.write(f"- **Relevance Score:** {law_data.get('relevance_score', 0)}\n")
        f.write(f"- **Last Processed:** {datetime.datetime.now().isoformat()}\n")
        f.write(f"- **Is New:** {is_new}\n\n")
        
        # Keywords and matches
        keyword_matches = law_data.get('keyword_matches', [])
        if keyword_matches:
            f.write("### Keywords Found\n")
            for match in keyword_matches:
                f.write(f"- {match}\n")
            f.write("\n")
        
        # AI Summary
        f.write("### AI Summary\n")
        f.write(summary_text.strip() + '\n\n')

        # laws_affected
        f.write("### Laws Affected\n")
        f.write(laws_affected.strip() + '\n\n')

        # DSO Relevance
        f.write("### DSO Relevance\n")
        f.write(DSO_relevance.strip() + '\n\n')

        # Key points (if available)
        key_points = law_data.get('key_points', [])
        if key_points:
            f.write("### Key Points\n")
            for point in key_points:
                f.write(f"- {point}\n")
            f.write("\n")
        
        # Content snippet (first 500 chars)
        content = law_data.get('content', '')
        if content:
            f.write("### Content Preview\n")
            f.write(f"```\n{content[:500]}...\n```\n\n")
        
        f.write("---\n\n")  # Separator between laws

    print(f"✅ Saved comprehensive law data to {filepath}")

# =========================
# Main Pipeline
# =========================
def scrape_and_save_to_markdown(website_key=None):
    """
    Main function: scrape website -> filter by keywords -> AI summarize -> save to markdown
    """
    print("DEBUG: Starting scrape_and_save_to_markdown")
    keywords = load_keywords()
    print(f"DEBUG: Loaded {len(keywords)} keywords")
    config = WEBSITE_CONFIGS.get(website_key or DEFAULT_WEBSITE, WEBSITE_CONFIGS[DEFAULT_WEBSITE])
    website_type = config.get("type", "rss")
    
    logger.info(f"Starting {website_type} scraping for {config.get('url')} with {len(keywords)} keywords")
    print(f"DEBUG: Starting {website_type} scraping for {config.get('url')}")
    
    # Scrape based on website type
    if website_type == "content_page":
        content_items = scrape_content_page(config)
    else:
        content_items = scrape_rss_feed(config)
    
    if not content_items:
        logger.error(f"No content found for {website_type} website")
        return []
    
    relevant_items = []
    for item in content_items:
        try:
            title = item.get("title", "")
            description = item.get("description", "")
            content_text = item.get("content", "")
            
            score, matches = calculate_relevance_score(title, description, content_text, keywords)
            if score >= MIN_RELEVANCE_SCORE:
                item["relevance_score"] = score
                item["keyword_matches"] = matches
                relevant_items.append(item)
        except Exception as e:
            logger.warning(f"Error processing item: {e}")
    
    relevant_items.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    logger.info(f"Found {len(relevant_items)} relevant items")
    
    # Process and save each relevant item
    for item in relevant_items:
        try:
            # Generate AI summary
            summary = AI_call(item.get("content", "")[:10000])
            Law_affected = AI_call(item.get("content", "")[:10000], system_msg="List the specific laws or sections affected, separated by commas.")
            DSO_impt = AI_call(item.get("content", "")[:8000], system_msg="Generate a list of potential impacts on the DSO national laboratories (DSO) Singapore in bullet points. **Assess relevance to DSO National Laboratories**, a defence research and development organization. Specifically: - Highlight any updates related to: - **Manpower or employment laws** - **Finance, procurement, or corporate compliance** - **Defence, military operations, or airspace/security policy** - Clearly **flag any updates that could affect DSO’s operations, compliance obligations, or research environment**")
            # Save to markdown
            save_to_markdown(item, summary, Law_affected, DSO_impt)
            
            logger.info(f"Processed: {item.get('title')} (score: {item.get('relevance_score')})")
            
        except Exception as e:
            logger.error(f"Failed to process item {item.get('title')}: {e}")
    
    return relevant_items

# =========================
# Flask Server Setup
# =========================
app = Flask(__name__, static_folder=".")
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type"]}})
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

def get_latest_markdown_files():
    """Get the latest markdown files from output directory"""
    output_dirs = [d for d in os.listdir('output') if os.path.isdir(os.path.join('output', d))]
    if not output_dirs:
        return []
    
    latest_dir = sorted(output_dirs)[-1]
    markdown_files = []
    
    for file in os.listdir(os.path.join('output', latest_dir)):
        if file.endswith('.md'):
            file_path = os.path.join('output', latest_dir, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            markdown_files.append({
                'filename': file,
                'path': file_path,
                'content': content,
                'date': latest_dir
            })
    
    return markdown_files

@app.route('/')
def serve_index():
    """Serve the main index.html page"""
    return send_from_directory('.', 'index.html')

@app.route('/api/markdown-files')
def get_markdown_files():
    """API endpoint to get all markdown files"""
    try:
        files = get_latest_markdown_files()
        return jsonify({
            'success': True,
            'files': files,
            'count': len(files)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scrape', methods=['POST'])
def scrape_website():
    """API endpoint to trigger scraping for a specific website"""
    try:
        data = request.get_json()
        website_key = data.get('website', DEFAULT_WEBSITE)
        
        results = scrape_and_save_to_markdown(website_key)
        
        return jsonify({
            'success': True,
            'results': len(results),
            'message': f'Scraped {len(results)} relevant laws from {website_key}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scrape-all', methods=['POST'])
def scrape_all_websites():
    """API endpoint to trigger scraping for all websites"""
    try:
        total_results = 0
        all_results = {}
        
        for website_key in WEBSITE_CONFIGS.keys():
            try:
                results = scrape_and_save_to_markdown(website_key)
                all_results[website_key] = len(results)
                total_results += len(results)
                print(f"Scraped {len(results)} laws from {website_key}")
            except Exception as e:
                print(f"Error scraping {website_key}: {e}")
                all_results[website_key] = f"Error: {str(e)}"
        
        return jsonify({
            'success': True,
            'total_results': total_results,
            'results_by_website': all_results,
            'message': f'Scraped {total_results} relevant laws from all websites'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/websites')
def get_websites():
    """API endpoint to get available website configurations"""
    return jsonify({
        'websites': list(WEBSITE_CONFIGS.keys()),
        'categories': WEBSITE_CATEGORIES,
        'default': DEFAULT_WEBSITE
    })

@app.route('/api/category/<category_name>')
def get_category_markdown_files(category_name):
    """API endpoint to get markdown files for a specific category"""
    try:
        # Get websites in the specified category
        websites_in_category = WEBSITE_CATEGORIES.get(category_name, [])
        if not websites_in_category:
            return jsonify({
                'success': False,
                'error': f'Category "{category_name}" not found'
            }), 404
        
        # Get the latest date folder
        output_dirs = [d for d in os.listdir('output') 
                      if os.path.isdir(os.path.join('output', d)) 
                      and re.match(r'\d{4}-\d{2}-\d{2}', d)]
        
        if not output_dirs:
            return jsonify({
                'success': False,
                'error': 'No output directories found'
            }), 404
        
        latest_dir = sorted(output_dirs)[-1]
        category_files = []
        
        # Map website keys to their corresponding markdown filenames
        website_to_filename_map = {
            "sso_agc": "sso_agc_gov_sg.md",
            "iras_cit": "www_iras_gov_sg.md", 
            "acra_main": "www_acra_gov_sg.md",
            "acra_frs": "acra_frs.md",
            "singstat": "www_singstat_gov_sg.md",
            "mom_employment": "www_mom_gov_sg.md",
            "mom_wic": "mom_wic.md",
            "profamily_leave": "profamily_leave.md",
            "cpf": "www_cpf_gov_sg.md",
            "mom_retirement": "mom_retirement.md",
            "mom_reemployment": "mom_reemployment.md",
            "caas_air_nav": "www_caas_gov_sg.md",
            "caas_air_nav_order": "caas_air_nav_order.md",
            "ecfr_part_21": "www_ecfr_gov.md",
            "ecfr_part_23": "www_ecfr_gov.md",
            "ecfr_part_25": "www_ecfr_gov.md",
            "ecfr_part_29": "www_ecfr_gov.md",
            "ecfr_part_31": "www_ecfr_gov.md",
            "ecfr_part_39": "www_ecfr_gov.md",
            "ecfr_part_91": "www_ecfr_gov.md",
            "mtcr_annex": "mtcr_annex.md",
            "imda_spectrum": "imda_spectrum.md",
            "imda_telecom": "imda_telecom.md",
            "nas_gov_records": "nas_gov_records.md",
            "nas_gov_pdf": "nas_gov_pdf.md",
            "nparks_animals": "nparks_animals.md",
            "nparks_naclar": "nparks_naclar.md",
            "nparks_animals_page2": "nparks_animals_page2.md",
            "moh_biosafety": "moh_biosafety.md",
            "opcw_cwc": "opcw_cwc.md",
            "gmac_news": "www_gmac_sg.md",
            "moh_medical_acts": "moh_medical_acts.md",
            "hsa_poisons": "hsa_poisons.md",
            "hsa_controlled_drugs": "hsa_controlled_drugs.md",
            "moh_hcsa": "moh_hcsa.md",
            "mom_wsh": "mom_wsh.md"
        }
        
        # Get markdown files for each website in the category
        for website_key in websites_in_category:
            filename = website_to_filename_map.get(website_key)
            if filename:
                file_path = os.path.join('output', latest_dir, filename)
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    category_files.append({
                        'filename': filename,
                        'website_key': website_key,
                        'content': content,
                        'date': latest_dir
                    })
        
        return jsonify({
            'success': True,
            'category': category_name,
            'files': category_files,
            'date': latest_dir,
            'count': len(category_files)
        })
        
    except Exception as e:
        logger.error(f"Error getting category files: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('.', path)

if __name__ == "__main__":
    print("Starting Flask server on http://localhost:5000")
    print("Available endpoints:")
    print("  GET  /api/markdown-files  - Get all markdown files")
    print("  POST /api/scrape          - Trigger scraping")
    print("  GET  /api/websites        - Get available websites")
    app.run(host='0.0.0.0', port=5000, debug=True)
