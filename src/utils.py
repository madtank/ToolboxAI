import random
import streamlit as st

def new_chat():
    st.session_state.messages = []
    st.session_state.history = []
    st.session_state.display_messages = []
    st.session_state['uploader_key'] = random.randint(1, 100000)
    st.session_state.token_usage = None
    # Reset the total token usage
    st.session_state.total_token_usage = {
        'inputTokens': 0,
        'outputTokens': 0,
        'totalTokens': 0
    }

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
    if not isinstance(results, list):
        return "Error: Unexpected format for search results."

    formatted_output = "Search Results:\n\n"
    for i, result in enumerate(results, 1):
        if isinstance(result, dict):
            title = result.get('title', 'No title')
            href = result.get('href', '#')
            body = result.get('body', 'No description available.')
            
            formatted_output += f"{i}. [{title}]({href})\n"
            formatted_output += f"   {body}\n"
            formatted_output += f"   URL: {href}\n\n"
        else:
            formatted_output += f"{i}. Unable to parse result\n\n"
    
    return formatted_output

def format_rss_results(entries):
    if not isinstance(entries, list):
        return "Error: Unexpected format for RSS feed results."

    formatted_output = "RSS Feed Results:\n\n"
    for i, entry in enumerate(entries, 1):
        if isinstance(entry, dict):
            title = entry.get('title', 'No title')
            link = entry.get('link', '#')
            published = entry.get('published', 'No publication date')
            summary = entry.get('summary', 'No summary available.')
            
            formatted_output += f"{i}. [{title}]({link})\n"
            formatted_output += f"   Published: {published}\n"
            formatted_output += f"   Summary: {summary}\n"
            formatted_output += f"   URL: {link}\n\n"
        else:
            formatted_output += f"{i}. Unable to parse entry\n\n"
    
    return formatted_output

def format_memory_results(results):
    if isinstance(results, dict):
        return "\n".join(f"{key}: {value}" for key, value in results.items())
    elif isinstance(results, list):
        return "\n".join(str(item) for item in results)
    else:
        return str(results)
