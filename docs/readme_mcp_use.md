# MCP-Use: Create MCP Clients and Agents

**The open source way to connect any LLM to any MCP server** and build custom MCP agents that have tool access, without using closed source or application clients.

## Overview

MCP-Use is a Python library that lets developers easily connect any LLM to tools like web browsing, file operations, and more through the Model Context Protocol (MCP).

**Key Features:**
- Easy-to-use API for creating MCP-capable agents in just 6 lines of code
- Works with any LangChain-supported LLM that supports tool calling (OpenAI, Anthropic, Groq, LLama, etc.)
- Direct HTTP connection support to MCP servers
- Dynamic server selection - agents choose the appropriate MCP server for each task
- Multi-server support - use multiple MCP servers simultaneously
- Tool access control to restrict potentially dangerous operations
- Custom agent building with LangChain adapter
- Sandboxed execution via E2B cloud infrastructure

**Supported MCP Primitives:**
- Tools
- Resources
- Prompts
- Sampling
- Elicitation
- Authentication

**Supported Transports:**
- Stdio
- SSE (Server-Sent Events)
- Streamable HTTP

---

## Installation

### Basic Installation

```bash
pip install mcp-use
```

Or install from source:

```bash
git clone https://github.com/mcp-use/mcp-use.git
cd mcp-use
pip install -e .
```

### Installing LLM Providers

MCP-Use works with various LLM providers through LangChain. Install the appropriate provider package:

```bash
# For OpenAI
pip install langchain-openai

# For Anthropic
pip install langchain-anthropic

# For Groq
pip install langchain-groq
```

**Important:** Only models with tool calling capabilities can be used with MCP-Use.

### API Keys

Add your API keys to a `.env` file:

```bash
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

---

## Quick Start

### Basic Agent Setup

```python
import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient

async def main():
    load_dotenv()

    # Create configuration dictionary
    config = {
      "mcpServers": {
        "playwright": {
          "command": "npx",
          "args": ["@playwright/mcp@latest"],
          "env": {
            "DISPLAY": ":1"
          }
        }
      }
    }

    # Create MCPClient from configuration
    client = MCPClient.from_dict(config)

    # Create LLM
    llm = ChatOpenAI(model="gpt-4o")

    # Create agent
    agent = MCPAgent(llm=llm, client=client, max_steps=30)

    # Run query
    result = await agent.run("Find the best restaurant in San Francisco")
    print(f"\nResult: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Configuration from File

You can also load configuration from a JSON file:

```python
client = MCPClient.from_config_file("browser_mcp.json")
```

Example configuration file (`browser_mcp.json`):

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"],
      "env": {
        "DISPLAY": ":1"
      }
    }
  }
}
```

---

## API Reference

### MCPClient

The `MCPClient` class manages connections to one or more MCP servers.

#### Constructor

```python
MCPClient(config: dict, sandbox: bool = False, sandbox_options: dict = None)
```

**Parameters:**
- `config`: Configuration dictionary with MCP server definitions
- `sandbox`: Enable sandboxed execution via E2B (default: False)
- `sandbox_options`: Options for sandbox configuration

#### Class Methods

##### `from_dict(config: dict) -> MCPClient`
Create client from configuration dictionary.

```python
config = {
    "mcpServers": {
        "server_name": {
            "command": "command",
            "args": ["arg1", "arg2"]
        }
    }
}
client = MCPClient.from_dict(config)
```

##### `from_config_file(path: str) -> MCPClient`
Create client from JSON configuration file.

```python
client = MCPClient.from_config_file("config.json")
```

#### Instance Methods

##### `create_all_sessions() -> None`
Create connections to all configured servers.

```python
await client.create_all_sessions()
```

##### `close_all_sessions() -> None`
Close all server connections.

```python
await client.close_all_sessions()
```

##### `get_session(server_name: str) -> Session`
Get session for a specific server.

```python
session = client.get_session("playwright")
```

#### Properties

- `sessions`: Dictionary of active server sessions

---

### MCPAgent

The `MCPAgent` class creates an LLM agent with access to MCP server tools.

#### Constructor

```python
MCPAgent(
    llm,
    client: MCPClient,
    max_steps: int = 10,
    use_server_manager: bool = False,
    disallowed_tools: list = None,
    verbose: bool = False
)
```

**Parameters:**
- `llm`: LangChain chat model with tool calling support
- `client`: MCPClient instance
- `max_steps`: Maximum reasoning steps (default: 10)
- `use_server_manager`: Enable dynamic server selection (default: False)
- `disallowed_tools`: List of tool names to restrict
- `verbose`: Enable debug output (default: False)

#### Methods

##### `run(query: str, max_steps: int = None, server_name: str = None) -> str`
Execute a query with the agent.

```python
result = await agent.run(
    "Find the best restaurant in San Francisco",
    max_steps=30,
    server_name="playwright"  # Optional: target specific server
)
```

**Parameters:**
- `query`: Query string for the agent
- `max_steps`: Override default max_steps
- `server_name`: Target specific server (optional)

**Returns:** String result from agent execution

##### `stream(query: str) -> AsyncIterator[dict]`
Stream agent output in real-time.

```python
async for chunk in agent.stream("Find nearby restaurants"):
    print(chunk["messages"], end="", flush=True)
