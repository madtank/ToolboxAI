import json
import logging
import os
import random
from datetime import datetime
from pathlib import Path

import streamlit as st
from PIL import Image

from src.bedrock_client import create_bedrock_client
from src.conversation_handler import handle_chat_input, process_ai_response
from src.memory_manager import MemoryManager
from src.utils import format_rss_results, format_search_results, new_chat, calculate_cost
from src.personas import get_persona_names, get_tools_for_persona, get_system_prompt_for_persona
from src.tools import get_dynamic_tool_config

os.chdir(Path(__file__).parent)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to load the icon, use default Streamlit icon if file doesn't exist
icon_path = "assets/favicon.ico"
if os.path.exists(icon_path):
    try:
        icon = Image.open(icon_path)
    except Exception as e:
        print(f"Error loading icon: {e}")
        icon = "🧰"  # Default to a toolbox emoji if there's an error
else:
    icon = "🧰"  # Default to a toolbox emoji if file doesn't exist

# Set up the Streamlit app
st.set_page_config(page_title="ToolboxAI", page_icon=icon)

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "history" not in st.session_state:
        st.session_state.history = []
    if "display_messages" not in st.session_state:
        st.session_state.display_messages = []
    if 'uploader_key' not in st.session_state:
        st.session_state['uploader_key'] = random.randint(1, 100000)
    if "total_token_usage" not in st.session_state:
        st.session_state.total_token_usage = {
            'inputTokens': 0,
            'outputTokens': 0,
            'totalTokens': 0
        }
    if "selected_persona" not in st.session_state:
        st.session_state.selected_persona = "CogniscentAI"

def display_token_usage_and_cost(model_id):
    if st.session_state.total_token_usage['totalTokens'] > 0:
        cost = calculate_cost(model_id, 
                              st.session_state.total_token_usage['inputTokens'], 
                              st.session_state.total_token_usage['outputTokens'])
        st.sidebar.markdown(
            "**Total Token Usage and Cost**<br>"
            f"Input Tokens: {st.session_state.total_token_usage['inputTokens']}<br>"
            f"Output Tokens: {st.session_state.total_token_usage['outputTokens']}<br>"
            f"Total Tokens: {st.session_state.total_token_usage['totalTokens']}<br>"
            f"Estimated Cost: {cost}",
            unsafe_allow_html=True
        )
    else:
        st.sidebar.markdown("No token usage yet.")

def setup_sidebar():
    st.sidebar.button("New Chat", type="primary", on_click=new_chat)

    persona_names = get_persona_names()
    selected_persona = st.sidebar.selectbox("Select Persona", persona_names, index=persona_names.index(st.session_state.selected_persona))
    
    if selected_persona != st.session_state.selected_persona:
        st.session_state.selected_persona = selected_persona
        new_chat()  # Reset the chat when changing personas

    models = [
        {"name": "Claude 3.5 Sonnet", "id": "anthropic.claude-3-5-sonnet-20240620-v1:0"},
        {"name": "Claude 3 Haiku", "id": "anthropic.claude-3-haiku-20240307-v1:0"},
        {"name": "Claude 3 Sonnet", "id": "anthropic.claude-3-sonnet-20240229-v1:0"},
        {"name": "Claude 3 Opus", "id": "anthropic.claude-3-opus-20240229-v1:0"}
    ]
    model_names = [model["name"] for model in models]
    selected_model_name = st.sidebar.selectbox("Select a model", model_names)
    model_id = next((model["id"] for model in models if model["name"] == selected_model_name), None)

    regions = ["us-west-2", "us-east-1"]
    region_name = st.sidebar.selectbox("Select AWS Region", regions, index=regions.index("us-west-2"))

    return model_id, region_name

