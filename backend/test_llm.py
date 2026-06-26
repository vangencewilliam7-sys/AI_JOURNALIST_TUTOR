import asyncio
import os
from dotenv import dotenv_values
from langchain_openai import ChatOpenAI

env = dotenv_values(".env")
os.environ["OPENAI_API_KEY"] = env.get("OPENAI_API_KEY")

async def test_llm():
    try:
        llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
        system_prompt = "Hello, this is a test prompt."
        response = await llm.ainvoke(system_prompt)
        print("Success:", response.content)
    except Exception as e:
        print("Error:", repr(e))

asyncio.run(test_llm())
