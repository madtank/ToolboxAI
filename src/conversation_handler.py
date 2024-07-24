import streamlit as st
import json
from botocore.exceptions import ClientError
from src.bedrock_client import get_stream, stream_conversation
from src.utils import handle_chat_output, handle_tool_use, format_memory_results
from src.tools import process_tool_call
import os
import base64
import logging
import re

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def handle_chat_input(prompt, file_content=None, file_name=None):
    logger.debug(f"Handling chat input: {prompt}, file: {file_name}")
    
    user_message = {"role": "user", "content": [{"text": prompt}]}
    display_message = {"role": "user", "content": prompt}
    
    if file_content and file_name:
        name, ext = os.path.splitext(file_name)
        file_format = ext.lstrip('.').lower()
        
        if file_format in ["png", "jpg", "jpeg", "webp"]:
            user_message["content"].append({
                "image": {
                    "format": file_format,
                    "source": {
                        "bytes": file_content
                    }
                }
            })
            file_b64 = base64.b64encode(file_content).decode()
            display_message["image"] = f"data:image/{file_format};base64,{file_b64}"
            logger.debug(f"Processed image file: {file_name}")
        else:
            document_formats = ["pdf", "csv", "doc", "docx", "xls", "xlsx", "html", "txt", "md"]
            if file_format not in document_formats:
                file_format = "txt"
            
            user_message["content"].append({
                "document": {
                    "name": name,
                    "format": file_format,
                    "source": {
                        "bytes": file_content
                    }
                }
            })
            display_message["document"] = name
            logger.debug(f"Processed document file: {file_name}")
        
        display_message["file_type"] = file_format
        display_message["file_name"] = file_name
    
    st.session_state.history.append(user_message)
    st.session_state.display_messages.append(display_message)
    logger.debug("Appended user message to session state")

def process_ai_response(bedrock_client, model_id, messages, system_prompts, inference_config, additional_model_fields, dynamic_tool_config):
    logger.debug("Starting AI response processing")
    turn_token_usage = {'inputTokens': 0, 'outputTokens': 0, 'totalTokens': 0}
    
    while True:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            tool_input_placeholder = st.empty()
            full_response = ""
            thinking_content = ""
            answer_content = ""
            clean_answer = ""
            is_thinking = False
            is_answering = False
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
                    dynamic_tool_config
                )
                for event in stream_conversation(stream):
                    logger.debug(f"Received event: {event}")

                    if 'contentBlockStart' in event:
                        start = event['contentBlockStart']['start']
                        if 'toolUse' in start:
                            is_tool_use = True
                            tool_use = start['toolUse']
                            tool_id = tool_use['toolUseId']
                            tool_name = tool_use['name']
                            # # This is where the output is changing the display messages
                            # st.markdown(f"Using tool: {tool_name}")
                            logger.debug(f"Tool use started: {tool_name}")

                    if 'contentBlockDelta' in event:
                        delta = event['contentBlockDelta']['delta']
                        
                        if 'text' in delta and not is_tool_use:
                            text_chunk = delta['text']
                            full_response += text_chunk
                            
                            if '<thinking' in text_chunk:
                                is_thinking = True
                                is_answering = False
                            elif '<answer' in text_chunk:
                                is_thinking = False
                                is_answering = True
                                answer_content = ""
                            elif '</answer' in text_chunk:
                                is_answering = False
                            else:
                                if text_chunk != ">":
                                    is_answering = True
                            
                            if is_thinking:
                                thinking_content += text_chunk
                            elif is_answering:
                                answer_content += text_chunk
                                
                                clean_answer = re.sub(r'<answer>|</answer>', '', answer_content).strip()
                                message_placeholder.markdown(clean_answer)
                                logger.debug(f"Assistant response: {clean_answer}")
    
                        elif 'toolUse' in delta and is_tool_use:
                            full_tool_input = handle_tool_use(delta, tool_input_placeholder, full_tool_input, False)
                            logger.debug(f"Tool input: {full_tool_input}")

                    elif 'messageStop' in event:
                        if event['messageStop'].get('stopReason') == 'tool_use':
                            if clean_answer:
                                assistant_message["content"].append({"text": clean_answer})
                                update_display_messages("assistant", clean_answer)
                                logger.debug(f"Assistant message appended: {clean_answer}")
                            
                            tool_input_json = {}
                            if full_tool_input:
                                try:
                                    tool_input_json = json.loads(full_tool_input)
                                except json.JSONDecodeError as e:
                                    logger.error(f"Error parsing tool input JSON: {e}")
                                    logger.error(f"Full tool input: {full_tool_input}")
                                    tool_input_json = {"error": "Invalid JSON input"}
                            
                            assistant_message["content"].append({
                                "toolUse": {
                                    "toolUseId": tool_id,
                                    "name": tool_name,
                                    "input": tool_input_json
                                }
                            })
                            tool_input_placeholder.markdown(f"Tool input: {full_tool_input}")

                            try:
                                tool_results = process_tool_call(tool_name, tool_input_json)
                                tool_results_json = json.loads(tool_results)
                            except json.JSONDecodeError as e:
                                logger.error(f"Error decoding tool results JSON: {e}")
                                tool_results_json = {"error": "Invalid tool results format"}

                            with st.expander(f"🔍 Tool Results: {tool_name}", expanded=False):
                                if "error" in tool_results_json:
                                    st.error(tool_results_json["error"])
                                else:
                                    if tool_name in ["save_memory", "recall_memories", "update_memory", "delete_memory", "get_user_profile", "list_all_memories"]:
                                        st.markdown(format_memory_results(tool_results_json["result"]))
                                    else:
                                        st.json(tool_results_json["result"])

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

                            update_display_messages("tool", f"Tool used: {tool_name}", tool_name, full_tool_input, tool_results)
                            logger.debug(f"Tool results processed: {tool_results}")

                            tool_input_placeholder.empty()
                            is_tool_use = False
                            full_tool_input = ""
                            full_response = ""
                            assistant_message = {"role": "assistant", "content": []}
                        else:
                            if clean_answer:
                                assistant_message["content"].append({"text": clean_answer})
                                update_display_messages("assistant", clean_answer)
                                logger.debug(f"Final assistant message: {clean_answer}")
                            messages.append(assistant_message)

                    if 'metadata' in event:
                        metadata = event['metadata']
                        if 'usage' in metadata:
                            usage = metadata['usage']
                            turn_token_usage['inputTokens'] += usage.get('inputTokens', 0)
                            turn_token_usage['outputTokens'] += usage.get('outputTokens', 0)
                            turn_token_usage['totalTokens'] += usage.get('totalTokens', 0)

                if messages[-1]["role"] == "assistant":
                    return turn_token_usage

            except ClientError as err:
                message = err.response['Error']['Message']
                st.error(f"A client error occurred: {message}")
                logger.error(f"A client error occurred: {message}")
                st.stop()
                return
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")
                logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
                st.stop()
                return

    return turn_token_usage

def update_display_messages(role, content, tool_name=None, tool_input=None, tool_results=None):
    message = {
        "role": role,
        "content": content,
        "tool_name": tool_name,
        "tool_input": tool_input,
        "tool_results": tool_results
    }
    st.session_state.display_messages.append(message)
    logger.debug(f"Display message updated: {message}")