import random
import json
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

def handle_chat_output(delta, message_placeholder, full_response, answer_content, is_thinking):
    text_chunk = delta['text']
    full_response += text_chunk
    
    if '<thinking>' in text_chunk:
        is_thinking = True
        message_placeholder.markdown("Thinking...")
    elif '</thinking>' in text_chunk:
        is_thinking = False
        message_placeholder.empty()
    
    if '<answer>' in text_chunk:
        answer_start = full_response.rfind('<answer>') + 8
        answer_content = full_response[answer_start:]
    elif '</answer>' in text_chunk:
        answer_end = full_response.rfind('</answer>')
        answer_content = full_response[full_response.rfind('<answer>') + 8:answer_end]
    
    if not is_thinking:
        message_placeholder.markdown(answer_content)
    
    return full_response, answer_content, is_thinking

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
    if isinstance(results, str):
        try:
            results = json.loads(results)
        except json.JSONDecodeError:
            return "Error: Search results are not in a valid format."

    if isinstance(results, dict) and 'result' in results:
        results = results['result']

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
    if isinstance(entries, str):
        try:
            entries = json.loads(entries)
        except json.JSONDecodeError:
            return "Error: RSS feed results are not in a valid format."

    if isinstance(entries, dict) and 'result' in entries:
        entries = entries['result']

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
    if isinstance(results, str):
        try:
            results = json.loads(results)
        except json.JSONDecodeError:
            return results  # Return as-is if it's not JSON

    if isinstance(results, dict):
        return "\n".join(f"{key}: {value}" for key, value in results.items())
    elif isinstance(results, list):
        return "\n".join(str(item) for item in results)
    else:
        return str(results)

def calculate_cost(model_id, input_tokens, output_tokens):
    # Pricing information for different models (as of the latest update)
    pricing = {
        "anthropic.claude-3-haiku-20240307-v1:0": {"input": 0.00025, "output": 0.00125},
        "anthropic.claude-3-sonnet-20240229-v1:0": {"input": 0.003, "output": 0.015},
        "anthropic.claude-3-5-sonnet-20240620-v1:0": {"input": 0.003, "output": 0.015},
        "anthropic.claude-3-opus-20240229-v1:0": {"input": 0.015, "output": 0.075}
    }
    
    if model_id not in pricing:
        return "Cost calculation not available for this model"
    
    model_pricing = pricing[model_id]
    input_cost = (input_tokens / 1000) * model_pricing["input"]
    output_cost = (output_tokens / 1000) * model_pricing["output"]
    total_cost = input_cost + output_cost
    
    return f"${total_cost:.4f}"