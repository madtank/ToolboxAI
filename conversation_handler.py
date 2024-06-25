import streamlit as st
import json
from botocore.exceptions import ClientError
from bedrock_client import get_stream, stream_conversation
from utils import handle_chat_output, handle_tool_use
from tools import process_tool_call

def handle_chat_input(prompt):
    user_message = {"role": "user", "content": [{"text": prompt}]}
    st.session_state.history.append(user_message)
    st.session_state.display_messages.append({"role": "user", "content": prompt})

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
                    additional_model_fields
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
                            assistant_message["content"].append({
                                "toolUse": {
                                    "toolUseId": tool_id,
                                    "name": tool_name,
                                    "input": json.loads(full_tool_input)
                                }
                            })
                            message_placeholder.markdown(full_response)
                            tool_input_placeholder.markdown(f"Tool input: {full_tool_input}")

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

                            # Update display messages
                            st.session_state.display_messages.append({"role": "assistant", "content": full_response})
                            st.session_state.display_messages.append({"role": "tool", "content": f"Tool: {tool_name}\nInput: {full_tool_input}\nResults: {tool_results}"})

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

                    elif 'metadata' in event:
                        metadata = event['metadata']
                        if 'usage' in metadata:
                            usage = metadata['usage']
                            input_tokens = usage.get('inputTokens', 0)
                            output_tokens = usage.get('outputTokens', 0)
                            total_tokens = usage.get('totalTokens', 0)

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
                return  # Exit the function on error