import boto3
import json
import streamlit as st
from botocore.exceptions import ClientError

def create_bedrock_client():
    return boto3.client(service_name='bedrock-runtime', region_name='us-west-2')

def get_stream(bedrock_client, model_id, messages, system_prompts, inference_config, additional_model_fields):
    response = bedrock_client.converse_stream(
        modelId=model_id,
        messages=messages,
        system=system_prompts,
        inferenceConfig=inference_config,
        additionalModelRequestFields=additional_model_fields
    )
    return response.get('stream')

def stream_conversation(stream):
    if stream:
        for event in stream:
            yield event

def handle_chat_input(prompt):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": [{"text": prompt}]})

def handle_chat_output(event, message_placeholder, full_response):
    if 'contentBlockDelta' in event:
        text_chunk = event['contentBlockDelta']['delta']['text']
        full_response += text_chunk
        message_placeholder.markdown(full_response + "▌")
    return full_response

def main():
    st.title("Amazon Bedrock Chatbot with Streaming")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"][0]["text"])

    if prompt := st.chat_input("Ask me anything!"):
        handle_chat_input(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            model_id = "anthropic.claude-3-haiku-20240307-v1:0"
            system_prompt = """You are an assistant that provides responses based on the user's questions."""
            system_prompts = [{"text": system_prompt}]
            inference_config = {"temperature": 0.5}
            additional_model_fields = {"top_k": 200}

            try:
                bedrock_client = create_bedrock_client()
                messages = st.session_state.messages
                stream = get_stream(bedrock_client, model_id, messages, system_prompts, inference_config, additional_model_fields)

                for event in stream_conversation(stream):
                    full_response = handle_chat_output(event, message_placeholder, full_response)

                    if 'messageStop' in event:
                        stop_reason = event['messageStop']['stopReason']

                st.session_state.messages.append({"role": "assistant", "content": [{"text": full_response}]})
                message_placeholder.markdown(full_response)

            except ClientError as err:
                message = err.response['Error']['Message']
                st.error(f"A client error occurred: {message}")

if __name__ == "__main__":
    main()