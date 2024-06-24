# bedrock-conversai-toolbox
Welcome to bedrock-conversai-toolbox! This project utilizes Amazon Bedrock’s ConversAI API to build advanced conversational AI tools. Enhance chatbot development with integrated DuckDuckGo web search and an intuitive Streamlit interface. Perfect for developers aiming to create sophisticated AI-driven applications effortlessly.

## Setup and Installation
To get started with the bedrock-conversai-toolbox, follow these steps:

1. **Install Dependencies**: Run `pip install -r requirements.txt` to install the necessary dependencies.
2. **Set Up a Virtual Environment**:
   - Create a virtual environment by running `python -m venv .env`.
   - Activate the virtual environment:
     - On Windows, use `.env\Scripts\activate`.
     - On Unix or MacOS, use `source .env/bin/activate`.
3. **Run `converse_tools.py` with Streamlit**: Execute `streamlit run converse_tools.py` to start the application.

## About `converse_tools.py`
The `converse_tools.py` module is a cornerstone of the bedrock-conversai-toolbox, offering a suite of functions designed to facilitate the development of conversational AI applications using Amazon Bedrock’s ConversAI API. This module enables developers to:

- **Create a Bedrock client**: Establish a connection to Amazon Bedrock’s ConversAI API.
- **Handle chat input**: Process user inputs for the conversational AI.
- **Search DuckDuckGo**: Integrate real-time web search within chatbot conversations.
- **Scrape webpages**: Extract content from webpages to use as context or responses.
- **Process AI responses**: Manage the flow of conversation by processing AI-generated responses.
- **Manage conversational AI streams**: Seamlessly handle the stream of messages in a conversation.

### Integration of DuckDuckGo Web Search
`converse_tools.py` integrates DuckDuckGo web search, allowing chatbots to retrieve current information from the web in real-time, enhancing the user experience by providing accurate and up-to-date responses.

### Conversational AI Stream Management
This module also simplifies the management of conversational AI streams, making it easier for developers to maintain the flow of conversation and ensure that chatbots respond appropriately to user inputs.

### Usage Example
Below is a simple usage example demonstrating how to utilize key functions within `converse_tools.py`:

```python
from converse_tools import create_bedrock_client, handle_chat_input, search_duckduckgo, scrape_webpage, process_ai_response

# Create a Bedrock client
bedrock_client = create_bedrock_client()

# Example of handling chat input
handle_chat_input("Hello, how can I assist you today?")

# Example of searching DuckDuckGo
search_results = search_duckduckgo("Latest news on AI")

# Example of scraping a webpage
webpage_content = scrape_webpage("https://example.com")

# Example of processing an AI response
process_ai_response(bedrock_client, "What is the weather like today?")
```

This example illustrates the ease with which developers can integrate these functions into their projects, leveraging the power of Amazon Bedrock’s ConversAI API to create dynamic and responsive chatbots.
