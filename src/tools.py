import requests
import json
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
    logger.info(f"Processing tool call for: {tool_name}")
    logger.debug(f"Tool input: {tool_input}")

    try:
        if tool_name == "search":
            search_results = search_duckduckgo(tool_input["query"])
            return json.dumps({"result": search_results})
        elif tool_name == "webscrape":
            return json.dumps({"result": scrape_webpage(tool_input["url"])})
        elif tool_name == "rss_feed":
            rss_results = fetch_rss_feed(tool_input["url"], tool_input.get("num_entries", 5))
            return json.dumps({"result": rss_results})
        elif tool_name == "save_memory":
            return json.dumps({"result": memory_manager.save_memory(tool_input["text"], tool_input.get("metadata"))})
        elif tool_name == "recall_memories":
            result = memory_manager.recall_memories(tool_input["query"], tool_input.get("k", 3))
            return json.dumps({"result": result})
        elif tool_name == "update_memory":
            return json.dumps({"result": memory_manager.update_memory(tool_input["memory_id"], tool_input["new_text"], tool_input.get("new_metadata"))})
        elif tool_name == "delete_memory":
            return json.dumps({"result": memory_manager.delete_memory(tool_input["memory_id"])})
        elif tool_name == "update_user_profile":
            return json.dumps({"result": memory_manager.update_user_profile(tool_input["profile_data"])})
        elif tool_name == "get_user_profile":
            return json.dumps({"result": memory_manager.get_user_profile()})
        elif tool_name == "list_all_memories":
            return json.dumps({"result": memory_manager.list_all_memories()})
        else:
            logger.warning(f"Unknown tool: {tool_name}")
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
    except Exception as e:
        logger.error(f"Error processing tool call for {tool_name}: {str(e)}")
        return json.dumps({"error": f"Error processing tool call: {str(e)}"})


toolConfig = {
    'tools': [
        {
            'toolSpec': {
                'name': 'search',
                'description': 'Web search using DuckDuckGo. Use for current info, news, or specific facts not in your knowledge base.',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {
                            'query': {
                                'type': 'string',
                                'description': 'Search query: specific questions or keywords.'
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
                'description': 'Extract text from a webpage. Use for detailed info from specific pages. Returns raw text without HTML.',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {
                            'url': {
                                'type': 'string',
                                'description': 'Full URL of webpage to scrape (include http:// or https://)'
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
                'description': '''
                Fetch latest entries from predefined RSS feeds. Available options:
                - "AI news": TechCrunch AI category
                - "Finance news": Dow Jones Markets
                - "US News": New York Times US news
                - "World News": New York Times World news
                Use for current events or recent developments in these areas.
                ''',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {
                            'url': {
                                'type': 'string',
                                'description': 'RSS feed key: "AI news", "Finance news", "US News", or "World News".'
                            },
                            'num_entries': {
                                'type': 'integer',
                                'description': 'Number of entries to return. Default is 5.',
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
                'description': 'Save important user info as a memory. Use for preferences, interests, or significant details shared during conversation.',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {
                            'text': {
                                'type': 'string',
                                'description': 'Specific info to save as a memory.'
                            },
                            'metadata': {
                                'type': 'object',
                                'description': 'Optional metadata for the memory.'
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
                'description': 'Semantic search on stored memories. Retrieves memories similar to the query, not by exact match or ID.',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {
                            'query': {
                                'type': 'string',
                                'description': 'Search query for memories.'
                            },
                            'k': {
                                'type': 'integer',
                                'description': 'Number of memories to retrieve. Default is 3.',
                                'default': 3
                            }
                        },
                        'required': ['query']
                    }
                }
            }
        },
        {
            'toolSpec': {
                'name': 'update_memory',
                'description': 'Update an existing memory. Provide memory ID and new content.',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {
                            'memory_id': {
                                'type': 'string',
                                'description': 'ID of memory to update.'
                            },
                            'new_text': {
                                'type': 'string',
                                'description': 'New content for the memory.'
                            },
                            'new_metadata': {
                                'type': 'object',
                                'description': 'Optional new metadata.'
                            }
                        },
                        'required': ['memory_id', 'new_text']
                    }
                }
            }
        },
        {
            'toolSpec': {
                'name': 'delete_memory',
                'description': 'Delete a specific memory. Use caution: deletion is irreversible.',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {
                            'memory_id': {
                                'type': 'string',
                                'description': 'ID of memory to delete.'
                            }
                        },
                        'required': ['memory_id']
                    }
                }
            }
        },
        {
            'toolSpec': {
                'name': 'list_all_memories',
                'description': 'List all saved memories. Useful for overview or finding memory IDs.',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {},
                        'additionalProperties': False
                    }
                }
            }
        },
        {
            'toolSpec': {
                'name': 'update_user_profile',
                'description': 'Update user profile with new information about preferences, interests, or other key details.',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {
                            'profile_data': {
                                'type': 'string',
                                'description': 'JSON string of user profile data to update.'
                            }
                        },
                        'required': ['profile_data']
                    }
                }
            }
        },
        {
            'toolSpec': {
                'name': 'get_user_profile',
                'description': 'Retrieve the complete user profile as stored in the system.',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {}
                    }
                }
            }
        }
    ],
    'toolChoice': {
        'auto': {}
    }
}