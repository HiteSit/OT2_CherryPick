# FastMCP: The Fast, Pythonic Way to Build MCP Servers and Clients

**The standard framework for building production-ready MCP applications.**

*Made with ☕️ by [Prefect](https://www.prefect.io/)*

## Overview

FastMCP is the fastest path from idea to production for building Model Context Protocol (MCP) applications. It provides a high-level, Pythonic interface with enterprise authentication, deployment tools, and a complete ecosystem built in.

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io) is a standardized way to provide context and tools to LLMs - think of it as "the USB-C port for AI" or an API specifically designed for LLM interactions.

**Key Features:**
- 🚀 **Fast:** High-level interface with minimal boilerplate
- 🍀 **Simple:** Build MCP servers by decorating Python functions
- 🐍 **Pythonic:** Feels natural to Python developers
- 🔍 **Complete:** Enterprise auth, deployment tools, testing frameworks, client libraries

---

## Installation

```bash
# Recommended: Install with uv
uv pip install fastmcp

# Or with pip
pip install fastmcp
```

---

## Quick Start

### Basic Server

```python
# server.py
from fastmcp import FastMCP

mcp = FastMCP("Demo 🚀")

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

if __name__ == "__main__":
    mcp.run()
```

Run the server:

```bash
fastmcp run server.py
```

---

## Core Concepts

### The FastMCP Server

The central object representing your MCP application. It holds tools, resources, prompts, and manages connections.

```python
from fastmcp import FastMCP

mcp = FastMCP(name="MyAssistantServer")
```

### Tools

Tools allow LLMs to perform actions by executing your Python functions. FastMCP handles schema generation from type hints and docstrings.

```python
@mcp.tool
def multiply(a: float, b: float) -> float:
    """Multiplies two numbers."""
    return a * b
```

### Resources & Templates

Resources expose read-only data sources. Use URI templates with `{placeholders}` for dynamic resources.

```python
# Static resource
@mcp.resource("config://version")
def get_version():
    return "2.0.1"

# Dynamic resource template
@mcp.resource("users://{user_id}/profile")
def get_profile(user_id: int):
    return {"name": f"User {user_id}", "status": "active"}
```

### Prompts

Prompts define reusable message templates to guide LLM interactions.

```python
@mcp.prompt
def summarize_request(text: str) -> str:
    """Generate a prompt asking for a summary."""
    return f"Please summarize the following text:\n\n{text}"
```

### Context

Access MCP session capabilities within your functions via the `Context` parameter.

```python
from fastmcp import FastMCP, Context

mcp = FastMCP("My Server")

@mcp.tool
async def process_data(uri: str, ctx: Context):
    # Log a message
    await ctx.info(f"Processing {uri}...")

    # Read a resource
    data = await ctx.read_resource(uri)

    # Ask client LLM
    summary = await ctx.sample(f"Summarize: {data.content[:500]}")

    return summary.text
```

### MCP Clients

Interact with any MCP server programmatically using `fastmcp.Client`.

```python
from fastmcp import Client

async def main():
    # Connect via stdio
    async with Client("my_server.py") as client:
        tools = await client.list_tools()
        result = await client.call_tool("add", {"a": 5, "b": 3})
        print(result.content[0].text)

    # Connect via SSE
    async with Client("http://localhost:8000/sse") as client:
        pass

    # In-memory testing
    async with Client(mcp) as client:
        pass
```

---

## API Reference

### FastMCP Class

The main server class for building MCP applications.

#### Constructor

```python
FastMCP(
    name: str,
    instructions: str = None,
    auth: AuthProvider = None,
    dependencies: list = None
)
```

**Parameters:**
- `name`: Server name (required)
- `instructions`: Server description/instructions
- `auth`: Authentication provider (optional)
- `dependencies`: Dependency injection list (optional)

#### Decorators

##### `@mcp.tool`
Define a tool that LLMs can execute.

```python
@mcp.tool
def tool_name(param: type, ctx: Context = None) -> return_type:
    """Tool description."""
    return result
```

**Decorator Parameters:**
- `name`: Custom tool name (optional)
- `description`: Tool description (optional)
- `tags`: Set of tags for categorization (optional)
- `enabled`: Enable/disable tool (default: True)
- `meta`: Additional metadata dictionary (optional)

**Supported Parameter Types:**
- Basic: `str`, `int`, `float`, `bool`
- Collections: `list`, `dict`, `set`, `tuple`
- Date/Time: `datetime`, `date`, `timedelta`
- Advanced: `Union`, `Optional`, `Enum`, `Literal`
- Pydantic models
- Binary: `bytes`
- Other: `Path`, `UUID`

**Return Value Handling:**
- Automatically converts return values to appropriate content blocks
- Supports JSON-serializable objects
- Can use `ToolResult` for full control
- Supports media types via helper classes

##### `@mcp.resource`
Define a resource that exposes data.

```python
@mcp.resource("resource://uri")
def resource_name(ctx: Context = None) -> return_type:
    """Resource description."""
    return data

# Dynamic resource with template
@mcp.resource("users://{user_id}/data")
def get_user_data(user_id: int) -> dict:
    return {"id": user_id, "name": "User"}
```

