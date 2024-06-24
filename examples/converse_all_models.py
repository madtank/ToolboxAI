import boto3
import streamlit as st
from botocore.exceptions import ClientError

def create_bedrock_client():
    # Change the region_name to the region where your Bedrock API is hosted
    return boto3.client(service_name='bedrock-runtime', region_name='us-east-1')

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

def handle_chat_output(event, message_placeholder, full_response):
    if 'contentBlockDelta' in event:
        text_chunk = event['contentBlockDelta']['delta']['text']
        full_response += text_chunk
        message_placeholder.markdown(full_response + "▌")
    return full_response

def handle_conversation(messages, model_id):
    """
    Handles the conversation by streaming responses from the specified model and updating the UI.
    
    :param messages: The list of messages for the conversation.
    :param model_id: The ID of the model to use for generating responses.
    """
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        system_prompt = "You are an assistant that provides responses based on the user's questions."
        system_prompts = [{"text": system_prompt}]
        inference_config = {"temperature": 0.1}
        additional_model_fields = {"top_k": 200}

        try:
            bedrock_client = create_bedrock_client()
            stream = get_stream(
                bedrock_client, 
                model_id, 
                messages, 
                system_prompts, 
                inference_config, 
                additional_model_fields
            )
            for event in stream_conversation(stream):
                full_response = handle_chat_output(event, message_placeholder, full_response)

                if 'messageStop' in event:
                    stop_reason = event['messageStop']['stopReason']
                    if stop_reason == "end_turn":
                        st.session_state.messages.append({"role": "assistant", "content": [{"text": full_response}]})
                        message_placeholder.markdown(full_response)

        except ClientError as err:
            message = err.response['Error']['Message']
            st.error(f"A client error occurred: {message}")

def main():
    st.title("Amazon Bedrock Chatbot with Streaming")
    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"][0]["text"])

    if prompt := st.chat_input("Ask me anything!"):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": [{"text": prompt}]})
        handle_conversation(st.session_state.messages, model_id)

if __name__ == "__main__":
    main()