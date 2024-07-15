import requests
import json
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import feedparser
from src.memory_manager import MemoryManager
import logging
from src.music_tool import process_music_tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

memory_manager = MemoryManager()

def search_duckduckgo(query, region='wt-wt', safesearch='off', max_results=5):
    """DuckDuckGo web search."""
    return list(DDGS().text(keywords=query, region=region, safesearch=safesearch, max_results=max_results))

def scrape_webpage(url):
    """Extract text from webpage."""
    return BeautifulSoup(requests.get(url).text, 'html.parser').get_text(separator='\n', strip=True)

def fetch_rss_feed(url, num_entries=5):
    """Fetch RSS feed entries."""
    try:
        feed = feedparser.parse(url)
        return [
            {
                'title': entry.get('title', 'No title'),
                'link': entry.get('link', '#'),
                'published': entry.get('published', 'No date'),
                'summary': entry.get('summary', 'No summary')
            }
            for entry in feed.entries[:num_entries]
        ]
    except Exception as e:
        logger.error(f"RSS feed error: {str(e)}")
        return None

def process_tool_call(tool_name, tool_input):
    """Process tool calls."""
    logger.info(f"Tool call: {tool_name}")
    try:
        if tool_name == "search":
            result = search_duckduckgo(tool_input["query"])
        elif tool_name == "webscrape":
            result = scrape_webpage(tool_input["url"])
        elif tool_name == "rss_feed":
            result = fetch_rss_feed(tool_input["url"], tool_input.get("num_entries", 5))
        elif tool_name == "music_player":
            result = process_music_tool(tool_input)
        elif hasattr(memory_manager, tool_name):
            result = getattr(memory_manager, tool_name)(**tool_input)
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
        return json.dumps({"result": result})
    except Exception as e:
        return json.dumps({"error": f"Error in {tool_name}: {str(e)}"})

toolConfig = {
    'tools': [
        {
            'toolSpec': {
                'name': 'get_user_profile',
                'description': 'Retrieve basic user info (name, age, location, interests). Use at the start of conversations or when context is needed.',
                'inputSchema': {'json': {'type': 'object', 'properties': {}}}
            }
        },
        {
            'toolSpec': {
                'name': 'update_user_profile',
                'description': 'Update basic user info. Use when profile is incomplete or needs updating.',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {
                            'profile_data': {'type': 'string', 'description': 'JSON string of profile data to update'}
                        },
                        'required': ['profile_data']
                    }
                }
            }
        },
        {
            'toolSpec': {
                'name': 'save_memory',
                'description': 'Save user preferences, experiences, or detailed info. Use for specifics not suitable for basic profile.',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {
                            'text': {'type': 'string', 'description': 'Content to save'},
                            'metadata': {'type': 'object', 'description': 'Optional categorization metadata'}
                        },
                        'required': ['text']
                    }
                }
            }
        },
        {
            'toolSpec': {
                'name': 'recall_memories',
                'description': 'Search stored memories by similarity. Use to retrieve relevant past information.',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {
                            'query': {'type': 'string', 'description': 'Search query'},
                            'k': {'type': 'integer', 'description': 'Number of results', 'default': 3}
                        },
                        'required': ['query']
                    }
                }
            }
        },
        {
            'toolSpec': {
                'name': 'search',
                'description': 'Web search for current info, news, or facts. Use for up-to-date or factual information.',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {
                            'query': {'type': 'string', 'description': 'Search query'}
                        },
                        'required': ['query']
                    }
                }
            }
        },
        {
            'toolSpec': {
                'name': 'webscrape',
                'description': 'Extract text from a webpage. Use for detailed info from specific online sources.',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {
                            'url': {'type': 'string', 'description': 'Webpage URL to scrape'}
                        },
                        'required': ['url']
                    }
                }
            }
        },
        {
            'toolSpec': {
                'name': 'rss_feed',
                'description': 'Fetch latest entries from RSS feeds. Use for recent news or updates. Refer to saved feed URLs in memories.',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {
                            'url': {'type': 'string', 'description': 'RSS feed URL'},
                            'num_entries': {'type': 'integer', 'description': 'Number of entries', 'default': 5}
                        },
                        'required': ['url']
                    }
                }
            }
        },
        {
            'toolSpec': {
                'name': 'music_player',
                'description': 'Generate and play musical elements including melodies, chord progressions, and rhythms.',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {
                            'key': {
                                'type': 'string',
                                'enum': ['C', 'G', 'F'],
                                'description': 'The musical key'
                            },
                            'style': {
                                'type': 'string',
                                'enum': ['pop', 'blues', 'jazz'],
                                'description': 'The musical style'
                            },
                            'length': {
                                'type': 'integer',
                                'description': 'The number of notes or chords to generate'
                            }
                        }
                    }
                }
            }
        }
    ],
    'toolChoice': {'auto': {}}
}
