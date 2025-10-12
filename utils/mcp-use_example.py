import asyncio
from langchain_mistralai import ChatMistralAI
from mcp_use import MCPAgent, MCPClient

async def main():
    client = MCPClient(config=
    {
      "mcpServers": {
        "brave-search": {
          "command": "npx",
          "args": [
            "-y",
            "@modelcontextprotocol/server-brave-search"
          ],
          "env": {
            "BRAVE_API_KEY": "BSA41s9jTRtw2uu4IES4LkY3tPwHOIt"
          }
        }
      }
    }
    )
    # Create LLM
    llm = ChatMistralAI(model="mistral-large-latest")
    # Create agent with tools
    agent = MCPAgent(llm=llm, client=client, max_steps=30)
    # Run the query
    result = await agent.run("What is the weather in Olomouc")

if __name__ == "__main__":
    asyncio.run(main())