**Decorator Parameters:**
- `uri`: Resource URI (required)
- `name`: Human-readable name (optional)
- `description`: Resource explanation (optional)
- `mime_type`: Content type (optional)
- `tags`: Categorization set (optional)
- `enabled`: Resource availability (default: True)
- `annotations`: Metadata about behavior (optional)

**Return Value Types:**
- `str`: Sent as plain text
- `dict`/`list`: Serialized to JSON
- `bytes`: Base64 encoded
- `None`: Empty content

##### `@mcp.prompt`
Define a reusable prompt template.

```python
@mcp.prompt
def prompt_name(param: str) -> str:
    """Prompt description."""
    return f"Template with {param}"
```

**Decorator Parameters:**
- `name`: Custom prompt identifier (optional)
- `description`: Prompt explanation (optional)
- `tags`: Categorization set (optional)
- `enabled`: Toggle availability (default: True)
- `meta`: Additional metadata (optional)

#### Methods

##### `run()`
Start the MCP server.

```python
mcp.run(
    transport: str = "stdio",
    host: str = "127.0.0.1",
    port: int = 8000,
    path: str = "/mcp"
)
```

**Parameters:**
- `transport`: Transport type - "stdio", "http", or "sse" (default: "stdio")
- `host`: Host address for HTTP/SSE (default: "127.0.0.1")
- `port`: Port for HTTP/SSE (default: 8000)
- `path`: Path for HTTP transport (default: "/mcp")

##### `mount()`
Mount another FastMCP server (live link).

```python
parent_mcp.mount(
    child_mcp,
    prefix: str = None
)
```

##### `import_server()`
Import another FastMCP server (static copy).

```python
parent_mcp.import_server(
    other_mcp,
    prefix: str = None
)
```

#### Class Methods

##### `from_openapi()`
Create FastMCP server from OpenAPI specification.

```python
mcp = FastMCP.from_openapi(
    spec: dict | str,
    name: str = "OpenAPI Server"
)
```

##### `from_fastapi()`
Create FastMCP server from FastAPI application.

```python
from fastapi import FastAPI

app = FastAPI()

mcp = FastMCP.from_fastapi(
    app,
    name: str = "FastAPI Server"
)
```

##### `as_proxy()`
Create a proxy server for another MCP server.

```python
proxy_mcp = FastMCP.as_proxy(
    target: str | FastMCP,
    name: str = "Proxy Server"
)
```

---

### Context Class

Provides access to MCP session capabilities within tools, resources, and prompts.

#### Logging Methods

```python
async def debug(message: str) -> None
async def info(message: str) -> None
async def warning(message: str) -> None
async def error(message: str) -> None
```

Send log messages of different severity levels to the MCP client.

```python
@mcp.tool
async def process(ctx: Context):
    await ctx.info("Starting processing...")
    await ctx.debug("Debug information")
    await ctx.warning("Warning message")
    await ctx.error("Error occurred")
```

#### Progress Reporting

```python
async def report_progress(progress: int, total: int) -> None
```

Update clients on long-running operation progress.

```python
@mcp.tool
async def long_task(ctx: Context):
    for i in range(100):
        await ctx.report_progress(i, 100)
        # Do work...
```

#### Resource Access

```python
async def read_resource(uri: str | AnyUrl) -> list[ReadResourceContents]
```

Read data from resources registered with the server.

```python
@mcp.tool
async def use_resource(uri: str, ctx: Context):
    data = await ctx.read_resource(uri)
    return data.content[0].text
```

#### LLM Sampling

```python
async def sample(prompt: str, temperature: float = 0.7) -> str
```

Request text generation from the client's language model.

```python
@mcp.tool
async def analyze(text: str, ctx: Context):
    result = await ctx.sample(f"Analyze this: {text}")
    return result
```

#### User Elicitation

```python
async def elicit(prompt: str, response_type: Type) -> ElicitationResult
```

Request structured input from clients during tool execution.

```python
@mcp.tool
async def interactive_tool(ctx: Context):
    response = await ctx.elicit("Enter your name:", str)
    return f"Hello, {response}!"
```

#### State Management

```python
def set_state(key: str, value: Any) -> None
def get_state(key: str) -> Any
```

Store and retrieve data across middleware and tool calls.

```python
@mcp.tool
def store_data(key: str, value: str, ctx: Context):
    ctx.set_state(key, value)

@mcp.tool
def retrieve_data(key: str, ctx: Context):
    return ctx.get_state(key)
```

#### Change Notifications

```python
async def send_tool_list_changed() -> None
async def send_resource_list_changed() -> None
async def send_prompt_list_changed() -> None
```

Manually trigger component list change notifications.

#### Properties

- `request_id`: Unique ID for the current MCP request
- `client_id`: ID of the client making the request
- `session_id`: MCP session ID
- `fastmcp`: Access to the underlying FastMCP server instance

---

### Client Class

Interact with MCP servers programmatically.

#### Constructor

```python
Client(
    transport,
    log_handler=None,
    progress_handler=None,
    sampling_handler=None,
    roots=None,
    timeout=30.0,
    auth=None
)
```

