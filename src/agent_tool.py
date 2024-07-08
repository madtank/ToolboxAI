import streamlit as st
import boto3
import json
from botocore.exceptions import ClientError
import uuid
from config import TEST_MODE, DEFAULT_REGION, TEST_AGENT_ID, TEST_AGENT_ALIAS_ID

def create_agents_for_bedrock_client(region):
    return boto3.client(service_name='bedrock-agent-runtime', region_name=region)

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

def agent_tool(input_text):
    region = DEFAULT_REGION if TEST_MODE else st.session_state.get('region_name', DEFAULT_REGION)
    agent_id = TEST_AGENT_ID if TEST_MODE else st.session_state.get('agent_id', TEST_AGENT_ID)
    agent_alias_id = TEST_AGENT_ALIAS_ID if TEST_MODE else st.session_state.get('agent_alias_id', TEST_AGENT_ALIAS_ID)
    
    client = create_agents_for_bedrock_client(region)
    
    if 'agent_session_id' not in st.session_state:
        st.session_state.agent_session_id = str(uuid.uuid4())
    
    result, citations = invoke_agent(client, agent_id, agent_alias_id, input_text, st.session_state.agent_session_id)
    
    if result:
        formatted_result = format_agent_response(result, citations)
        
        with st.expander("Agent Response", expanded=True):
            st.markdown(formatted_result)
        
        return formatted_result
    else:
        return "Failed to get a response from the agent."