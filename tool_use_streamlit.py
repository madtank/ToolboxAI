import boto3
import json
import streamlit as st
from datetime import date
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
from botocore.exceptions import ClientError

def create_bedrock_client():
    return boto3.client(service_name='bedrock-runtime', region_name='us-west-2')

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

def handle_chat_output(event, message_placeholder, full_response):
    if 'contentBlockDelta' in event:
        delta = event['contentBlockDelta']['delta']
        if 'text' in delta:
            text_chunk = delta['text']
            full_response += text_chunk
            message_placeholder.markdown(full_response + "▌")
    elif 'contentBlockStart' in event:
        start = event['contentBlockStart']['start']
        if 'toolUseId' in start and 'name' in start:
            tool_id = start['toolUseId']
            tool_name = start['name']
            # Handle the tool use start event here
    return full_response

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

def process_tool_call(tool_name, tool_input):
    if tool_name == "search":
        return search_duckduckgo(tool_input["query"])
    elif tool_name == "webscrape":
        return scrape_webpage(tool_input["url"])

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

def main():

    st.title("Amazon Bedrock Chatbot with Streaming")

    system_prompt = f"""
    Answer as many questions as you can using your existing knowledge.
    Only search the web for queries that you can not confidently answer.
    Today's date is {date.today().strftime("%B %d %Y")}
    If you think a user's question involves something in the future that hasn't happened yet, use the search tool.
    """
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if 'text' in message["content"][0]:
                st.markdown(message["content"][0]["text"])
            elif 'toolResult' in message["content"][0]:
                tool_result = message["content"][0]["toolResult"]
                st.markdown(f"Tool result: {tool_result}")

    if prompt := st.chat_input("Ask me anything!"):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": [{"text": prompt}]})

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            model_id = "anthropic.claude-3-haiku-20240307-v1:0"
            system_prompt = """You are an assistant that provides responses based on the user's questions."""
            system_prompts = [{"text": system_prompt}]
            inference_config = {"temperature": 0.1}
            additional_model_fields = {"top_k": 200}

            try:
                bedrock_client = create_bedrock_client()
                stream = get_stream(
                    bedrock_client,
                    model_id,
                    st.session_state.messages,
                    system_prompts,
                    inference_config,
                    additional_model_fields,
                    toolConfig
                )
                for event in stream_conversation(stream):
                    full_response = handle_chat_output(event, message_placeholder, full_response)
                    if 'messageStop' in event:
                        stop_reason = event['messageStop']['stopReason']

                        if stop_reason == "tool_use":
                            tool_use = event['messageStop']['toolUse']
                            tool_id = tool_use['toolUseId']
                            tool_name = tool_use['name']
                            tool_input = tool_use['input']

                            st.write(f"Claude wants to use the {tool_name} tool")
                            st.write(f"Tool Input:")
                            st.json(tool_input)

                            tool_result = process_tool_call(tool_name, tool_input)

                            st.write(f"\nTool Result:")
                            st.json(tool_result)

                            st.session_state.messages.append({
                                "role": "user",
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
                            })

                            # Start a new stream after processing the tool use event
                            stream = get_stream(
                                bedrock_client,
                                model_id,
                                st.session_state.messages,
                                system_prompts,
                                inference_config,
                                additional_model_fields,
                                toolConfig
                            )
                            for event in stream_conversation(stream):
                                full_response = handle_chat_output(event, message_placeholder, full_response)
                st.session_state.messages.append({"role": "assistant", "content": [{"text": full_response}]})
                message_placeholder.markdown(full_response)

            except ClientError as err:
                message = err.response['Error']['Message']
                st.error(f"A client error occurred: {message}")
if __name__ == "__main__":
    main()