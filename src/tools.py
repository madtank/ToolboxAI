import requests
import json
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import feedparser
from src.memory_manager import MemoryManager
import logging
import json
import logging
import boto3
from src.finance_manager import (
    get_stock_price,
    calculate_roi,
    market_sentiment_analysis,
    check_platform_status,
    simulate_trade,
    explain_financial_term,
    compare_financial_apps
)
from .python_repl import execute_python_code
import subprocess

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

def get_crypto_price(symbol):
    """Get current price of a cryptocurrency."""
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get(symbol, {}).get('usd')
    else:
        return None

def execute_shell_command(command: str) -> str:
    """Execute a shell command and return the input command and output."""
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        output = result.stdout
    except subprocess.CalledProcessError as e:
        output = f"Error executing command: {e}\nStderr: {e.stderr}"
    
    return json.dumps({
        "command": command,
        "output": output
    })

import boto3

DEFAULT_SESSION_ID = "CogniscentAI-Main-Session"
DEFAULT_REGION = "us-west-2"  # You can change this to your preferred default region

def consult_agent(input_text, session_id=None, region=None):
    if not region:
        region = DEFAULT_REGION
    
    bedrock = boto3.client('bedrock-agent-runtime', region_name=region)
    
    if not session_id:
        session_id = DEFAULT_SESSION_ID
    
    try:
        response = bedrock.invoke_agent(
            agentAliasId='HBC1BIIRQG',
            agentId='NG7BOZJ9TN',
            sessionId=session_id,
            inputText=input_text
        )
        
        event_stream = response['completion']
        full_response = ""
        for event in event_stream:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    full_response += chunk['bytes'].decode('utf-8')
        
        return {"response": full_response, "session_id": session_id}
    except Exception as e:
        raise Exception(f"Error in consult_agent: {str(e)}")

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
        elif tool_name == "get_crypto_price":
            result = get_crypto_price(tool_input["symbol"])
        elif tool_name == "get_stock_price":
            result = get_stock_price(tool_input["ticker"])
        elif tool_name == "calculate_roi":
            result = calculate_roi(tool_input["initial_investment"], tool_input["final_value"])
        elif tool_name == "market_sentiment_analysis":
            result = market_sentiment_analysis(tool_input["keyword"])
        elif tool_name == "check_platform_status":
            result = check_platform_status(tool_input["platform_name"])
        elif tool_name == "simulate_trade":
            result = simulate_trade(tool_input["platform"], tool_input["asset"], tool_input["amount"], tool_input["action"])
        elif tool_name == "explain_financial_term":
            result = explain_financial_term(tool_input["term"])
        elif tool_name == "compare_financial_apps":
            result = compare_financial_apps(tool_input["app1"], tool_input["app2"], tool_input["feature"])
        elif tool_name == "execute_python_code":
            result = execute_python_code(tool_input["code"])
        elif tool_name == "execute_shell_command":
            result = execute_shell_command(tool_input["command"])
        elif tool_name == "consult_agent":
            result = consult_agent(tool_input["input_text"], tool_input.get("session_id"))
        elif hasattr(memory_manager, tool_name):
            result = getattr(memory_manager, tool_name)(**tool_input)
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
        return json.dumps({"result": result})
    except Exception as e:
        return json.dumps({"error": f"Error in {tool_name}: {str(e)}"})

