import json
import logging
import os
import random
from datetime import datetime

import streamlit as st
from PIL import Image

from src.bedrock_client import create_bedrock_client
from src.conversation_handler import handle_chat_input, process_ai_response
from src.memory_manager import MemoryManager  # Pbdcb
from src.utils import format_rss_results, format_search_results, new_chat

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

icon = Image.open("assets/favicon.ico")
st.set_page_config(page_title="ToolboxAI", page_icon=icon)

def main():
    st.title("ToolboxAI")

    # Initialize session state variables
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "history" not in st.session_state:
        st.session_state.history = []
    if "display_messages" not in st.session_state:
        st.session_state.display_messages = []
    if 'uploader_key' not in st.session_state:
        st.session_state['uploader_key'] = random.randint(1, 100000)
    if "token_usage" not in st.session_state:
        st.session_state.token_usage = None

    # File uploader for both images and documents
    allowed_types = ["png", "jpg", "jpeg", "webp", "pdf", "csv", "doc", "docx", "xls", "xlsx", "html", "txt", "md", "py"]
    uploaded_file = st.file_uploader("Upload an image or document", type=allowed_types, key=f"uploader_{st.session_state['uploader_key']}")

    # Sidebar elements
    st.sidebar.button("New Chat", type="primary", on_click=new_chat)

    # Model selection
    models = [
        {"name": "Claude 3.5 Sonnet", "id": "anthropic.claude-3-5-sonnet-20240620-v1:0"},
        {"name": "Claude 3 Haiku", "id": "anthropic.claude-3-haiku-20240307-v1:0"},
        {"name": "Claude 3 Sonnet", "id": "anthropic.claude-3-sonnet-20240229-v1:0"},
        {"name": "Claude 3 Opus", "id": "anthropic.claude-3-opus-20240229-v1:0"},
        {"name": "Command R+", "id": "cohere.command-r-plus-v1:0"}
    ]
    model_names = [model["name"] for model in models]
    selected_model_name = st.sidebar.selectbox("Select a model", model_names)

    model_id = next((model["id"] for model in models if model["name"] == selected_model_name), None)

    # AWS regions for dropdown
    regions = ["us-east-1", "us-west-2"]
    region_name = st.sidebar.selectbox("Select AWS Region", regions, index=regions.index("us-east-1"))

    # Display token usage if available
    if st.session_state.token_usage:
        st.sidebar.markdown("### Token Usage")
        st.sidebar.markdown(f"Input Tokens: {st.session_state.token_usage['inputTokens']}")
        st.sidebar.markdown(f"Output Tokens: {st.session_state.token_usage['outputTokens']}")
        st.sidebar.markdown(f"Total Tokens: {st.session_state.token_usage['totalTokens']}")

    # Get current date and time
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    system_prompt = f"""
    You are ToolboxAI, a personal AI assistant focused on personalized help and interactive experiences.

    ALWAYS start by using get_user_profile tool to retrieve latest user info.

    If profile needs updating, ask user questions and use update_user_profile tool.

    Current date/time: {current_datetime}

    Use available tools for accurate, personalized responses based on user's profile and needs.

    You can create and manage interactive story-based games using the game tools (start_game_server, add_scene, get_game_state).
    When a user wants to play a game, first use add_scene to create multiple scenes for an engaging story with choices.
    Then use start_game_server to launch the game in a new browser window.
    The user will interact with the game directly in the new window, but you can use get_game_state to check on their progress.
    """
    
    bedrock_client = create_bedrock_client(region_name)
    system_prompts = [{"text": system_prompt}]
    inference_config = {"temperature": 0.1}
    additional_model_fields = {"top_k": 200}

    with st.spinner("Initializing memory management. This may take a moment on first run..."):
        memory_manager = MemoryManager()

    # Display chat messages
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
                        
                        # Handle different tool types
                        if tool_name == 'search':
                            formatted_results = format_search_results(tool_results)
                        elif tool_name == 'rss_feed':
                            formatted_results = format_rss_results(tool_results)
                        else:
                            # For other tools, just display the raw results
                            formatted_results = json.dumps(tool_results, indent=2)
                        
                        st.markdown(formatted_results)
                        
                        # Display tool input if available
                        if "tool_input" in message:
                            st.subheader("Input:")
                            st.code(message["tool_input"])
                    
                    except Exception as e:
                        st.error(f"Error formatting {tool_name} results: {str(e)}")
                        st.json(message["tool_results"])  # Display raw results as fallback

                    else:
                        if "tool_input" in message:
                            st.subheader("Input:")
                            st.code(message["tool_input"])
                        st.subheader("Results:")
                        # Check if tool_results is a string (JSON) and parse it
                        if isinstance(message["tool_results"], str):
                            try:
                                tool_results = json.loads(tool_results)
                                st.json(tool_results)
                            except json.JSONDecodeError:
                                st.text(message["tool_results"])  # Display as plain text if not valid JSON
                        else:
                            st.json(message["tool_results"])

    # Chat input and processing
    if prompt := st.chat_input("Ask me anything or start a game!"):
        file_content = None
        file_name = None

        if uploaded_file is not None:
            file_content = uploaded_file.getvalue()
            file_name = uploaded_file.name

        try:
            # Immediately display user message and file info
            with st.chat_message("user"):
                st.markdown(prompt)
                if file_name:
                    name, ext = os.path.splitext(file_name)
                    file_format = ext.lstrip('.').lower()
                    if file_format in ["png", "jpg", "jpeg", "webp"]:
                        st.image(file_content, caption="Uploaded Image", width=300)
                    else:
                        st.markdown(f"Document uploaded: {name}")

            # Update session state
            handle_chat_input(prompt, file_content, file_name)

            # Process AI response
            process_ai_response(bedrock_client, model_id, st.session_state.history, system_prompts, inference_config, additional_model_fields)

            # Update the uploader key to reset the file uploader
            st.session_state['uploader_key'] = random.randint(1, 100000)
            st.rerun()

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            logger.exception("An error occurred during chat processing")

if __name__ == "__main__":
    main()
