import boto3
from tools import toolConfig

def create_bedrock_client():
    return boto3.client(service_name='bedrock-runtime', region_name='us-east-1')

def get_stream(bedrock_client, model_id, messages, system_prompts, inference_config, additional_model_fields):
    response = bedrock_client.converse_stream(
        modelId=model_id,
        messages=messages,
        system=system_prompts,
        inferenceConfig=inference_config,
        additionalModelRequestFields=additional_model_fields,
        toolConfig=toolConfig
    )
    return response.get('stream')

def stream_conversation(stream):
    if stream:
        for event in stream:
            yield event