**Parameters:**
- `transport`: Transport specification (FastMCP instance, file path, URL, or config dict)
- `log_handler`: Callback for server log messages
- `progress_handler`: Callback for progress updates
- `sampling_handler`: Callback for LLM sampling requests
- `roots`: Local context to provide to servers
- `timeout`: Default request timeout in seconds (default: 30.0)
- `auth`: Authentication mode ("oauth" or provider instance)

#### Connection Methods

```python
async with client:
    # Use client
    pass

# Or manual control
await client.connect()
await client.disconnect()

# Check status
is_connected = client.is_connected()

# Test connection
await client.ping()
```

#### Tool Methods

##### `list_tools()`
Retrieve available server tools.

```python
tools = await client.list_tools()
for tool in tools:
    print(f"{tool.name}: {tool.description}")
```

##### `call_tool()`
Execute a server-side tool.

```python
result = await client.call_tool(
    tool_name: str,
    arguments: dict
)
print(result.content[0].text)
```

#### Resource Methods

##### `list_resources()`
List available resources.

```python
resources = await client.list_resources()
for resource in resources:
    print(f"{resource.uri}: {resource.name}")
```

##### `read_resource()`
Read a specific resource.

```python
content = await client.read_resource(resource_uri: str)
print(content[0].text)
```

#### Prompt Methods

##### `list_prompts()`
Retrieve available prompts.

```python
prompts = await client.list_prompts()
```

##### `get_prompt()`
Render a prompt template.

```python
result = await client.get_prompt(
    prompt_name: str,
    arguments: dict
)
```

#### Supported Transports

1. **In-memory**: Pass `FastMCP` instance for testing
2. **File-based**: Pass path to `.py` or `.js` script
3. **HTTP/HTTPS**: Pass URL string
4. **Configuration**: Pass config dictionary for multiple servers

---

### Authentication

FastMCP provides comprehensive enterprise-grade authentication.

#### Built-in OAuth Providers

- GoogleProvider
- GitHubProvider
- AzureProvider (Microsoft Azure)
- Auth0Provider
- WorkOSProvider
- DescopeProvider
- JWTProvider
- APIKeyProvider

#### Server-Side Authentication

Protect your server with OAuth:

```python
from fastmcp import FastMCP
from fastmcp.server.auth import GoogleProvider

auth = GoogleProvider(
    client_id="your_client_id",
    client_secret="your_client_secret",
    base_url="https://myserver.com"
)

mcp = FastMCP("Protected Server", auth=auth)
```

#### Client-Side Authentication

Connect to protected servers:

```python
from fastmcp import Client

# Zero-config OAuth (automatic browser flow)
async with Client("https://protected-server.com/mcp", auth="oauth") as client:
    result = await client.call_tool("protected_tool")
```

#### Provider Examples

**GitHub Provider:**

```python
from fastmcp.server.auth import GitHubProvider

auth = GitHubProvider(
    client_id="github_client_id",
    client_secret="github_client_secret",
    base_url="https://myserver.com"
)
```

**Azure Provider:**

```python
from fastmcp.server.auth import AzureProvider

auth = AzureProvider(
    client_id="azure_client_id",
    client_secret="azure_client_secret",
    tenant_id="azure_tenant_id",
    base_url="https://myserver.com"
)
```

**Auth0 Provider:**

```python
from fastmcp.server.auth import Auth0Provider

auth = Auth0Provider(
    client_id="auth0_client_id",
    client_secret="auth0_client_secret",
    domain="your-domain.auth0.com",
    base_url="https://myserver.com"
)
```

**WorkOS Provider (SSO):**

```python
from fastmcp.server.auth import WorkOSProvider

auth = WorkOSProvider(
    client_id="workos_client_id",
    api_key="workos_api_key",
    base_url="https://myserver.com"
)
```

**API Key Provider:**

```python
from fastmcp.server.auth import APIKeyProvider

auth = APIKeyProvider(
    valid_keys={"key1", "key2", "key3"}
)
```

**JWT Provider:**

```python
from fastmcp.server.auth import JWTProvider

auth = JWTProvider(
    secret="your_jwt_secret",
    algorithm="HS256"
)
```

---

## Advanced Features

### Proxy Servers

Create a server that acts as an intermediary for another MCP server:

```python
from fastmcp import FastMCP

# Proxy a remote server
proxy = FastMCP.as_proxy(
    "https://remote-server.com/mcp",
    name="Remote Proxy"
)

# Proxy a local server
local_server = FastMCP("Local")
proxy = FastMCP.as_proxy(local_server, name="Local Proxy")

proxy.run(transport="http", port=8000)
```

### Server Composition

Build modular applications by combining multiple servers:

```python
from fastmcp import FastMCP

# Create sub-servers
math_server = FastMCP("Math")

@math_server.tool
def add(a: int, b: int) -> int:
    return a + b

text_server = FastMCP("Text")

@text_server.tool
def uppercase(text: str) -> str:
    return text.upper()

# Compose into main server
main = FastMCP("Main Server")
main.mount(math_server, prefix="math")
main.mount(text_server, prefix="text")

# Tools available as: math_add, text_uppercase
main.run()
```