```

**Yields:** Dictionary with keys:
- `actions`: Current actions being taken
- `steps`: Processing steps
- `messages`: Agent messages
- `output`: Final output (on last chunk only)

---

### Session

The `Session` class represents a connection to a single MCP server.

#### Methods

##### `call_tool(name: str, arguments: dict) -> ToolResult`
Call a tool directly without LLM.

```python
result = await session.call_tool(
    name="add",
    arguments={"a": 1, "b": 2}
)
print(result.content[0].text)
```

**Parameters:**
- `name`: Tool name
- `arguments`: Dictionary of tool arguments

**Returns:** ToolResult object with content

---

### LangChainAdapter

Adapter for creating custom agents using LangChain tools.

#### Methods

##### `create_tools(client: MCPClient) -> list`
Convert MCP server tools to LangChain tools.

```python
from mcp_use.adapters.langchain_adapter import LangChainAdapter

adapter = LangChainAdapter()
tools = await adapter.create_tools(client)

# Use with LangChain
llm_with_tools = llm.bind_tools(tools)
result = await llm_with_tools.ainvoke("What tools are available?")
```

---

### Sandbox Types

#### SandboxOptions

Configuration for E2B sandboxed execution.

```python
sandbox_options: SandboxOptions = {
    "api_key": os.getenv("E2B_API_KEY"),
    "sandbox_template_id": "base",
    "supergateway_command": "npx -y supergateway"
}
```

**Fields:**
- `api_key`: E2B API key (required)
- `sandbox_template_id`: Template ID (default: "base")
- `supergateway_command`: Gateway command (default: "npx -y supergateway")

---

## Configuration Guide

### Server Configuration Format

MCP servers are configured using a standard JSON format:

```json
{
  "mcpServers": {
    "server_name": {
      "command": "executable_command",
      "args": ["arg1", "arg2"],
      "env": {
        "ENV_VAR": "value"
      }
    }
  }
}
```

### HTTP Server Configuration

Connect directly to HTTP-based MCP servers:

```json
{
  "mcpServers": {
    "http_server": {
      "url": "http://localhost:8931/sse"
    }
  }
}
```

### Multi-Server Configuration

Configure multiple servers for simultaneous use:

```json
{
  "mcpServers": {
    "airbnb": {
      "command": "npx",
      "args": ["-y", "@openbnb/mcp-server-airbnb"]
    },
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"],
      "env": {
        "DISPLAY": ":1"
      }
    }
  }
}
```

---

## Advanced Features

### Streaming Agent Output

Stream agent responses in real-time for interactive applications:

```python
async def main():
    client = MCPClient.from_config_file("config.json")
    llm = ChatOpenAI(model="gpt-4o")
    agent = MCPAgent(llm=llm, client=client, max_steps=30)

    async for chunk in agent.stream("Search for jobs at nvidia"):
        print(chunk["messages"], end="", flush=True)
