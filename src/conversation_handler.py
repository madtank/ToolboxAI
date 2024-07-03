import streamlit as st
import json
from botocore.exceptions import ClientError
from src.bedrock_client import get_stream, stream_conversation
from src.utils import handle_chat_output, handle_tool_use, format_memory_results
from src.tools import toolConfig, process_tool_call
import os
import base64
import logging

logger = logging.getLogger(__name__)

def handle_chat_input(prompt, file_content=None, file_name=None):
    user_message = {"role": "user", "content": [{"text": prompt}]}
    display_message = {"role": "user", "content": prompt}
    
    if file_content and file_name:
        # Split the filename and extension
        name, ext = os.path.splitext(file_name)
        
        # Remove the dot from the extension
        file_format = ext.lstrip('.').lower()
        if file_format in ["png", "jpg", "jpeg", "webp"]:
            # Handle image files
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
        else:
            # Handle document files
            document_formats = ["pdf", "csv", "doc", "docx", "xls", "xlsx", "html", "txt", "md"]
            if file_format not in document_formats:
                file_format = "txt"  # Default to txt if format is not recognized
            
            user_message["content"].append({
                "document": {
                    "name": name,  # Use the filename without extension
                    "format": file_format,
                    "source": {
                        "bytes": file_content
                    }
                }
            })
            display_message["document"] = name  # Use the filename without extension
        
        display_message["file_type"] = file_format
        display_message["file_name"] = file_name
    st.session_state.history.append(user_message)
    st.session_state.display_messages.append(display_message)

def process_ai_response(bedrock_client, model_id, messages, system_prompts, inference_config, additional_model_fields):
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
            input_tokens = 0
            output_tokens = 0
            total_tokens = 0
            token_usage_placeholder = st.sidebar.empty()

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
                            # Process tool use
                            if full_response:
                                assistant_message["content"].append({"text": full_response})
                            
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
                            message_placeholder.markdown(full_response)
                            tool_input_placeholder.markdown(f"Tool input: {full_tool_input}")

                            try:
                                tool_results = process_tool_call(tool_name, tool_input_json)
                                tool_results_json = json.loads(tool_results)
                            except json.JSONDecodeError as e:
                                logger.error(f"Error decoding tool results JSON: {e}")
                                tool_results_json = {"error": "Invalid tool results format"}

                            # Display tool results in an expander
                            with st.expander(f"🔍 Tool Results: {tool_name}", expanded=False):
                                if "error" in tool_results_json:
                                    st.error(tool_results_json["error"])
                                else:
                                    if tool_name in ["save_memory", "recall_memories", "update_memory", "delete_memory", "get_user_profile", "list_all_memories"]:
                                        st.markdown(format_memory_results(tool_results_json["result"]))
                                    else:
                                        st.json(tool_results_json["result"])

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

                            # Update display messages
                            st.session_state.display_messages.append({"role": "assistant", "content": full_response})
                            st.session_state.display_messages.append({
                                "role": "tool", 
                                "content": f"Tool used: {tool_name}",
                                "tool_name": tool_name,
                                "tool_input": full_tool_input,
                                "tool_results": tool_results
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
                            # Update display messages
                            st.session_state.display_messages.append({"role": "assistant", "content": full_response})

                    if 'metadata' in event:
                        metadata = event['metadata']
                        if 'usage' in metadata:
                            usage = metadata['usage']
                            st.session_state.token_usage = {
                                'inputTokens': usage.get('inputTokens', 0),
                                'outputTokens': usage.get('outputTokens', 0),
                                'totalTokens': usage.get('totalTokens', 0)
                            }

                            # Update the token usage in the sidebar
                            token_usage_placeholder.markdown(f"**Usage Information:**\n- Input Tokens: {input_tokens}\n- Output Tokens: {output_tokens}\n- Total Tokens: {total_tokens}")

                # Check whose turn it is next
                if messages[-1]["role"] == "assistant":
                    # If it's the user's turn, we return to main
                    return
                # If it's the assistant's turn, the loop will continue

            except ClientError as err:
                message = err.response['Error']['Message']
                st.error(f"A client error occurred: {message}")
                logger.error(f"A client error occurred: {message}")
                st.stop()
                return  # Exit the function on error
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")
                logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
                st.stop()
                return  # Exit the function on error

def update_display_messages(role, content, tool_name=None, tool_input=None, tool_results=None):
    message = {"role": role, "content": content}
    if tool_name:
        message["tool_name"] = tool_name
    if tool_input is not None:
        message["tool_input"] = tool_input
    if tool_results is not None:
        message["tool_results"] = tool_results
    st.session_state.display_messages.append(message)