### OpenAPI Integration

Generate FastMCP server from OpenAPI specification:

```python
from fastmcp import FastMCP

# From OpenAPI spec
mcp = FastMCP.from_openapi(
    "https://api.example.com/openapi.json",
    name="API Server"
)

mcp.run()
```

### FastAPI Integration

Convert FastAPI application to MCP server:

```python
from fastapi import FastAPI
from fastmcp import FastMCP

app = FastAPI()

@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}

# Convert to MCP server
mcp = FastMCP.from_fastapi(app, name="FastAPI Server")
mcp.run()
```

---

## Transport Protocols

### STDIO (Default)

Best for local tools and command-line scripts:

```python
mcp.run(transport="stdio")  # Default
```

### Streamable HTTP

Recommended for web deployments:

```python
mcp.run(
    transport="http",
    host="0.0.0.0",
    port=8000,
    path="/mcp"
)
```

### SSE (Server-Sent Events)

For compatibility with existing SSE clients:

```python
mcp.run(
    transport="sse",
    host="0.0.0.0",
    port=8000
)
```

---

## Deployment

FastMCP servers can be deployed in three ways: local development, self-hosted production, and FastMCP Cloud managed hosting. Each approach offers different tradeoffs between simplicity, control, and operational overhead.

---

### Local Development

The fastest way to run and test your server locally:

```bash
fastmcp run server.py
```

**CLI Features:**
- Automatic dependency management via `uv`
- Python version specification support
- Command-line argument passing (after `--`)
- Development mode with MCP Inspector integration
- Hot reloading during development

**With specific Python version:**
```bash
fastmcp run server.py --python 3.12
```

**With additional dependencies:**
```bash
fastmcp run server.py --with httpx --with pandas
```

**With requirements file:**
```bash
fastmcp run server.py --requirements requirements.txt
```

**Pass arguments to your server:**
```bash
fastmcp run server.py -- --debug --port 9000
```

---

### Server Configuration (fastmcp.json)

FastMCP uses `fastmcp.json` for declarative project configuration. This file is organized around three key sections: **source**, **environment**, and **deployment**.

#### Configuration Structure

```json
{
  "source": {
    "type": "filesystem",
    "path": "./server.py",
    "entrypoint": "mcp"
  },
  "environment": {
    "python": ">=3.10",
    "dependencies": [
      "httpx>=0.24.0",
      "pandas",
      "numpy>=1.24"
    ]
  },
  "deployment": {
    "transport": "http",
    "host": "0.0.0.0",
    "port": 8000,
    "path": "/mcp/",
    "log_level": "INFO",
    "env": {
      "DATABASE_URL": "${DATABASE_URL}",
      "API_KEY": "${API_KEY}",
      "DEBUG": "false"
    }
  }
}
```

#### Source Configuration

Specifies where your server code lives.

**Fields:**
- `type` (optional): Source type - currently only `"filesystem"` supported (future: Git repos, cloud-hosted)
- `path` (required): Path to Python file containing your server
- `entrypoint` (optional): Name of server instance or factory function
  - Defaults to auto-detection: searches for `mcp`, `server`, or `app`

**Example:**
```json
{
  "source": {
    "path": "./src/my_server.py",
    "entrypoint": "create_server"
  }
}
```

#### Environment Configuration

Manages build-time dependencies and Python environment setup using `uv`.

**Fields:**
- `python` (optional): Python version constraint
  - Examples: `">=3.10"`, `"3.12"`, `">=3.10,<3.13"`
- `dependencies` (optional): List of pip packages with optional version specifiers
  - Examples: `["httpx>=0.24.0", "pandas", "numpy>=1.24"]`
- `requirements` (optional): Path to requirements.txt file
  - Example: `"./requirements.txt"`
- `project` (optional): Path to directory containing pyproject.toml
  - Example: `"./"`
- `editable` (optional): List of packages installed in editable mode for local development
  - Example: `["./local-package"]`

**Example with requirements.txt:**
```json
{
  "environment": {
    "python": "3.12",
    "requirements": "./requirements.txt"
  }
}
```

**Example with pyproject.toml:**
```json
{
  "environment": {
    "project": "./",
    "python": ">=3.10"
  }
}
```

#### Deployment Configuration

Controls runtime behavior and server execution.

**Fields:**
- `transport` (optional): Communication protocol
  - Options: `"stdio"` (default), `"http"`, `"sse"` (deprecated)
- `host` (optional): Network interface to bind to
  - Default: `"127.0.0.1"`
  - Use `"0.0.0.0"` for external access
- `port` (optional): HTTP port number
  - Default: `3000`
- `path` (optional): URL endpoint path for MCP
  - Default: `"/mcp/"`
- `log_level` (optional): Logging verbosity
  - Options: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"`
- `env` (optional): Environment variables with interpolation support
  - Supports `${VAR_NAME}` syntax for runtime substitution
- `cwd` (optional): Working directory for the process
- `args` (optional): Command-line arguments passed to the server

