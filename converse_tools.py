import boto3
import json
import streamlit as st
from datetime import date
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
from botocore.exceptions import ClientError

def create_bedrock_client():
    return boto3.client(service_name='bedrock-runtime', region_name='us-east-1')

def get_stream(bedrock_client, model_id, messages, system_prompts, inference_config, additional_model_fields, toolConfig):
    response = bedrock_client.converse_stream(
        modelId=model_id,
        messages=messages,
        system=system_prompts,
        inferenceConfig=inference_config,
        additionalModelRequestFields=additional_model_fields,
        toolConfig=toolConfig
    )
    return response.get('stream')

def stream_conversation(stream):
    if stream:
        for event in stream:
            yield event

def handle_chat_input(prompt):
    st.chat_message("user").markdown(prompt)
    st.session_state.history.append({"role": "user", "content": [{"text": prompt}]})
    st.session_state.current_chat.append({"role": "user", "content": [{"text": prompt}]})

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

def process_ai_response(bedrock_client, model_id, messages, system_prompts, inference_config, additional_model_fields, toolConfig):
    while True:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            tool_input_placeholder = st.empty()
            full_response = ""
            full_tool_input = ""
            tool_name = None
            tool_id = None
            is_tool_use = False
            assistant_message = {"role": "assistant", "content": []}

            try:
                stream = get_stream(
                    bedrock_client, 
                    model_id, 
                    messages, 
                    system_prompts, 
                    inference_config, 
                    additional_model_fields,
                    toolConfig
                )
                for event in stream_conversation(stream):
                    if 'contentBlockStart' in event:
                        start = event['contentBlockStart']['start']
                        if 'toolUse' in start:
                            is_tool_use = True
                            tool_use = start['toolUse']
                            tool_id = tool_use['toolUseId']
                            tool_name = tool_use['name']
                            st.markdown(f"Using tool: {tool_name}")

                    elif 'contentBlockDelta' in event:
                        delta = event['contentBlockDelta']['delta']

                        if 'text' in delta and not is_tool_use:
                            full_response = handle_chat_output(delta, message_placeholder, full_response, False)

                        elif 'toolUse' in delta and is_tool_use:
                            full_tool_input = handle_tool_use(delta, tool_input_placeholder, full_tool_input, False)

                    elif 'messageStop' in event:
                        if event['messageStop'].get('stopReason') == 'tool_use':
                            # Add text response and tool use to assistant's message
                            if full_response:
                                assistant_message["content"].append({"text": full_response})
                            assistant_message["content"].append({
                                "toolUse": {
                                    "toolUseId": tool_id,
                                    "name": tool_name,
                                    "input": json.loads(full_tool_input)
                                }
                            })
                            message_placeholder.markdown(full_response)
                            tool_input_placeholder.markdown(full_tool_input)

                            # Process tool use
                            tool_results = process_tool_call(tool_name, json.loads(full_tool_input))
                            st.markdown(f"**Tool Results:** {tool_results}")

                            # Add assistant message and tool result as separate messages
                            messages.append(assistant_message)
                            messages.append({
                                "role": "user",
                                "content": [
                                    {
                                        "toolResult": {
                                            "toolUseId": tool_id,
                                            "content": [
                                                {"text": str(tool_results)}
                                            ]
                                        }
                                    }
                                ]
                            })

                            tool_input_placeholder.empty()
                            is_tool_use = False
                            full_tool_input = ""
                            full_response = ""  # Reset full_response for potential continued assistant response
                            assistant_message = {"role": "assistant", "content": []}  # Reset for potential next response
                        else:
                            # Final message stop
                            if full_response:
                                assistant_message["content"].append({"text": full_response})
                                message_placeholder.markdown(full_response)
                            messages.append(assistant_message)
                            return  # Exit the function when the assistant's turn is complete
                            # New code to handle metadata events
                    elif 'metadata' in event:
                        metadata = event['metadata']
                        if 'usage' in metadata:
                            usage = metadata['usage']
                            inputTokens = usage.get('inputTokens', 0)
                            outputTokens = usage.get('outputTokens', 0)
                            totalTokens = usage.get('totalTokens', 0)
                            
                            # Display the usage information in the sidebar
                            st.sidebar.markdown(f"**Usage Information:**\n- Input Tokens: {inputTokens}\n- Output Tokens: {outputTokens}\n- Total Tokens: {totalTokens}")

            except ClientError as err:
                message = err.response['Error']['Message']
                st.error(f"A client error occurred: {message}")

def handle_chat_output(delta, message_placeholder, full_response, is_final=True):
    text_chunk = delta['text']
    full_response += text_chunk
    if is_final:
        message_placeholder.markdown(full_response)
    else:
        message_placeholder.markdown(full_response + "▌")
    return full_response

def handle_tool_use(delta, tool_input_placeholder, full_tool_input, is_final=True):
    if 'input' in delta['toolUse']:
        text_chunk = delta['toolUse']['input']
        full_tool_input += text_chunk
        if is_final:
            tool_input_placeholder.markdown(full_tool_input)
        else:
            tool_input_placeholder.markdown(full_tool_input + "▌")
    return full_tool_input

def process_tool_call(tool_name, tool_input):
    if tool_name == "search":
        return search_duckduckgo(tool_input["query"])
    elif tool_name == "webscrape":
        return scrape_webpage(tool_input["url"])

def process_tool_use(tool_name, full_tool_input, tool_id):
    full_tool_input_dict = json.loads(full_tool_input)
    tool_result = process_tool_call(tool_name, full_tool_input_dict)
    tool_result_message = {
        "role": "assistant",
        "content": [
            {
                "toolResult": {
                    "toolUseId": tool_id,
                    "content": [
                        {"text": str(tool_result)}
                    ]
                }
            }
        ]
    }
    return tool_result, tool_result_message

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
        }
    ],
    'toolChoice': {
        'auto': {}
    }
}

def new_chat() -> None:
    """
    Reset the chat session and initialize a new conversation chain.
    """
    st.session_state["messages"] = []
    st.session_state["history"] = []
    st.session_state["current_chat"] = []

def main():
    st.title("Amazon Bedrock Chatbot with Streaming")

    system_prompt = f"""
    Answer as many questions as you can using your existing knowledge.
    Only search the web for queries that you can not confidently answer.
    Today's date is {date.today().strftime("%B %d %Y")}
    If you think a user's question involves something in the future that hasn't happened yet, use the search tool.
    """
    # Add a button to start a new chat
    st.sidebar.button("New Chat", on_click=new_chat, type="primary")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "history" not in st.session_state:
        st.session_state.history = []
    if "current_chat" not in st.session_state:
        st.session_state.current_chat = []

    bedrock_client = create_bedrock_client()
    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    system_prompts = [{"text": system_prompt}]
    inference_config = {"temperature": 0.1}
    additional_model_fields = {"top_k": 200}

    # Display all messages from current_chat
    for message in st.session_state.current_chat:
        with st.chat_message(message["role"]):
            if 'text' in message["content"][0]:
                st.markdown(message["content"][0]["text"])
            elif 'toolResult' in message["content"][0]:
                tool_result = message["content"][0]["toolResult"]
                st.markdown(f"Tool result: {tool_result}")
    # Clear current_chat after displaying messages
    st.session_state.current_chat = []

    if prompt := st.chat_input("Ask me anything!"):
        handle_chat_input(prompt)
        process_ai_response(bedrock_client, model_id, st.session_state.history, system_prompts, inference_config, additional_model_fields, toolConfig)

if __name__ == "__main__":
    main()