```

### Dynamic Server Selection

Enable intelligent server selection with the server manager:

```python
agent = MCPAgent(
    llm=ChatAnthropic(model="claude-3-5-sonnet-20240620"),
    client=client,
    use_server_manager=True  # Agent selects appropriate server
)

result = await agent.run(
    "Search for a place in Barcelona on Airbnb, "
    "then use Google to find nearby restaurants."
)
```

### Manual Server Selection

Target a specific server for a query:

```python
# Use airbnb server
result = await agent.run(
    "Search for Airbnb listings in Barcelona",
    server_name="airbnb"
)

# Use playwright server
result = await agent.run(
    "Find restaurants using Google Search",
    server_name="playwright"
)
```

### Tool Access Control

Restrict dangerous or sensitive tools:

```python
agent = MCPAgent(
    llm=ChatOpenAI(model="gpt-4"),
    client=client,
    disallowed_tools=["file_system", "network", "delete_file"]
)
```

### Direct Tool Calls

Call MCP tools programmatically without an LLM:

```python
import asyncio
from mcp_use import MCPClient

async def call_tool_example():
    config = {
        "mcpServers": {
            "everything": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-everything"],
            }
        }
    }

    client = MCPClient.from_dict(config)

    try:
        await client.create_all_sessions()
        session = client.get_session("everything")

        # Direct tool call
        result = await session.call_tool(
            name="add",
            arguments={"a": 1, "b": 2}
        )

        print(f"Result: {result.content[0].text}")  # Output: 3

    finally:
        await client.close_all_sessions()

if __name__ == "__main__":
    asyncio.run(call_tool_example())
```

### Sandboxed Execution

Run MCP servers in isolated E2B cloud environments:

```python
import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient
from mcp_use.types.sandbox import SandboxOptions

async def main():
    load_dotenv()

    server_config = {
        "mcpServers": {
            "everything": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-everything"],
            }
        }
    }

    sandbox_options: SandboxOptions = {
        "api_key": os.getenv("E2B_API_KEY"),
        "sandbox_template_id": "base",
    }

    # Create sandboxed client
    client = MCPClient(
        config=server_config,
        sandbox=True,
        sandbox_options=sandbox_options,
    )

    llm = ChatOpenAI(model="gpt-4o")
    agent = MCPAgent(llm=llm, client=client)

    result = await agent.run("Use command line tools to add 1+1")
    print(result)

    await client.close_all_sessions()

if __name__ == "__main__":
    asyncio.run(main())
```

### Building Custom Agents

Use the LangChain adapter to build custom agent architectures:

```python
import asyncio
from langchain_openai import ChatOpenAI
from mcp_use.client import MCPClient
from mcp_use.adapters.langchain_adapter import LangChainAdapter
from dotenv import load_dotenv

load_dotenv()

async def main():
    # Initialize MCP client
    client = MCPClient.from_config_file("browser_mcp.json")
    llm = ChatOpenAI(model="gpt-4o")

    # Create adapter and get tools
    adapter = LangChainAdapter()
    tools = await adapter.create_tools(client)

    # Create custom LangChain agent
    llm_with_tools = llm.bind_tools(tools)
    result = await llm_with_tools.ainvoke("What tools do you have available?")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Cookbook: Common Patterns

### Web Browsing with Playwright

```python
import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient

async def main():
    load_dotenv()

    client = MCPClient.from_config_file("browser_mcp.json")
    llm = ChatOpenAI(model="gpt-4o")
    agent = MCPAgent(llm=llm, client=client, max_steps=30)

    result = await agent.run(
        "Find the best restaurant in San Francisco USING GOOGLE SEARCH",
        max_steps=30,
    )
    print(f"\nResult: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Airbnb Search

```python
import asyncio
import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from mcp_use import MCPAgent, MCPClient

