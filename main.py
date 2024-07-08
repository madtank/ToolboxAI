import streamlit as st
from agent_tool import get_tool_config, process_tool_call
import json
from datetime import datetime

st.set_page_config(page_title="ToolboxAI", page_icon=":toolbox:")

def main():
    st.title("ToolboxAI")

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "total_token_usage" not in st.session_state:
        st.session_state.total_token_usage = {
            'inputTokens': 0,
            'outputTokens': 0,
            'totalTokens': 0
        }

    # Sidebar
    st.sidebar.title("Settings")
    st.sidebar.button("New Chat", on_click=new_chat)

    # Display total token usage
    st.sidebar.subheader("Total Token Usage")
    st.sidebar.write(f"Input Tokens: {st.session_state.total_token_usage['inputTokens']}")
    st.sidebar.write(f"Output Tokens: {st.session_state.total_token_usage['outputTokens']}")
    st.sidebar.write(f"Total Tokens: {st.session_state.total_token_usage['totalTokens']}")

    # Chat interface
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What would you like to know?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = process_agent_response(prompt)
            message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

def new_chat():
    st.session_state.messages = []
    st.session_state.total_token_usage = {
        'inputTokens': 0,
        'outputTokens': 0,
        'totalTokens': 0
    }

def process_agent_response(prompt):
    tool_config = get_tool_config()
    
    # For simplicity, we're using the first tool in the config
    tool_name = tool_config['tools'][0]['toolSpec']['name']
    tool_input = {"query": prompt}
    
    response = process_tool_call(tool_name, tool_input)
    
    # Update token usage (this is a placeholder, as we don't have actual token counts)
    st.session_state.total_token_usage['inputTokens'] += len(prompt.split())
    st.session_state.total_token_usage['outputTokens'] += len(response.split())
    st.session_state.total_token_usage['totalTokens'] = (
        st.session_state.total_token_usage['inputTokens'] + 
        st.session_state.total_token_usage['outputTokens']
    )
    
    return response

if __name__ == "__main__":
    main()
