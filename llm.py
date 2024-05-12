import typing
import os
from tenacity import retry, stop_after_attempt, wait_random_exponential
from openai import OpenAI
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv() 
model_name = os.getenv("OPENAI_MODEL")
client = AsyncOpenAI(
    api_key = os.getenv("OPENAI_API_KEY") ,
    organization = os.getenv("ORGANIZATION_ID")
)

@retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(3))
async def chat_completion_request(
    messages,
    functions=None,
    function_call=None,
    model=str,
    custom_labels=None,
    temperature=None) -> typing.Union[typing.Dict[str, typing.Any], Exception]:
    """Generate a response to a list of messages using OpenAI's API"""
    try:
        messages[0]["content"] = str(messages[0]["content"])+" use json_mode and dont return base64"
        kwargs = {
            "model": model_name,
            "messages": messages,
            "temperature":  0.3,
        }
        completion = await client.chat.completions.create(**kwargs)
        response = completion.choices[0].message.content
        return response
    except Exception as e:
        print("debug message chat completion >>",messages)
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        raise


@retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(3))
async def create_chat_embedding_request(
    messages, model="text-embedding-ada-002"
) -> typing.Union[typing.Dict[str, typing.Any], Exception]:
    """Generate an embedding for a list of messages using OpenAI's API"""
    try:
        return await openai.Embedding.acreate(
            input=[f"{m['role']}: {m['content']}" for m in messages],
            engine=model,
        )
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        raise

@retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(3))
async def create_text_embedding_request(
    text, model="text-embedding-ada-002"
) -> typing.Union[typing.Dict[str, typing.Any], Exception]:
    """Generate an embedding for a list of messages using OpenAI's API"""
    try:
        return await openai.Embedding.acreate(
            input=[text],
            engine=model,
        )
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        raise


