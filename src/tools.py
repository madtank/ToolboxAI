import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import feedparser
from datetime import datetime
from src.memory_manager import MemoryManager

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

def fetch_rss_feed(url, num_entries=5):
    """
    Fetch and parse an RSS feed, returning the specified number of latest entries.

    You have access to an RSS feed tool that can fetch recent AI news from TechCrunch. Use it when asked about recent AI news or developments.
    AI news: https://techcrunch.com/category/artificial-intelligence/feed/
    Finance news: https://feeds.a.dj.com/rss/RSSMarketsMain.xml
    US News: https://rss.nytimes.com/services/xml/rss/nyt/US.xml
    World News: https://rss.nytimes.com/services/xml/rss/nyt/World.xml
    Args:
    url (str): The URL of the RSS feed to fetch.
    num_entries (int, optional): The number of entries to return. Default is 5.
    """
    feed = feedparser.parse(url)
    entries = []
    for entry in feed.entries[:num_entries]:
        entries.append({
            'title': entry.title,
            'link': entry.link,
            'published': entry.published,
            'summary': entry.summary
        })
    return entries

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
                'description': 'This tool fetches and parses an RSS feed, returning the latest entries. It can be used to get recent news or updates from various sources.',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {
                            'url': {
                                'type': 'string',
                                'description': 'The URL of the RSS feed to fetch.'
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
        }
    ],
    'toolChoice': {
        'auto': {}
    }
}