**Example production configuration:**
```json
{
  "deployment": {
    "transport": "http",
    "host": "0.0.0.0",
    "port": 8000,
    "log_level": "WARNING",
    "env": {
      "DATABASE_URL": "${DATABASE_URL}",
      "REDIS_URL": "${REDIS_URL}",
      "API_KEY": "${API_KEY}",
      "ENVIRONMENT": "production"
    }
  }
}
```

#### Environment Variable Interpolation

The `env` field supports dynamic variable substitution using `${VAR_NAME}` syntax. This enables secure configuration across different deployment environments without hardcoding credentials.

**How it works:**
- Variables are resolved at runtime from the system environment
- Unmatched placeholders remain unchanged
- Useful for secrets, connection strings, and environment-specific settings

**Example:**
```json
{
  "deployment": {
    "env": {
      "DATABASE_URL": "${DATABASE_URL}",
      "API_KEY": "${API_KEY}",
      "LOG_LEVEL": "${LOG_LEVEL:-INFO}"
    }
  }
}
```

Then set environment variables before running:
```bash
export DATABASE_URL="postgresql://localhost/mydb"
export API_KEY="secret-key-here"
fastmcp run server.py
```

---

### Self-Hosted Deployment

Self-hosting provides maximum control over infrastructure, security, and performance. FastMCP supports two deployment approaches: **Direct HTTP Server** (simple) and **ASGI Application** (production).

#### Direct HTTP Server (Simple)

The built-in `run()` method handles all server configuration automatically. Ideal for standalone MCP servers without additional complexity.

**Basic HTTP server:**
```python
# server.py
from fastmcp import FastMCP

mcp = FastMCP("Production Server")

@mcp.tool
def hello(name: str) -> str:
    return f"Hello, {name}!"

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000,
        path="/mcp/"
    )
```

**Run directly:**
```bash
uv run python server.py
```

**Custom endpoint path:**
```python
mcp.run(
    transport="http",
    host="0.0.0.0",
    port=8000,
    path="/api/mcp/"  # Access at http://host:8000/api/mcp/
)
```

#### ASGI Application (Production)

For production environments, create an ASGI application to leverage multiple workers, custom middleware, monitoring, and standard ASGI tooling.

**Create ASGI app:**
```python
# server.py
from fastmcp import FastMCP

mcp = FastMCP("Production Server")

@mcp.tool
def process_data(data: str) -> dict:
    """Process incoming data."""
    return {"processed": data.upper(), "length": len(data)}

# Create ASGI application
app = mcp.http_app()
```

**Run with Uvicorn (single worker):**
```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

**Run with Uvicorn (multiple workers for concurrency):**
```bash
# Install uvicorn with standard extras for better performance
pip install uvicorn[standard]

# Run with 4 worker processes
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
```

**Run with Gunicorn + Uvicorn workers:**
```bash
gunicorn server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

**Run with Hypercorn:**
```bash
hypercorn server:app --bind 0.0.0.0:8000 --workers 4
```

#### Authentication (Highly Recommended)

**Why authentication matters:** Remote MCP servers expose tools and resources over the network. Many LLM clients require authentication for remote connections. FastMCP supports multiple authentication strategies.

**API Key Authentication:**
```python
from fastmcp import FastMCP
from fastmcp.server.auth import APIKeyProvider

auth = APIKeyProvider(
    valid_keys={"key1", "key2", "key3"}
)

mcp = FastMCP("Secured Server", auth=auth)
```

**JWT Authentication:**
```python
from fastmcp.server.auth import JWTProvider

auth = JWTProvider(
    secret="your-secret-key",
    algorithm="HS256"
)

mcp = FastMCP("JWT Secured Server", auth=auth)
```

**OAuth (Google, GitHub, Azure, etc.):**
```python
from fastmcp.server.auth import GoogleProvider

auth = GoogleProvider(
    client_id="your_client_id",
    client_secret="your_client_secret",
    base_url="https://yourserver.com"
)

mcp = FastMCP("OAuth Secured Server", auth=auth)
```

**Environment variable best practice:**
```python
import os
from fastmcp.server.auth import APIKeyProvider

auth = APIKeyProvider(
    valid_keys={
        os.environ.get("API_KEY_1"),
        os.environ.get("API_KEY_2")
    }
)
```

#### Health Check Endpoints

Add custom health check routes for monitoring and load balancer integration:

```python
from fastmcp import FastMCP

mcp = FastMCP("Production Server")

@mcp.custom_route("/health", methods=["GET"])
async def health_check():
    """Health check endpoint for load balancers."""
    return {"status": "healthy", "version": "1.0.0"}

@mcp.custom_route("/status", methods=["GET"])
async def status():
    """Detailed status information."""
    return {
        "status": "operational",
        "tools": len(mcp.list_tools()),
        "resources": len(mcp.list_resources())
    }
```

#### Hosting Infrastructure Options

FastMCP servers can deploy on any infrastructure supporting Python 3.10+ and HTTP port exposure:

**Cloud Virtual Machines:**
- AWS EC2
- Google Compute Engine
- Azure Virtual Machines
- DigitalOcean Droplets
- Linode Compute Instances

**Container Platforms:**
- Google Cloud Run
- AWS ECS/Fargate
- Azure Container Instances
- Docker Swarm

