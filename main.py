import streamlit as st
from datetime import date
from src.bedrock_client import create_bedrock_client
from src.conversation_handler import handle_chat_input, process_ai_response
from src.utils import new_chat

import logging
logging.basicConfig(level=logging.INFO) # Set to DEBUG for more detailed logging or INFO for less detailed logging
logger = logging.getLogger(__name__)

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
        st.session_state['uploader_key'] = 0

    # File uploader - at the top, right after the title
    uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "webp"], key=f"uploader_{st.session_state['uploader_key']}")

    # Sidebar elements
    st.sidebar.button("New Chat", type="primary", on_click=new_chat)

    # Model selection
    models = [
        {"name": "Claude 3 Haiku", "id": "anthropic.claude-3-haiku-20240307-v1:0"},
        {"name": "Claude 3 Opus", "id": "anthropic.claude-3-opus-20240229-v1:0"},
        {"name": "Claude 3 Sonnet", "id": "anthropic.claude-3-sonnet-20240229-v1:0"},
        {"name": "Claude 3.5 Sonnet", "id": "anthropic.claude-3-5-sonnet-20240620-v1:0"}
    ]
    model_names = [model["name"] for model in models]
    selected_model_name = st.sidebar.selectbox("Select a model", model_names)
    model_id = next((model["id"] for model in models if model["name"] == selected_model_name), None)

    # System prompt and other configurations
    system_prompt = f"""
    Answer as many questions as you can using your existing knowledge.
    Only search the web for queries that you can not confidently answer.
    Today's date is {date.today().strftime("%B %d %Y")}
    If you think a user's question involves something in the future that hasn't happened yet, use the search tool.
    You can also analyze images that the user uploads.
    """
    region_name = "us-west-2"
    bedrock_client = create_bedrock_client(region_name)
    system_prompts = [{"text": system_prompt}]
    inference_config = {"temperature": 0.1}
    additional_model_fields = {"top_k": 200}

    # Display chat messages
    for message in st.session_state.display_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "image" in message:
                st.image(message["image"], caption="Uploaded Image", use_column_width=True)

    # Chat input and processing
    if prompt := st.chat_input("Ask me anything!"):
        image_content = None
        image_format = None
        if uploaded_file is not None:
            image_content = uploaded_file.read()
            image_format = uploaded_file.type.split('/')[-1]

        try:
            handle_chat_input(prompt, image_content, image_format)
            process_ai_response(bedrock_client, model_id, st.session_state.history, system_prompts, inference_config, additional_model_fields)

            # Reset the uploader key to allow new uploads
            st.session_state['uploader_key'] += 1
            st.rerun()
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            logger.exception("An error occurred during chat processing")

if __name__ == "__main__":
    main()