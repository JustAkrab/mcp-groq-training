# MCP Project: a terminal AI assistant with Groq and MCP

A small chat app that runs in the terminal. It uses a Groq-hosted model to understand questions and a local [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server to answer the ones that need tools.

The project includes its own **host**, the program that connects the model and the tools. Apps like Claude Desktop normally do this job for you.

```
You (terminal)
     │
     ▼
chat.py ──── question + tool list ───▶ Groq API (model)
(host +  ◀─── "call tool X" / answer ──
 MCP client)
     │
     │ tools/list, tools/call (stdio)
     ▼
server.py (MCP server: the tools)
```

Groq never talks to the server directly. Every tool call goes through `chat.py`.

## Files

| File | What it does |
|---|---|
| `server.py` | The MCP server, built with [FastMCP](https://gofastmcp.com). It exposes two tools: `simple_add` (adds two whole numbers) and `c_time` (returns the current local date and time). |
| `chat.py` | The host. It starts `server.py` as a child process, discovers its tools, passes them to Groq, runs the tool calls Groq asks for, and sends back the results. |
| `groq_hello.py` | A one-off check that your Groq API key works. It makes a plain model call with no tools. |
| `.env` | Holds your Groq API key. Not committed. |

## Requirements

- [uv](https://docs.astral.sh/uv/) (installs Python 3.15 and the dependencies for you)
- [Node.js](https://nodejs.org) LTS, only needed to test the server with the MCP Inspector
- A free Groq API key from [console.groq.com](https://console.groq.com)

## Setup

1. Install the dependencies:
   ```
   uv sync
   ```
2. Create a file named `.env` in the project folder with one line:
   ```
   GROQ_API_KEY=gsk_your_key_here
   ```
   Create it in your editor, not with PowerShell's `echo`, which can save it in an encoding Python can't read. Never put the key in code.
3. Check the key works:
   ```
   uv run python groq_hello.py
   ```

## Usage

Run the chat from the project folder:

```
uv run python chat.py
```

Example session:

```
Connected. Tools: simple_add, c_time

You: what is 1234 plus 5678?
  [tool call]   simple_add({'a': 1234, 'b': 5678})
  [tool result] 6912
Assistant: The sum of 1234 and 5678 is 6912.

You: what time is it?
  [tool call]   c_time({})
  [tool result] 2026-11-25 01:06:44
Assistant: The current local date and time is 2026-11-25 01:06:44.
```

Type `quit`, `exit` or press Enter on an empty line to stop.

### Testing the server on its own

The MCP Inspector lets you call the tools from a browser page, without Groq:

```
npx @modelcontextprotocol/inspector uv run python server.py
```

Include the `@`. Without it, npx tries to build the Inspector from its GitHub source instead of installing the published package.

## How it works

`chat.py` does the host's four jobs:

1. **Discover:** `await mcp_client.list_tools()` asks the server which tools exist.
2. **Translate:** `to_groq_tool()` converts each MCP tool (name, description, input schema) into Groq's function-calling format.
3. **Call:** when Groq replies with a tool call, `await mcp_client.call_tool(name, args)` runs it on the server.
4. **Return:** the result is added to the conversation as a `tool` message, and Groq is asked again. This repeats until Groq answers without a tool call (at most 5 rounds per question).

Because `chat.py` never names a tool, adding a new `@mcp.tool` function to `server.py` makes it available to the model with no change to `chat.py`.

**Tool descriptions matter.** FastMCP uses each function's docstring as the tool's description, and that text is the only thing the model reads about the tool. Without a docstring, the model may skip a tool and answer on its own.

## Configuration

| Setting | Where | Default |
|---|---|---|
| Model | `MODEL` in `chat.py` and `groq_hello.py` | `openai/gpt-oss-120b` |
| Server path | `Client(Path("server.py"))` in `chat.py` | `server.py`, relative to the folder you run from |

To try another model, pick a production model that supports tool use from [Groq's model list](https://console.groq.com/docs/models). Preview models can be removed at short notice.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `KeyError: 'GROQ_API_KEY'` | `.env` is missing, misnamed (for example `.env.txt`), or not in the folder you ran from. |
| `401` / invalid API key | The key has a typo or was deleted. Create a new one in the Groq console. |
| `429` / rate limit | The free tier limits requests per minute. Wait and try again. |
| Model not found or decommissioned | Groq retired the model. Choose a current one and update `MODEL`. |
| `FileNotFoundError: Script not found` | You ran `chat.py` from another folder. Run it from the project folder. |
| `MCPError: Connection closed` | `server.py` crashed on startup. Run `uv run python server.py` on its own to see the error. |
| The model never calls a tool | Check that each tool has a clear docstring. Open the Inspector to see what the model sees. |

## Ideas for extending it

- Add a resource or prompt to the server ([FastMCP server docs](https://gofastmcp.com/docs/servers/server))
- Log tool calls with the `Context` object, to stderr or a file but never stdout, which carries the MCP messages ([FastMCP context](https://gofastmcp.com/servers/context))
- Run the server over HTTP and connect with `Client("http://127.0.0.1:8000/mcp")` ([running your server](https://gofastmcp.com/docs/deployment/running-server))
- Read how MCP fits together: [server concepts](https://modelcontextprotocol.io/docs/2026-07-28/learn/server-concepts) and [architecture](https://modelcontextprotocol.io/docs/learn/architecture)
