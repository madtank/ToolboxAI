import boto3
import json
import streamlit as st
from datetime import date
from botocore.exceptions import ClientError
from tools import process_tool_call, toolConfig

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
    user_message = {"role": "user", "content": [{"text": prompt}]}
    st.session_state.history.append(user_message)
    st.session_state.display_messages.append({"role": "user", "content": prompt})

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

def new_chat():
    st.session_state.messages = []
    st.session_state.history = []
    st.session_state.display_messages = []

def main():
    st.title("Converse API - Tools")

    system_prompt = f"""
    Answer as many questions as you can using your existing knowledge.
    Only search the web for queries that you can not confidently answer.
    Today's date is {date.today().strftime("%B %d %Y")}
    If you think a user's question involves something in the future that hasn't happened yet, use the search tool.
    """

    # Add a button to start a new chat
    st.sidebar.button("New Chat", on_click=new_chat, type="primary")

    # Initialize session state variables
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "history" not in st.session_state:
        st.session_state.history = []
    if "display_messages" not in st.session_state:
        st.session_state.display_messages = []

    bedrock_client = create_bedrock_client()
    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    system_prompts = [{"text": system_prompt}]
    inference_config = {"temperature": 0.1}
    additional_model_fields = {"top_k": 200}

    # Display messages
    for message in st.session_state.display_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask me anything!"):
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)

        # Handle chat input and process AI response
        handle_chat_input(prompt)
        process_ai_response(bedrock_client, model_id, st.session_state.history, system_prompts, inference_config, additional_model_fields, toolConfig)

if __name__ == "__main__":
    main()