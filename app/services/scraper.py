# scraper.py
import requests
from bs4 import BeautifulSoup
from googlesearch import search
import re

def extract_case_from_text(text: str):
    """
    Extracts case names like:
    X v. Y
    X versus Y
    """
    match = re.search(
        r'([A-Z][A-Za-z\s.&]+)\s+(?:v\.|versus)\s+([A-Z][A-Za-z\s.&]+)',
        text,
        re.IGNORECASE
    )
    if match:
        return f"{match.group(1).strip()} v. {match.group(2).strip()}"
    return None


def scrape_legal_context(query: str, template_type: str):
    # print(f"🕵️ Searching Trusted Sources for: {query}")

    trusted_domains = [
        "indiankanoon.org",
        "incometaxindia.gov.in",
        "cbic.gov.in",
        "mca.gov.in",
        "rbi.org.in",
        "ibbi.gov.in"
    ]

    safe_query = f"{query} Supreme Court High Court judgment India"
    results_list = []

    try:
        results = search(safe_query, num_results=10)

        for url in results:
            if not any(domain in url for domain in trusted_domains):
                continue

            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.get(url, headers=headers, timeout=15)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                case_name = soup.title.string.strip() if soup.title else "Unnamed Case"
                court_name = "Supreme Court / High Court"

                # Grab first 5 paragraphs for content
                paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
                text_content = " ".join(paragraphs[:5]) if paragraphs else case_name

                # Even if short, include the case
                results_list.append({
                    "case_name": case_name,
                    "court": court_name,
                    "legal_principle": "See source",
                    "relevance_to_present_document": f"Relevant to: {query[:100]}"
                })

                if len(results_list) >= 3:
                    break

            except Exception as e:
                print(f"⚠️ Error scraping {url}: {e}")
                continue

    except Exception as e:
        print("Scraper error:", e)

    if not results_list:
        results_list.append({
            "case_name": "No relevant SC/HC case found",
            "court": "—",
            "legal_principle": "See source",
            "relevance_to_present_document": "Judicial precedents must be researched separately."
        })

    # print("📝 Scraper results:", results_list)
    return results_list
