import asyncio
import json
import os
from pathlib import Path
from groq import AsyncGroq
from fastmcp import Client
from dotenv import load_dotenv


load_dotenv()


MODEL = "openai/gpt-oss-120b"

groq = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])


mcp_client = Client(Path("server.py"))


def to_groq_tool(tool):
    schema = getattr(tool, "input_schema", None) or getattr(tool, "inputSchema", None)
    return {
        "type" : "function",
        "function": {
            "name" : tool.name,
            "description" : tool.description or "",
            "parameters" : schema or {"type" : "object", "properties" : {}},
        },
    }


def result_to_text(result):
    if getattr(result, "data", None) is not None:
        return str(result.data)
    return "\n".join(getattr(block, "text", "") for block in result.content)


async def answer(questions, tools, messages):
    messages.append({"role": "user", "content": questions})
    for _ in range(5):
        response = await groq.chat.completions.create(
            model= MODEL,
            messages=messages,
            tools=tools,
            tool_choice= "auto"
        )
        
        
        msg = response.choices[0].message
        
        if not msg.tool_calls:
            messages.append({"role": "assistant", "content": msg.content})
            return msg.content
        
        messages.append(msg)   # remember that Groq asked for tools

        for i in msg.tool_calls:
            name = i.function.name
            args = json.loads(i.function.arguments or "{}")
            print(f"  [tool call]   {name}({args})")
            try:
                result = await mcp_client.call_tool(name, args)
                text = result_to_text(result)
            except Exception as error:
                text = f"Error: {error}"
            print(f"  [tool result] {text}")
            messages.append({
                "role": "tool",
                "tool_call_id": i.id,
                "name": name,
                "content": text,
                
            })
    return "Stopped: too many tool calls in a row."


async def main():
    async with mcp_client:
        mcp_tools = await mcp_client.list_tools()
        tools = [to_groq_tool(t) for t in mcp_tools]
        print("Connected. Tools:", ", ".join(t.name for t in mcp_tools))
        
        messages = [{"role": "system", "content": "You are a helpful assistant. Use the tools when they help."}]
        
        while True:
            question = (await asyncio.to_thread(input, "\nYou: ")).strip()
            if question.lower() in {"", "quit", "exit"}:
                break
            reply = await answer(question, tools, messages)
            print(f"Assistant: {reply}")


if __name__ == "__main__":
    asyncio.run(main())
        
    
