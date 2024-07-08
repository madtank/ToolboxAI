import streamlit as st
import boto3
import json
import uuid
from botocore.exceptions import ClientError

def create_bedrock_runtime_client(region="us-east-1"):
    return boto3.client(service_name='bedrock-runtime', region_name=region)

def invoke_agent(client, agent_id, agent_alias_id, input_text, session_id):
    try:
        with st.spinner("Contacting agent..."):
            response = client.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                sessionId=session_id,
                inputText=input_text,
                enableTrace=True
            )
        
        result = ""
        citations = []
        
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    result += chunk['bytes'].decode()
                if 'attribution' in chunk:
                    for citation in chunk['attribution'].get('citations', []):
                        citations.append({
                            'text': citation['generatedResponsePart'].get('text', ''),
                            'reference': citation['retrievedReferences'][0] if citation['retrievedReferences'] else None
                        })
        
        return result, citations
    
    except ClientError as e:
        st.error(f"An error occurred: {str(e)}")
        return None, None

def format_agent_response(result, citations):
    formatted_result = result
    
    if citations:
        formatted_result += "\n\nCitations:\n"
        for i, citation in enumerate(citations, 1):
            formatted_result += f"{i}. {citation['text']}\n"
            if citation['reference']:
                formatted_result += f"   Source: {citation['reference'].get('content', {}).get('text', 'N/A')}\n"
                formatted_result += f"   Location: {citation['reference'].get('location', {}).get('s3Location', {}).get('uri', 'N/A')}\n"
            formatted_result += "\n"
    
    return formatted_result

def agent_tool(query, agent_id, agent_alias_id):
    client = create_bedrock_runtime_client()
    
    if 'agent_session_id' not in st.session_state:
        st.session_state.agent_session_id = str(uuid.uuid4())
    
    result, citations = invoke_agent(client, agent_id, agent_alias_id, query, st.session_state.agent_session_id)
    
    if result:
        formatted_result = format_agent_response(result, citations)
        
        with st.expander("Agent Response", expanded=True):
            st.markdown(formatted_result)
        
        return formatted_result
    else:
        return "Failed to get a response from the agent."

# Tool configuration
AGENT_TOOLS = [
    {
        'name': 'general_agent',
        'description': 'Use this general-purpose Bedrock agent (ID: YTLVOXZIDY, Alias: OXFBEUV8LB) to perform complex tasks, answer questions, and provide information. This agent can handle a wide range of queries and tasks.',
        'agent_id': 'YTLVOXZIDY',
        'agent_alias_id': 'OXFBEUV8LB'
    },
    # Add more agent definitions here if needed
]

def get_tool_config():
    return {
        'tools': [
            {
                'toolSpec': {
                    'name': tool['name'],
                    'description': tool['description'],
                    'inputSchema': {
                        'json': {
                            'type': 'object',
                            'properties': {
                                'query': {'type': 'string', 'description': 'The query or task for the agent to process'}
                            },
                            'required': ['query']
                        }
                    }
                }
            } for tool in AGENT_TOOLS
        ],
        'toolChoice': {'auto': {}}
    }

def process_tool_call(tool_name, tool_input):
    for tool in AGENT_TOOLS:
        if tool['name'] == tool_name:
            return agent_tool(tool_input["query"], tool['agent_id'], tool['agent_alias_id'])
    return f"Unknown tool: {tool_name}"
