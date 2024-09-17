import streamlit as st
import json
import re
import os
import base64
import logging
from botocore.exceptions import ClientError
from src.bedrock_client import get_stream, stream_conversation
from src.utils import handle_tool_use, format_memory_results
from src.tools import process_tool_call
from src.memory_manager import MemoryManager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

memory_manager = MemoryManager()

def handle_chat_input(prompt, file_content=None, file_name=None):
    logger.debug(f"Handling chat input: {prompt}, file: {file_name}")
    
    user_message = {"role": "user", "content": []}
    display_message = {"role": "user", "content": prompt}
    
    if prompt:
        user_message["content"].append({"text": prompt})
    
    if file_content and file_name:
        name, ext = os.path.splitext(file_name)
        file_format = ext.lstrip('.').lower()
        
        if file_format in ["png", "jpg", "jpeg", "webp"]:
            user_message["content"].append({
                "image": {
                    "format": file_format,
                    "source": {
                        "bytes": file_content  # Pass raw bytes directly
                    }
                }
            })
            display_message["image"] = f"data:image/{file_format};base64,{base64.b64encode(file_content).decode()}"
            logger.debug(f"Processed image file: {file_name}")
        else:
            logger.warning(f"Unsupported file format: {file_format}")
            st.warning(f"Unsupported file format: {file_format}. Please upload an image (png, jpg, jpeg, or webp).")
            return
        
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
            thinking_placeholder = st.empty()
            tool_input_placeholder = st.empty()
            state = {
                "full_response": "",
                "thinking_content": "",
                "answer_content": "",
                "clean_answer": "",
                "is_thinking": False,
                "is_answering": False,
                "full_tool_input": "",
                "tool_name": None,
                "tool_id": None,
                "is_tool_use": False,
                "assistant_message": {"role": "assistant", "content": []},
                "message_stop_received": False,
                "stop_reason": None,
                "need_tool_use_handling": False,
                "all_events_processed": False,
                "turn_token_usage": turn_token_usage  # Add this line
            }

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
                    
                    handle_event(event, state, message_placeholder, thinking_placeholder, tool_input_placeholder)

                # All events have been processed
                state['all_events_processed'] = True

                if state['need_tool_use_handling']:
                    handle_tool_use_stop(state, messages, tool_input_placeholder)
                    # Reset state for next iteration
                    state['need_tool_use_handling'] = False
                    state['message_stop_received'] = False
                    state['all_events_processed'] = False
                else:
                    finalize_assistant_message(state, messages)
                    break  # Exit the loop only if we have a final response and all events are processed

            except ClientError as err:
                handle_client_error(err)
                break
            except Exception as e:
                handle_unexpected_error(e)
                break

    # Save the assistant's message to ChromaDB
    if messages[-1]["role"] == "assistant":
        memory_manager.save_message(messages[-1], st.session_state.conversation_id)

    return state['turn_token_usage']  # Return the updated token usage

def handle_event(event, state, message_placeholder, thinking_placeholder, tool_input_placeholder):
    if 'contentBlockStart' in event:
        handle_content_block_start(event, state)
    elif 'contentBlockDelta' in event:
        handle_content_block_delta(event, state, message_placeholder, thinking_placeholder, tool_input_placeholder)
    elif 'messageStop' in event:
        state['message_stop_received'] = True
        state['stop_reason'] = event['messageStop'].get('stopReason')
        if state['stop_reason'] == 'tool_use':
            state['need_tool_use_handling'] = True
    elif 'metadata' in event:
        # This is likely the last event, containing token usage information
        update_token_usage(event, state['turn_token_usage'])

def update_token_usage(event, turn_token_usage):
    if 'metadata' in event:
        metadata = event['metadata']
        if 'usage' in metadata:
            usage = metadata['usage']
            turn_token_usage['inputTokens'] += usage.get('inputTokens', 0)
            turn_token_usage['outputTokens'] += usage.get('outputTokens', 0)
            turn_token_usage['totalTokens'] += usage.get('totalTokens', 0)

def handle_content_block_start(event, state):
    start = event['contentBlockStart']['start']
    if 'toolUse' in start:
        state['is_tool_use'] = True
        tool_use = start['toolUse']
        state['tool_id'] = tool_use['toolUseId']
        state['tool_name'] = tool_use['name']
        logger.debug(f"Tool use started: {state['tool_name']}")

