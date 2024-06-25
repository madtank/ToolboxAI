import streamlit as st

def new_chat():
    st.session_state.messages = []
    st.session_state.history = []
    st.session_state.display_messages = []

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