import boto3
import openai

def create_ai_client(provider, region=None, api_key=None, toolConfig=None):
    if provider == 'bedrock':
        return boto3.client(service_name='bedrock-runtime', region_name=region)
    elif provider == 'openai':
        openai.api_key = api_key
        return openai
    else:
        raise ValueError(f"Unsupported provider: {provider}")

def get_stream(client, provider, model_id, messages, system_prompts, inference_config, additional_model_fields, toolConfig):
    if provider == 'bedrock':
        response = client.converse_stream(
            modelId=model_id,
            messages=messages,
            system=system_prompts,
            inferenceConfig=inference_config,
            additionalModelRequestFields=additional_model_fields,
            toolConfig=toolConfig
        )
        return response.get('stream')
    elif provider == 'openai':
        functions = [tool['toolSpec'] for tool in toolConfig['tools']]
        response = client.ChatCompletion.create(
            model=model_id,
            messages=messages + [{"role": "system", "content": system_prompts[0]['text']}],
            functions=functions,
            stream=True
        )
        return response
    else:
        raise ValueError(f"Unsupported provider: {provider}")

def stream_conversation(stream, provider):
    if provider == 'bedrock':
        if stream:
            for event in stream:
                yield event
    elif provider == 'openai':
        for chunk in stream:
            yield chunk
    else:
        raise ValueError(f"Unsupported provider: {provider}")