**Platform-as-a-Service:**
- Railway
- Render
- Vercel (with serverless functions)
- Fly.io
- Heroku

**Orchestration:**
- Kubernetes clusters (any managed service)
- Docker Compose
- Nomad

**Edge Platforms:**
- Cloudflare Workers (Python support via Pyodide)

#### Docker Deployment

**Dockerfile example:**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv for dependency management
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run server
CMD ["uv", "run", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Docker Compose example:**
```yaml
version: '3.8'

services:
  fastmcp-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - API_KEY=${API_KEY}
      - LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Build and run:**
```bash
docker build -t my-fastmcp-server .
docker run -p 8000:8000 -e API_KEY=secret my-fastmcp-server
```

#### Kubernetes Deployment

**Deployment manifest:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastmcp-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastmcp-server
  template:
    metadata:
      labels:
        app: fastmcp-server
    spec:
      containers:
      - name: server
        image: my-fastmcp-server:latest
        ports:
        - containerPort: 8000
        env:
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: fastmcp-secrets
              key: api-key
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: fastmcp-service
spec:
  selector:
    app: fastmcp-server
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

#### Production Best Practices

**Security:**
- Always use authentication for remote servers
- Store secrets in environment variables or secret managers (AWS Secrets Manager, HashiCorp Vault)
- Use HTTPS/TLS termination (reverse proxy or load balancer)
- Implement rate limiting for public endpoints
- Regularly update dependencies

**Performance:**
- Use multiple workers for concurrent request handling
- Install uvicorn with standard extras: `pip install uvicorn[standard]`
- Enable HTTP/2 support where possible
- Configure appropriate timeouts
- Use connection pooling for databases

**Monitoring:**
- Implement health check endpoints
- Log errors and performance metrics
- Use application performance monitoring (APM) tools
- Set up alerts for failures and degraded performance
- Track resource usage (CPU, memory, network)

**Reliability:**
- Use process managers (systemd, supervisor) for automatic restarts
- Configure graceful shutdown handling
- Implement circuit breakers for external dependencies
- Set up horizontal scaling with load balancers
- Use container orchestration for automatic failover

---

### FastMCP Cloud (Managed Hosting)

FastMCP Cloud provides instant deployment with zero infrastructure management. The platform automatically builds, deploys, and hosts your server with continuous deployment from GitHub.

**Current Status:** Completely free during beta period with new features released weekly.

#### Prerequisites

- GitHub account (required for authentication)
- GitHub repository (public or private) containing FastMCP server
- At least one Python file with a FastMCP server instance
- Dependencies defined in `requirements.txt` or `pyproject.toml`

#### Deployment Process

**1. Sign Up**
- Navigate to [fastmcp.cloud](https://fastmcp.cloud)
- Sign in with GitHub credentials
- Authorize FastMCP Cloud to access your repositories

**2. Create Project**
Configure your deployment:
- **Project name**: Unique identifier (becomes part of your URL)
- **Repository**: Select GitHub repository containing your server
- **Python entrypoint**: Specify the file containing your FastMCP server
  - Example: `server.py`, `src/mcp_server.py`
- **Entrypoint variable**: Name of server instance (auto-detected if not specified)
  - Defaults to searching for: `mcp`, `server`, or `app`
- **Authentication**: Configure authentication settings (API keys, OAuth, etc.)

**Automatic dependency detection:**
FastMCP Cloud automatically detects Python dependencies from:
- `requirements.txt` (pip format)
- `pyproject.toml` (Poetry, PDM, uv, setuptools formats)

**3. Deploy**
FastMCP Cloud automatically:
- Clones your repository
- Detects and installs dependencies
- Builds the server
- Deploys to unique URL: `https://your-project-name.fastmcp.app/mcp`
- Provides instant connection instructions for LLM clients

**4. Connect**
Access your deployed server:
- **URL format**: `https://your-project-name.fastmcp.app/mcp`
- **LLM client integration**: Copy-paste connection details for Claude, Cursor, or other MCP clients
- **API access**: Use FastMCP Client library to connect programmatically

#### Key Features

**Continuous Deployment:**
- Automatically redeploys when changes push to main branch
- Zero-downtime deployments
- Build logs available in dashboard

**Pull Request Deployments:**
- Unique preview URL for each PR: `https://pr-123-your-project-name.fastmcp.app/mcp`
- Test changes before merging
- Automatic cleanup when PR closes

**Version Compatibility:**
- Supports both FastMCP 2.0 and FastMCP 1.0 servers
- Automatic version detection
- Migration assistance available

**Instant Connections:**
- Pre-configured connection snippets for popular LLM clients
- One-click integration for Claude Desktop
- WebSocket and HTTP transport support

**Dashboard Features:**
- Real-time deployment status
- Build logs and error messages
- Traffic and usage metrics (coming soon)
- Environment variable management
- Authentication configuration

#### Example Deployment

**Minimal server.py:**
```python
from fastmcp import FastMCP

mcp = FastMCP("My Cloud Server")

@mcp.tool
def greet(name: str) -> str:
    """Greet a person by name."""
    return f"Hello, {name}!"

# Note: Do NOT include if __name__ == "__main__" block
# FastMCP Cloud ignores these blocks during deployment
```

**requirements.txt:**
```
fastmcp>=2.0.0
httpx>=0.24.0
```

**Push to GitHub:**
```bash
git add server.py requirements.txt
git commit -m "Add FastMCP server"
git push origin main
```

**Deploy on FastMCP Cloud:**
1. Go to [fastmcp.cloud](https://fastmcp.cloud)
2. Click "New Project"
3. Select repository
4. Set entrypoint: `server.py`
5. Click "Deploy"

**Access deployed server:**
- URL: `https://my-cloud-server.fastmcp.app/mcp`
- Connect with Claude Desktop, Cursor, or programmatically

#### Environment Variables and Secrets

Configure secrets and environment variables through the FastMCP Cloud dashboard:

**In Dashboard:**
1. Navigate to project settings
2. Add environment variables:
   - `DATABASE_URL`: `postgresql://...`
   - `API_KEY`: `secret-key-here`
   - `DEBUG`: `false`
3. Variables are securely encrypted and injected at runtime

**In code:**
```python
import os
from fastmcp import FastMCP

mcp = FastMCP("Secure Server")

DATABASE_URL = os.environ.get("DATABASE_URL")
API_KEY = os.environ.get("API_KEY")

@mcp.tool
def query_database(query: str) -> dict:
    """Execute database query."""
    # Use DATABASE_URL here
    return {"result": "data"}
```

#### Limitations and Considerations

**Current Limitations:**
- Requires GitHub repository (no direct file uploads)
- Must contain Python file with FastMCP server instance
- `if __name__ == "__main__"` blocks are ignored during deployment
- Cold start latency for inactive servers (typical of serverless platforms)
- Resource limits apply during beta (check documentation for current limits)

**Best Practices for Cloud Deployment:**
- Keep dependencies minimal to reduce build time
- Use environment variables for all secrets and configuration
- Test locally before pushing to GitHub
- Monitor build logs for dependency conflicts
- Use PR deployments to test breaking changes

#### Connecting LLM Clients

**Claude Desktop:**
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "my-server": {
      "url": "https://your-project-name.fastmcp.app/mcp"
    }
  }
}
```

**Cursor:**
Add to Cursor settings:
```json
{
  "mcp": {
    "servers": {
      "my-server": {
        "url": "https://your-project-name.fastmcp.app/mcp"
      }
    }
  }
}
```

**Programmatic Access:**
```python
from fastmcp import Client
import asyncio