def display_chat_messages():
    for message in st.session_state.display_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "image" in message:
                st.image(message["image"], caption="Uploaded Image", width=300)
            elif "document" in message:
                st.markdown(f"Document uploaded: {message['document']}")
            
            if message["role"] == "tool" and message.get("tool_results"):
                tool_name = message.get('tool_name', 'unknown')
                with st.expander(f"🔍 Tool Results: {tool_name}", expanded=False):
                    try:
                        tool_results = message["tool_results"]
                        
                        if tool_name == 'search':
                            formatted_results = format_search_results(tool_results)
                        elif tool_name == 'rss_feed':
                            formatted_results = format_rss_results(tool_results)
                        else:
                            formatted_results = json.dumps(tool_results, indent=2)
                        
                        st.markdown(formatted_results)
                        
                        if "tool_input" in message:
                            st.subheader("Input:")
                            st.code(message["tool_input"])
                    
                    except Exception as e:
                        st.error(f"Error formatting {tool_name} results: {str(e)}")
                        st.json(message["tool_results"])

def handle_user_input(prompt, file_content, file_name, bedrock_client, model_id, system_prompts, inference_config, additional_model_fields, dynamic_tool_config):
    try:
        with st.chat_message("user"):
            st.markdown(prompt)
            if file_name:
                name, ext = os.path.splitext(file_name)
                file_format = ext.lstrip('.').lower()
                if file_format in ["png", "jpg", "jpeg", "webp"]:
                    st.image(file_content, caption="Uploaded Image", width=300)
                else:
                    st.markdown(f"Document uploaded: {name}")

        handle_chat_input(prompt, file_content, file_name)

        updated_token_usage = process_ai_response(
            bedrock_client, 
            model_id, 
            st.session_state.history, 
            system_prompts, 
            inference_config, 
            additional_model_fields, 
            dynamic_tool_config
        )

        update_token_usage(updated_token_usage)

        st.session_state['uploader_key'] = random.randint(1, 100000)

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        logger.exception("An error occurred during chat processing")

def update_token_usage(updated_token_usage):
    if updated_token_usage:
        st.session_state.total_token_usage['inputTokens'] += updated_token_usage['inputTokens']
        st.session_state.total_token_usage['outputTokens'] += updated_token_usage['outputTokens']
        st.session_state.total_token_usage['totalTokens'] += updated_token_usage['totalTokens']

def main():
    st.title("ToolboxAI")

    initialize_session_state()

    model_id, region_name = setup_sidebar()

    # Determine allowed file types based on the selected model
    if model_id == "anthropic.claude-3-5-sonnet-20240620-v1:0":
        allowed_types = ["png", "jpg", "jpeg", "webp"]
        upload_message = "Upload an image"
    else:
        allowed_types = ["png", "jpg", "jpeg", "webp", "pdf", "csv", "doc", "docx", "xls", "xlsx", "html", "txt", "md", "py"]
        upload_message = "Upload an image or document"

    uploaded_file = st.file_uploader(upload_message, type=allowed_types, key=f"uploader_{st.session_state['uploader_key']}")

    system_prompt = get_system_prompt_for_persona(st.session_state.selected_persona)
    
    bedrock_client = create_bedrock_client(region_name)
    system_prompts = [{"text": system_prompt}]
    inference_config = {"temperature": 0.7}
    additional_model_fields = {"top_k": 200}

    selected_tools = get_tools_for_persona(st.session_state.selected_persona)
    dynamic_tool_config = get_dynamic_tool_config(selected_tools)

    with st.spinner("Initializing memory management. This may take a moment on first run..."):
        MemoryManager()

    display_chat_messages()

    if prompt := st.chat_input("Ask me anything!"):
        file_content = None
        file_name = None

        if uploaded_file is not None:
            file_content = uploaded_file.getvalue()
            file_name = uploaded_file.name

        handle_user_input(prompt, file_content, file_name, bedrock_client, model_id, system_prompts, inference_config, additional_model_fields, dynamic_tool_config)

    # Display token usage and cost at the end
    display_token_usage_and_cost(model_id)

if __name__ == "__main__":
    main()