async def run_airbnb_example():
    load_dotenv()

    client = MCPClient.from_config_file("airbnb_mcp.json")
    llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")
    agent = MCPAgent(llm=llm, client=client, max_steps=30)

    try:
        result = await agent.run(
            "Find me a nice place to stay in Barcelona for 2 adults "
            "for a week in August. I prefer places with a pool and "
            "good reviews. Show me the top 3 options.",
            max_steps=30,
        )
        print(f"\nResult: {result}")
    finally:
        if client.sessions:
            await client.close_all_sessions()

if __name__ == "__main__":
    asyncio.run(run_airbnb_example())
```

Configuration file (`airbnb_mcp.json`):

```json
{
  "mcpServers": {
    "airbnb": {
      "command": "npx",
      "args": ["-y", "@openbnb/mcp-server-airbnb"]
    }
  }
}
```

### Blender 3D Creation

```python
import asyncio
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from mcp_use import MCPAgent, MCPClient

async def run_blender_example():
    load_dotenv()

    config = {
        "mcpServers": {
            "blender": {
                "command": "uvx",
                "args": ["blender-mcp"]
            }
        }
    }

    client = MCPClient.from_dict(config)
    llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")
    agent = MCPAgent(llm=llm, client=client, max_steps=30)

    try:
        result = await agent.run(
            "Create an inflatable cube with soft material and a plane as ground.",
            max_steps=30,
        )
        print(f"\nResult: {result}")
    finally:
        if client.sessions:
            await client.close_all_sessions()

if __name__ == "__main__":
    asyncio.run(run_blender_example())
```

### Multi-Server Workflow

```python
import asyncio
from mcp_use import MCPClient, MCPAgent
from langchain_anthropic import ChatAnthropic

async def main():
    # Multi-server configuration
    config = {
        "mcpServers": {
            "airbnb": {
                "command": "npx",
                "args": ["-y", "@openbnb/mcp-server-airbnb"]
            },
            "playwright": {
                "command": "npx",
                "args": ["@playwright/mcp@latest"],
                "env": {"DISPLAY": ":1"}
            }
        }
    }

    client = MCPClient.from_dict(config)

    agent = MCPAgent(
        llm=ChatAnthropic(model="claude-3-5-sonnet-20240620"),
        client=client,
        use_server_manager=True  # Automatic server selection
    )

    try:
        # Agent automatically uses both servers
        result = await agent.run(
            "Search for a nice place to stay in Barcelona on Airbnb, "
            "then use Google to find nearby restaurants and attractions."
        )
        print(result)
    finally:
        await client.close_all_sessions()

if __name__ == "__main__":
    asyncio.run(main())
```

### HTTP Connection Example

```python
import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient

async def main():
    load_dotenv()

    config = {
        "mcpServers": {
            "http": {
                "url": "http://localhost:8931/sse"
            }
        }
    }

    client = MCPClient.from_dict(config)
    llm = ChatOpenAI(model="gpt-4o")
    agent = MCPAgent(llm=llm, client=client, max_steps=30)

    result = await agent.run(
        "Find the best restaurant in San Francisco USING GOOGLE SEARCH",
        max_steps=30,
    )
    print(f"\nResult: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Debugging

### Enable Debug Mode

MCP-Use provides built-in debug logging at two levels:

**Level 1 - INFO:**
```bash
DEBUG=1 python your_script.py
# or
export MCP_USE_DEBUG=1
```

**Level 2 - DEBUG (Full Verbose):**
```bash
DEBUG=2 python your_script.py
# or
export MCP_USE_DEBUG=2
```

### Programmatic Debug Control

```python
import mcp_use

# Set debug level
mcp_use.set_debug(1)  # INFO level
# or
mcp_use.set_debug(2)  # DEBUG level (full verbose)
```

### Agent-Specific Verbosity

Enable verbose output only for the agent:

```python
agent = MCPAgent(
    llm=your_llm,
    client=your_client,
    verbose=True  # Agent debug messages only
)
```

---

## Requirements

- Python 3.11+
- LangChain-compatible LLM with tool calling support
- MCP server implementations

---

## License

MIT

---

## TypeScript Version

For TypeScript/JavaScript implementation, see [mcp-use-ts](https://github.com/mcp-use/mcp-use-ts)
