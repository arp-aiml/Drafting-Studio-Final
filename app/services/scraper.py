import requests
from bs4 import BeautifulSoup
from googlesearch import search

def scrape_legal_context(query: str, template_type: str):
    print(f"🕵️ Searching Trusted Sources for: {query}")
    
    # 1. STRICT WHITELIST (No 'site:' prefix, just domain substrings)
    trusted_domains = [
        "incometaxindia.gov.in", 
        "cbic.gov.in",           
        "mca.gov.in",            
        "rbi.org.in",            
        "indiankanoon.org",      
        "ibbi.gov.in"            
    ]
    
    # 2. SEARCH (Widen scope to top 10 results)
    # We remove the complex 'site:OR' filter from the query string to avoid Google blocking.
    # Instead, we search normally and filter the results manually below.
    safe_query = f"{query} Indian Law judgment section"

    try:
        # Increase results to 10 to find a good link
        search_results = list(search(safe_query, num_results=10, advanced=True))
        
        if search_results:
            for result in search_results:
                # 3. FILTER MANUALLY
                # Check if the URL contains any of our trusted domains
                if not any(domain in result.url for domain in trusted_domains):
                    continue # Skip blogs, news, linkedin, etc.

                # 4. SCRAPE
                try:
                    headers = {'User-Agent': 'Mozilla/5.0'}
                    page = requests.get(result.url, headers=headers, timeout=5)
                    soup = BeautifulSoup(page.content, 'html.parser')
                    
                    paragraphs = soup.find_all('p')
                    # Clean up: take substantial paragraphs only
                    content = " ".join([p.get_text().strip() for p in paragraphs[:6] if len(p.get_text()) > 60])
                    
                    if content:
                        return f"VERIFIED_SOURCE|{result.title}|{result.url}|{content[:1000]}..."
                except:
                    continue # If this link fails to load, try the next one in the list

    except Exception as e:
        print(f"Scrape Warning: {e}")

    # 5. FALLBACK
    return "STATUTORY_FALLBACK"