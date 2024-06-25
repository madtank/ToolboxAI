import streamlit as st
from datetime import date
from bedrock_client import create_bedrock_client
from conversation_handler import handle_chat_input, process_ai_response
from utils import new_chat

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
        process_ai_response(bedrock_client, model_id, st.session_state.history, system_prompts, inference_config, additional_model_fields)

if __name__ == "__main__":
    main()