import requests
import json
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import feedparser
from src.memory_manager import MemoryManager
import logging
import re
from datetime import datetime

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

def initialize_prompt(new_prompt):
    """Initialize a new prompt for the AI assistant."""
    try:
        # Parse the new_prompt to extract relevant settings
        settings = parse_prompt_settings(new_prompt)
        
        # Update the system prompt
        updated_prompt = f"""
        You are ToolboxAI, a personalized AI assistant. Current date/time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        Guidelines:
        1. Use get_user_profile at the start of conversations for context.
        2. Leverage tools to provide accurate, personalized responses.
        3. Save important information shared by users with save_memory.
        4. Use recall_memories to maintain conversation continuity.
        5. Employ search, webscrape, and rss_feed for current information when necessary.
        6. Suggest profile updates or new memories when appropriate.
        7. Balance tool usage with your inherent knowledge for efficient interactions.

        {settings['custom_instructions']}

        Adapt your communication style to each user's preferences and needs.
        """
        
        # Update other settings
        inference_config = {
            "temperature": settings['temperature'],
            "topP": settings['top_p'],
            "maxTokens": settings['max_tokens']
        }
        
        return {
            "system_prompt": updated_prompt,
            "inference_config": inference_config,
            "message": "New prompt and settings initialized successfully."
        }
    except Exception as e:
        return {"error": f"Error initializing new prompt: {str(e)}"}

def parse_prompt_settings(prompt):
    """Parse the natural language prompt to extract settings."""
    # This is a simplified parser. In a real-world scenario, you might want to use
    # more advanced NLP techniques or a dedicated parsing library.
    settings = {
        "custom_instructions": "",
        "temperature": 0.7,
        "top_p": 1.0,
        "max_tokens": 1024
    }
    
    # Extract custom instructions (everything before any specific setting mentions)
    custom_instructions_match = re.match(r"(.*?)(?:Set temperature|Set top p|Set max tokens|$)", prompt, re.DOTALL | re.IGNORECASE)
    if custom_instructions_match:
        settings["custom_instructions"] = custom_instructions_match.group(1).strip()
    
    # Extract temperature
    temp_match = re.search(r"Set temperature to (0\.\d+|\d+)", prompt, re.IGNORECASE)
    if temp_match:
        settings["temperature"] = float(temp_match.group(1))
    
    # Extract top_p
    top_p_match = re.search(r"Set top p to (0\.\d+|\d+)", prompt, re.IGNORECASE)
    if top_p_match:
        settings["top_p"] = float(top_p_match.group(1))
    
    # Extract max_tokens
    max_tokens_match = re.search(r"Set max tokens to (\d+)", prompt, re.IGNORECASE)
    if max_tokens_match:
        settings["max_tokens"] = int(max_tokens_match.group(1))
    
    return settings

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
        elif tool_name == "initialize_prompt":
            result = initialize_prompt(tool_input["new_prompt"])
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
                'name': 'initialize_prompt',
                'description': 'Initialize a new prompt and adjust settings for the AI assistant. Use this to customize the assistant\'s behavior, style, or capabilities. You can set custom instructions and adjust parameters like temperature, top_p, and max_tokens.',
                'inputSchema': {
                    'json': {
                        'type': 'object',
                        'properties': {
                            'new_prompt': {
                                'type': 'string',
                                'description': 'Natural language description of the new prompt and settings. Example: "Be more formal in your responses. Set temperature to 0.8 and max tokens to 2000."'
                            }
                        },
                        'required': ['new_prompt']
                    }
                }
            }
        }
    ],
    'toolChoice': {'auto': {}}
}
