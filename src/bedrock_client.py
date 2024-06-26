import boto3

def create_bedrock_client(region):
    return boto3.client(service_name='bedrock-runtime', region_name=region)

def get_stream(bedrock_client, model_id, messages, system_prompts, inference_config, additional_model_fields, toolConfig):
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