import random
import streamlit as st

def new_chat():
    st.session_state.messages = []
    st.session_state.history = []
    st.session_state.display_messages = []
    st.session_state['uploader_key'] = random.randint(1, 100000)  # Add this line

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

def format_search_results(results):
    formatted_output = "Search Results:\n\n"
    for i, result in enumerate(results, 1):
        title = result.get('title', 'No title')
        href = result.get('href', '#')
        body = result.get('body', 'No description available.')
        
        formatted_output += f"{i}. [{title}]({href})\n"
        formatted_output += f"   {body}\n"
        formatted_output += f"   URL: {href}\n\n"
    
    return formatted_output