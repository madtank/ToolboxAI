import boto3
import json
import streamlit as st
from botocore.exceptions import ClientError
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup

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

def stream_conversation(bedrock_client, model_id, messages, system_prompts, inference_config, additional_model_fields, tool_config):
    response = bedrock_client.converse_stream(
        modelId=model_id,
        messages=messages,
        system=system_prompts,
        inferenceConfig=inference_config,
        additionalModelRequestFields=additional_model_fields,
        toolConfig=tool_config
    )

    stream = response.get('stream')
    if stream:
        tool_use_input = ""
        tool_use_event = None
        for event in stream:
            if 'contentBlockDelta' in event and 'delta' in event['contentBlockDelta']:
                if 'text' in event['contentBlockDelta']['delta']:
                    text_chunk = event['contentBlockDelta']['delta']['text']
                    yield {'text_chunk': text_chunk}
                elif 'toolUse' in event['contentBlockDelta']['delta']:
                    tool_use_input += event['contentBlockDelta']['delta']['toolUse']['input']
            elif 'contentBlockStart' in event and 'start' in event['contentBlockStart']:
                if 'toolUse' in event['contentBlockStart']['start']:
                    tool_use_event = event['contentBlockStart']['start']['toolUse']
            elif 'contentBlockStop' in event:
                pass
            elif 'messageStop' in event:
                if tool_use_event:
                    tool_use_event['input'] = json.loads(tool_use_input)
                    yield {
                        'message_stop': {
                            'stopReason': event['messageStop']['stopReason'],
                            'toolUse': tool_use_event
                        }
                    }
                else:
                    yield {'unknown_event': event}

def main():
    st.title("Amazon Bedrock Chatbot with Streaming")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"][0]["text"])

    if prompt := st.chat_input("Ask me anything!"):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": [{"text": prompt}]})

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            model_id = "anthropic.claude-3-haiku-20240307-v1:0"
            system_prompt = """You are an assistant that provides responses based on the user's questions."""
            system_prompts = [{"text": system_prompt}]
            inference_config = {"temperature": 0.5, "maxTokens": 4096}
            additional_model_fields = {"top_k": 200}

            try:
                bedrock_client = boto3.client(service_name='bedrock-runtime', region_name='us-west-2')
                messages = st.session_state.messages

                for event in stream_conversation(bedrock_client, model_id, messages, system_prompts, inference_config, additional_model_fields, toolConfig):
                    if 'text_chunk' in event:
                        text_chunk = event['text_chunk']
                        full_response += text_chunk
                        message_placeholder.markdown(full_response + "▌")

                    if 'message_stop' in event:
                        stop_reason = event['message_stop']['stopReason']

                        if stop_reason == "tool_use":
                            tool_use = event['message_stop']['toolUse']
                            tool_id = tool_use['toolUseId']
                            tool_name = tool_use['name']
                            tool_input = tool_use['input']

                            st.write(f"Claude wants to use the {tool_name} tool")
                            st.write(f"Tool Input:")
                            st.write(json.dumps(tool_input, indent=2))

                            tool_result = process_tool_call(tool_name, tool_input)

                            st.write(f"\nTool Result:")
                            st.write(json.dumps(tool_result, indent=2))

                            # Append tool result to messages
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": [{"text": full_response}]
                            })

                            if tool_result:  # Check that tool_result is not empty
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

                                # Add tool result to the assistant's response
                                messages.append({
                                    "role": "assistant",
                                    "content": [{"text": str(tool_result)}]
                                })

                            # Continue the conversation after tool use
                            followup_prompt = "Thank you for the tool result. Please continue."
                            st.session_state.messages.append({"role": "user", "content": [{"text": followup_prompt}]})
                            messages.append({"role": "user", "content": [{"text": followup_prompt}]})


                            stream_results = stream_conversation(bedrock_client, model_id, messages, system_prompts, inference_config, additional_model_fields, toolConfig)
                            print(stream_results)  # Add this line to check the return value of stream_conversation
                            for followup_event in stream_results:
                                if 'text_chunk' in followup_event:
                                    followup_text_chunk = followup_event['text_chunk']
                                    full_response += followup_text_chunk
                                    message_placeholder.markdown(full_response + "▌")
                                if 'message_stop' in followup_event:
                                    break

                st.session_state.messages.append({"role": "assistant", "content": [{"text": full_response}]})
                message_placeholder.markdown(full_response)

            except ClientError as err:
                message = err.response['Error']['Message']
                st.error(f"A client error occurred: {message}")

if __name__ == "__main__":
    main()