def handle_content_block_delta(event, state, message_placeholder, thinking_placeholder, tool_input_placeholder):
    delta = event['contentBlockDelta']['delta']
    
    if 'text' in delta and not state['is_tool_use']:
        process_text_delta(delta['text'], state, message_placeholder, thinking_placeholder)
    elif 'toolUse' in delta and state['is_tool_use']:
        state['full_tool_input'] = handle_tool_use(delta, tool_input_placeholder, state['full_tool_input'], False)
        logger.debug(f"Tool input: {state['full_tool_input']}")

def process_text_delta(text_chunk, state, message_placeholder, thinking_placeholder):
    state['full_response'] += text_chunk
    
    # Instead of separating thinking and answering, just append all text to answer_content
    state['answer_content'] += text_chunk
    
    # Display the full response, including tags
    message_placeholder.markdown(state['full_response'])
    logger.debug(f"Assistant response: {state['full_response']}")

    # Optionally, you can keep a 'clean' version without tags for other purposes
    state['clean_answer'] = re.sub(r'<thinking>|</thinking>|<answer>|</answer>', '', state['full_response']).strip()

def handle_tool_use_stop(state, messages, tool_input_placeholder):
    # Parse the tool input
    tool_input_json = parse_tool_input(state['full_tool_input'])
    
    # Append tool use information
    state['assistant_message']["content"].append({
        "toolUse": {
            "toolUseId": state['tool_id'],
            "name": state['tool_name'],
            "input": tool_input_json
        }
    })
    
    # Get tool results
    tool_results = get_tool_results(state['tool_name'], tool_input_json)
    
    # Display tool results
    display_tool_results(state['tool_name'], tool_input_json, tool_results)

    if state['full_response']:  # Changed from state['clean_answer']
        state['assistant_message']["content"].append({"text": state['full_response']})  # Changed from state['clean_answer']
        update_display_messages("assistant", state['full_response'])  # Changed from state['clean_answer']
        logger.debug(f"Assistant message appended: {state['full_response']}")  # Changed from state['clean_answer']
    
    # tool_input_placeholder.markdown(f"Tool input: {state['full_tool_input']}")

    messages.append(state['assistant_message'])
    messages.append({
        "role": "user",
        "content": [
            {
                "toolResult": {
                    "toolUseId": state['tool_id'],
                    "content": [
                        {"text": str(tool_results)}
                    ]
                }
            }
        ]
    })

    update_display_messages("tool", f"Tool used: {state['tool_name']}", state['tool_name'], state['full_tool_input'], tool_results)
    logger.debug(f"Tool results processed: {tool_results}")
def parse_tool_input(full_tool_input):
    if full_tool_input:
        try:
            return json.loads(full_tool_input)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing tool input JSON: {e}")
            logger.error(f"Full tool input: {full_tool_input}")
            return {"error": "Invalid JSON input"}
    return {}

def get_tool_results(tool_name, tool_input):
    try:
        tool_results = process_tool_call(tool_name, tool_input)
        return json.loads(tool_results)  # Parse the JSON string
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding tool results JSON: {e}")
        return {"error": "Invalid tool results format"}

def display_tool_results(tool_name, tool_input, tool_results):
    with st.expander(f"🔍 Tool Results: {tool_name}", expanded=False):
        # Display tool input
        st.subheader("Tool Input:")
        st.json(tool_input)

        # Display tool results
        st.subheader("Tool Output:")
        if isinstance(tool_results, str):
            try:
                tool_results = json.loads(tool_results)
            except json.JSONDecodeError:
                tool_results = {"result": tool_results}
        
        if "error" in tool_results:
            st.error(tool_results["error"])
        elif "result" in tool_results:
            st.write(tool_results["result"])
        else:
            st.json(tool_results)

def finalize_assistant_message(state, messages):
    if state['clean_answer']:
        state['assistant_message']["content"].append({"text": state['clean_answer']})
        update_display_messages("assistant", state['clean_answer'])
        logger.debug(f"Final assistant message: {state['clean_answer']}")
    messages.append(state['assistant_message'])

def handle_client_error(err):
    message = err.response['Error']['Message']
    st.error(f"A client error occurred: {message}")
    logger.error(f"A client error occurred: {message}")
    st.stop()

def handle_unexpected_error(e):
    st.error(f"An unexpected error occurred: {str(e)}")
    logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
    st.stop()

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