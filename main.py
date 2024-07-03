import streamlit as st
from datetime import datetime
from src.bedrock_client import create_bedrock_client
from src.conversation_handler import handle_chat_input, process_ai_response
from src.utils import new_chat, format_search_results, format_rss_results
import random
from PIL import Image
import os
from src.memory_manager import MemoryManager  # Pbdcb

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
current_datetime = datetime.now().strftime("%B %d %Y %I:%M %p")

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
    allowed_types = ["png", "jpg", "jpeg", "webp", "pdf", "csv", "doc", "docx", "xls", "xlsx", "html", "txt", "md"]
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

    # System prompt and other configurations
    system_prompt = f"""
    You are a personal AI assistant. Your primary goal is to provide helpful, personalized assistance.

    1. At the start of each new conversation, use the 'get_user_profile' tool with the input "all" to retrieve basic user information. If none exists, engage the user to learn about their preferences, hobbies, and personal details.

    2. Regularly use the 'save_memory' tool to store important user information, including:
    - Preferences and dislikes
    - Hobbies and interests
    - Personal details relevant to future interactions
    - Any information that helps personalize your assistance

    3. Use the 'get_user_profile' tool with specific inputs ("preferences", "hobbies", "personal_details") when you need particular information about the user.

    4. When using tools it may be preferable to know the time and date, so here it is for reference: {current_datetime}.

    5. You can analyze user-uploaded images.

    6. Always strive to provide personalized, context-aware responses based on the user's saved information.

    7. You have access to an RSS feed tool that can fetch recent news from various sources. Use it when asked about recent news or developments. The available RSS feeds are:
    - AI news: Use "AI news" as the url parameter for TechCrunch's AI news feed
    - Finance news: Use "Finance news" as the url parameter for Wall Street Journal's Markets feed
    - US News: Use "US News" as the url parameter for New York Times' US news feed
    - World News: Use "World News" as the url parameter for New York Times' World news feed

    8. You can analyze Excel files using the excel_analysis tool. Use it when asked about data in uploaded Excel files.

    9. If you think a user's question involves something in the future that hasn't happened yet, use the search tool.

    Remember, building and using a comprehensive user profile over time is key to providing excellent assistance. Only search the web for queries that you cannot confidently answer based on your existing knowledge or the user's profile.
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
            if "tool_results" in message:
                with st.expander(f"🔍 Tool Results: {message['tool_name']}", expanded=False):
                    if message['tool_name'] == 'search':
                        st.markdown(format_search_results(message["tool_results"]))
                    elif message['tool_name'] == 'rss_feed':
                        st.markdown(format_rss_results(message["tool_results"]))
                    else:
                        st.subheader("Input:")
                        st.code(message["tool_input"])
                        st.subheader("Results:")
                        st.json(message["tool_results"])

    # Chat input and processing
    if prompt := st.chat_input("Ask me anything!"):
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