async def main():
    async with Client("https://your-project-name.fastmcp.app/mcp") as client:
        tools = await client.list_tools()
        result = await client.call_tool("greet", {"name": "Alice"})
        print(result.content[0].text)

asyncio.run(main())
```

#### Pricing

**Beta Period:** Completely free with no credit card required

**Future Pricing:** To be announced as platform exits beta. Expected to include:
- Free tier for hobby projects
- Paid tiers with higher resource limits
- Enterprise options with SLA guarantees

Stay updated at [fastmcp.cloud/pricing](https://fastmcp.cloud/pricing)

---

## Cookbook: Common Patterns

### Basic Tool Example

```python
from fastmcp import FastMCP

mcp = FastMCP("Calculator")

@mcp.tool
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b

@mcp.tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b

if __name__ == "__main__":
    mcp.run()
```

### Async Tools with Context

```python
from fastmcp import FastMCP, Context
import httpx

mcp = FastMCP("Weather Service")

@mcp.tool
async def get_weather(city: str, ctx: Context) -> dict:
    """Get weather information for a city."""
    await ctx.info(f"Fetching weather for {city}...")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.weather.com/v1/current",
            params={"city": city}
        )
        data = response.json()

    await ctx.info("Weather data retrieved successfully")
    return data

if __name__ == "__main__":
    mcp.run()
```

### Resource with Templates

```python
from fastmcp import FastMCP
import json

mcp = FastMCP("User Service")

# Static resource
@mcp.resource("config://app")
def get_config():
    """Application configuration."""
    return {"version": "1.0.0", "env": "production"}

# Dynamic resource template
@mcp.resource("users://{user_id}/profile")
def get_user_profile(user_id: int):
    """Get user profile by ID."""
    # Fetch from database
    return {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com"
    }

# List resource
@mcp.resource("users://all")
def list_users():
    """List all users."""
    return [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ]

if __name__ == "__main__":
    mcp.run()
```

### Prompts for Code Review

```python
from fastmcp import FastMCP

mcp = FastMCP("Code Assistant")

@mcp.prompt
def review_code(code: str, language: str = "python") -> str:
    """Generate a code review prompt."""
    return f"""Please review the following {language} code:

```{language}
{code}
```

Focus on:
1. Code quality and best practices
2. Potential bugs or issues
3. Performance considerations
4. Security concerns
"""

@mcp.prompt
def explain_code(code: str) -> str:
    """Generate a code explanation prompt."""
    return f"""Please explain what this code does in simple terms:

```
{code}
```

Include:
- Overall purpose
- How it works step by step
- Key concepts used
"""

if __name__ == "__main__":
    mcp.run()
```

### Progress Reporting

```python
from fastmcp import FastMCP, Context
import asyncio