# Define all available tools
ALL_TOOLS = {
    'get_user_profile': {
        'name': 'get_user_profile',
        'description': 'Retrieve basic user info (name, age, location, interests). Use at the start of conversations or when context is needed.',
        'inputSchema': {'json': {'type': 'object', 'properties': {}}}
    },
    'update_user_profile': {
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
    },
    'save_memory': {
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
    },
    'recall_memories': {
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
    },
    'search': {
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
    },
    'webscrape': {
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
    },
    'rss_feed': {
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
    },
    'get_crypto_price': {
        'name': 'get_crypto_price',
        'description': 'Get the current price of a cryptocurrency in USD. Use for real-time crypto price information.',
        'inputSchema': {
            'json': {
                'type': 'object',
                'properties': {
                    'symbol': {'type': 'string', 'description': 'Cryptocurrency symbol (e.g., bitcoin, ethereum)'}
                },
                'required': ['symbol']
            }
        }
    },
    'get_stock_price': {
        'name': 'get_stock_price',
        'description': 'Get the current price of a stock in USD. Use for real-time stock price information.',
        'inputSchema': {
            'json': {
                'type': 'object',
                'properties': {
                    'ticker': {'type': 'string', 'description': 'Stock ticker symbol (e.g., AAPL, GOOGL)'}
                },
                'required': ['ticker']
            }
        }
    },
    'calculate_roi': {
        'name': 'calculate_roi',
        'description': 'Calculate the Return on Investment (ROI). Use for determining ROI based on initial and final values.',
        'inputSchema': {
            'json': {
                'type': 'object',
                'properties': {
                    'initial_investment': {'type': 'number', 'description': 'Initial investment amount'},
                    'final_value': {'type': 'number', 'description': 'Final value after investment period'}
                },
                'required': ['initial_investment', 'final_value']
            }
        }
    },
    'market_sentiment_analysis': {
        'name': 'market_sentiment_analysis',
        'description': 'Perform sentiment analysis on a given market keyword. Use for understanding market mood and sentiment.',
        'inputSchema': {
            'json': {
                'type': 'object',
                'properties': {
                    'keyword': {'type': 'string', 'description': 'Market keyword for sentiment analysis'}
                },
                'required': ['keyword']
            }
        }
    },
    'check_platform_status': {
        'name': 'check_platform_status',
        'description': 'Check the operational status of a financial platform. Use for verifying platform availability.',
        'inputSchema': {
            'json': {
                'type': 'object',
                'properties': {
                    'platform_name': {'type': 'string', 'description': 'Name of the financial platform'}
                },
                'required': ['platform_name']
            }
        }
    },
    'simulate_trade': {
        'name': 'simulate_trade',
        'description': 'Simulate a trade on a financial platform without executing it. Use for estimating trade costs and execution time.',
        'inputSchema': {
            'json': {
                'type': 'object',
                'properties': {
                    'platform': {'type': 'string', 'description': 'Name of the trading platform'},
                    'asset': {'type': 'string', 'description': 'Asset to trade (e.g., AAPL, BTC)'},
                    'amount': {'type': 'number', 'description': 'Amount to trade'},
                    'action': {'type': 'string', 'enum': ['buy', 'sell'], 'description': 'Buy or sell'}
                },
                'required': ['platform', 'asset', 'amount', 'action']
            }
        }
    },
    'explain_financial_term': {
        'name': 'explain_financial_term',
        'description': 'Provide a clear explanation of a financial term. Use for understanding financial jargon.',
        'inputSchema': {
            'json': {
                'type': 'object',
                'properties': {
                    'term': {'type': 'string', 'description': 'Financial term to explain'}
                },
                'required': ['term']
            }
        }
    },
    'compare_financial_apps': {
        'name': 'compare_financial_apps',
        'description': 'Compare two financial apps based on a specific feature. Use for choosing the best financial app.',
        'inputSchema': {
            'json': {
                'type': 'object',
                'properties': {
                    'app1': {'type': 'string', 'description': 'First app to compare'},
                    'app2': {'type': 'string', 'description': 'Second app to compare'},
                    'feature': {'type': 'string', 'description': 'Feature to compare'}
                },
                'required': ['app1', 'app2', 'feature']
            }
        }
    },
    'execute_python_code': {
        'name': 'execute_python_code',
        'description': 'Execute Python code and return the result, output, and any errors.',
        'inputSchema': {
            'json': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'string', 'description': 'Python code to execute'}
                },
                'required': ['code']
            }
        }
    },
    'execute_shell_command': {
        'name': 'execute_shell_command',
        'description': 'Execute a shell command in the Docker environment. Returns both the input command and its output.',
        'inputSchema': {
            'json': {
                'type': 'object',
                'properties': {
                    'command': {'type': 'string', 'description': 'The shell command to execute'}
                },
                'required': ['command']
            }
        }
    },
    'consult_agent': {
        'name': 'consult_agent',
        'description': 'Consult with an advanced AI agent that has access to a code interpreter and long-term memory. Use for complex tasks or when additional expertise is needed.',
        'inputSchema': {
            'json': {
                'type': 'object',
                'properties': {
                    'input_text': {'type': 'string', 'description': 'The question or task for the AI agent'},
                    'session_id': {'type': 'string', 'description': 'Optional. Use the same session_id for related queries to maintain context'}
                },
                'required': ['input_text']
            }
        }
    }
}

def get_dynamic_tool_config(selected_tools):
    """
    Generate a dynamic toolConfig based on the selected tools for the current persona.
    """
    return {
        'tools': [
            {'toolSpec': ALL_TOOLS[tool]} for tool in selected_tools if tool in ALL_TOOLS
        ],
        'toolChoice': {'auto': {}}
    }
