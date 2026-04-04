import httpx
import xml.etree.ElementTree as ET
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

logger = logging.getLogger(__name__)

class CurfewService:
    """
    Checks for localized curfews or Section 144 alerts using the free Google News XML RSS feed.
    This provides real-time news data without requiring any API keys.
    """
    
    # Google News RSS base URL (XML format)
    RSS_BASE_URL = "https://news.google.com/rss/search"
    
    def check_curfew(self, city: str = "Bengaluru") -> Dict[str, Any]:
        """
        Queries GNews for curfews or Section 144 in a specific city.
        Returns a dictionary with status and latest news if a match is found.
        """
        # Query: City + (Curfew OR "Section 144" OR "Internet Shutdown")
        query = f'{city} (curfew OR "Section 144" OR "internet shutdown")'
        params = {
            "q": query,
            "hl": "en-IN",
            "gl": "IN",
            "ceid": "IN:en"
        }
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(self.RSS_BASE_URL, params=params)
                response.raise_for_status()
                
                # Parse the XML RSS Feed
                root = ET.fromstring(response.text)
                items = root.findall(".//item")
                
                if not items:
                    return {"curfew_active": False, "news": None, "source": None, "link": None}
                
                # Check for recent news items containing keywords in the title (last 12 hours)
                latest_news = None
                source_name = None
                source_link = None
                is_active = False
                
                for item in items:
                    title = item.find("title").text
                    link = item.find("link").text
                    source_elm = item.find("source")
                    source = source_elm.text if source_elm is not None else "Google News"
                    pub_date_str = item.find("pubDate").text
                    
                    # Convert pubDate to a comparable datetime object (RFC 822)
                    try:
                        pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %Z")
                        if datetime.utcnow() - pub_date < timedelta(hours=12):
                            is_active = True
                            latest_news = title
                            source_name = source
                            source_link = link
                            break
                    except Exception:
                        # Fallback for parsing errors, just check keywords
                        if any(keyword in title.lower() for keyword in ["section 144", "curfew", "shutdown"]):
                            is_active = True
                            latest_news = title
                            source_name = source
                            source_link = link
                            break
                
                return {
                    "curfew_active": is_active,
                    "news": latest_news,
                    "source": source_name,
                    "link": source_link,
                    "city": city
                }
                
        except Exception as e:
            logger.error(f"Failed to fetch curfew data from GNews: {e}")
            return {"curfew_active": False, "news": None}

    def _fallback_check(self) -> Dict[str, Any]:
        """Passive fallback in case of errors."""
        return {"curfew_active": False, "news": None}