mcp = FastMCP("Batch Processor")

@mcp.tool
async def process_batch(items: list[str], ctx: Context) -> dict:
    """Process a batch of items with progress reporting."""
    total = len(items)
    results = []

    for i, item in enumerate(items):
        await ctx.report_progress(i, total)
        await ctx.info(f"Processing item {i+1}/{total}: {item}")

        # Simulate processing
        await asyncio.sleep(0.5)
        results.append(f"Processed: {item}")

    await ctx.report_progress(total, total)
    return {"processed": total, "results": results}

if __name__ == "__main__":
    mcp.run()
```

### Error Handling

```python
from fastmcp import FastMCP, Context

mcp = FastMCP("File Service")

@mcp.tool
async def read_file(path: str, ctx: Context) -> str:
    """Read contents of a file."""
    try:
        await ctx.info(f"Reading file: {path}")
        with open(path, 'r') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        await ctx.error(f"File not found: {path}")
        raise ValueError(f"File {path} does not exist")
    except PermissionError:
        await ctx.error(f"Permission denied: {path}")
        raise ValueError(f"Cannot read {path}: permission denied")
    except Exception as e:
        await ctx.error(f"Unexpected error: {str(e)}")
        raise

if __name__ == "__main__":
    mcp.run()
```

### LLM Sampling

```python
from fastmcp import FastMCP, Context

mcp = FastMCP("Analysis Service")

@mcp.tool
async def analyze_sentiment(text: str, ctx: Context) -> dict:
    """Analyze sentiment of text using client's LLM."""
    await ctx.info("Analyzing sentiment...")

    # Request sentiment analysis from client's LLM
    prompt = f"""Analyze the sentiment of this text and respond with just one word: positive, negative, or neutral.

Text: {text}"""

    result = await ctx.sample(prompt, temperature=0.3)
    sentiment = result.strip().lower()

    return {
        "text": text,
        "sentiment": sentiment
    }

if __name__ == "__main__":
    mcp.run()
```

### Testing with In-Memory Client

```python
from fastmcp import FastMCP, Client
import asyncio

mcp = FastMCP("Test Server")

@mcp.tool
def greet(name: str) -> str:
    """Greet a person by name."""
    return f"Hello, {name}!"

async def test_server():
    """Test the server using in-memory client."""
    async with Client(mcp) as client:
        # List tools
        tools = await client.list_tools()
        print(f"Available tools: {[t.name for t in tools]}")

        # Call tool
        result = await client.call_tool("greet", {"name": "Alice"})
        print(f"Result: {result.content[0].text}")

        assert result.content[0].text == "Hello, Alice!"
        print("✓ Test passed!")

if __name__ == "__main__":
    asyncio.run(test_server())
```

### Multi-Server Client

```python
from fastmcp import Client
import asyncio

async def main():
    """Connect to multiple servers with a single client."""
    config = {
        "mcpServers": {
            "weather": {
                "url": "https://weather-api.example.com/mcp"
            },
            "calculator": {
                "command": "python",
                "args": ["./calculator_server.py"]
            }
        }
    }

    client = Client(config)

    async with client:
        # Tools are prefixed with server name
        weather = await client.call_tool(
            "weather_get_forecast",
            {"city": "London"}
        )

        result = await client.call_tool(
            "calculator_add",
            {"a": 5, "b": 3}
        )

        print(f"Weather: {weather.content[0].text}")
        print(f"5 + 3 = {result.content[0].text}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Authenticated Server and Client

```python
from fastmcp import FastMCP, Client
from fastmcp.server.auth import GoogleProvider
import asyncio

# Server with authentication
auth = GoogleProvider(
    client_id="your_client_id",
    client_secret="your_client_secret",
    base_url="https://myserver.com"
)

mcp = FastMCP("Protected Server", auth=auth)

@mcp.tool
def secret_operation() -> str:
    """A protected operation."""
    return "Secret data"

# Client connecting to protected server
async def main():
    async with Client("https://myserver.com/mcp", auth="oauth") as client:
        # Automatic browser-based OAuth flow
        result = await client.call_tool("secret_operation")
        print(result.content[0].text)

if __name__ == "__main__":
    # Run server
    # mcp.run(transport="http", host="0.0.0.0", port=443)

    # Or run client
    asyncio.run(main())
```

---

## Testing

FastMCP has a comprehensive test suite. To contribute:

### Setup Development Environment

```bash
git clone https://github.com/jlowin/fastmcp.git
cd fastmcp
uv sync
```

### Run Tests

```bash
# Run all tests
pytest

# With coverage
uv run pytest --cov=src --cov=examples --cov-report=html
```

### Static Checks

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run manually
uv run pre-commit run --all-files
```

---

## Requirements

- Python 3.10+
- uv (recommended for environment management)

---

## License

MIT

---

## Documentation

Complete documentation available at **[gofastmcp.com](https://gofastmcp.com)**

LLM-friendly documentation:
- [llms.txt](https://gofastmcp.com/llms.txt) - Documentation sitemap
- [llms-full.txt](https://gofastmcp.com/llms-full.txt) - Complete documentation
