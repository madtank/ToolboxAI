import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import feedparser
from src.memory_manager import MemoryManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

memory_manager = MemoryManager()

def search_duckduckgo(query, region='wt-wt', safesearch='off', max_results=5):
    """Search DuckDuckGo (ddg) for the given query and return the results. This is for websearch, we need this for current information."""
    ddg = DDGS()
    results = ddg.text(keywords=query, region=region, safesearch=safesearch, max_results=max_results)
    return results

def scrape_webpage(url):
    """Scrape a webpage and return its content as text."""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    text = soup.get_text(separator='\n', strip=True)
    return text

RSS_FEEDS = {
    "AI news": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "Finance news": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "US News": "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
    "World News": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"
}

def fetch_rss_feed(url, num_entries=5):
    """
    Fetch and parse an RSS feed, returning the specified number of latest entries.

    Args:
    url (str): The URL of the RSS feed to fetch or a key from the RSS_FEEDS dictionary.
    num_entries (int, optional): The number of entries to return. Default is 5.

    Returns:
    list: A list of dictionaries containing the latest entries from the feed.
    None: If there was an error fetching or parsing the feed.
    """
    try:
        # Check if the url is a key in our RSS_FEEDS dictionary
        if url in RSS_FEEDS:
            url = RSS_FEEDS[url]

        logger.info(f"Fetching RSS feed from: {url}")
        feed = feedparser.parse(url)

        if feed.bozo:
            logger.error(f"Error parsing RSS feed: {feed.bozo_exception}")
            return None

        entries = []
        for entry in feed.entries[:num_entries]:
            entries.append({
                'title': entry.get('title', 'No title'),
                'link': entry.get('link', '#'),
                'published': entry.get('published', 'No publication date'),
                'summary': entry.get('summary', 'No summary available.')
            })

        logger.info(f"Successfully fetched {len(entries)} entries from the RSS feed.")
        return entries

    except Exception as e:
        logger.error(f"Error fetching RSS feed: {str(e)}")
        return None

def process_tool_call(tool_name, tool_input):
    if tool_name == "search":
        return search_duckduckgo(tool_input["query"])
    elif tool_name == "webscrape":
        return scrape_webpage(tool_input["url"])
    elif tool_name == "rss_feed":
        return fetch_rss_feed(tool_input["url"], tool_input.get("num_entries", 5))
    elif tool_name == "save_memory":
        return memory_manager.save_memory(tool_input["text"])
    elif tool_name == "recall_memories":
        return memory_manager.recall_memories(tool_input["query"])
    elif tool_name == "get_user_profile":
        return memory_manager.get_user_profile(tool_input["info_type"])

toolConfig = {
    'tools': [
        {
            'toolSpec': {
                'name': 'search',
                'description': 'This tool allows you to search the web using DuckDuckGo. You can use it to find information, articles, websites, and more. Simply provide a query, and the tool will return a list of search results.',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {
                            'query': {
                                'type': 'string',
                                'description': 'The search query. This can be any string of text that you want to search for.'
                            }
                        },
                        'required': ['query']
                    }
                }
            }
        },
        {
            'toolSpec': {
                'name': 'webscrape',
                'description': 'This tool allows you to scrape the content of a webpage. You can use it to extract the text from a webpage, which can then be used as context for further actions. Simply provide a URL, and the tool will return the text content of the webpage.',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {
                            'url': {
                                'type': 'string',
                                'description': 'The URL of the webpage to scrape. This should be a fully qualified URL, including the http:// or https:// prefix.'
                            }
                        },
                        'required': ['url']
                    }
                }
            }
        },
        {
            'toolSpec': {
                'name': 'rss_feed',
                'description': 'This tool fetches and parses RSS feeds, returning the latest entries. It can be used to get recent news or updates from various sources including AI news, Finance news, US News, and World News.',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {
                            'url': {
                                'type': 'string',
                                'description': 'The URL of the RSS feed to fetch or one of the following keys: "AI news", "Finance news", "US News", "World News".'
                            },
                            'num_entries': {
                                'type': 'integer',
                                'description': 'The number of entries to return. Default is 5.',
                                'default': 5
                            }
                        },
                        'required': ['url']
                    }
                }
            }
        },
        {
            'toolSpec': {
                'name': 'save_memory',
                'description': 'Save an important piece of information for later recall. Use this when you encounter information that might be useful in future conversations.',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {
                            'text': {
                                'type': 'string',
                                'description': 'The text to save as a memory.'
                            }
                        },
                        'required': ['text']
                    }
                }
            }
        },
        {
            'toolSpec': {
                'name': 'recall_memories',
                'description': 'Recall relevant memories based on a query. Use this at the start of conversations or when you need to retrieve previously saved information.',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {
                            'query': {
                                'type': 'string',
                                'description': 'The query to search for in the saved memories.'
                            }
                        },
                        'required': ['query']
                    }
                }
            }
        },
        {
            'toolSpec': {
                'name': 'get_user_profile',
                'description': 'Retrieve specific user profile information. Use this at the start of conversations or when you need particular details about the user.',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {
                            'info_type': {
                                'type': 'string',
                                'description': 'The type of information to retrieve. Can be "preferences", "hobbies", "personal_details", or "all" for a complete profile.'
                            }
                        },
                        'required': ['info_type']
                    }
                }
            }
        }
    ],
    'toolChoice': {
        'auto': {}
    }
}
