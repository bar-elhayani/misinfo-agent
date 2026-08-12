"""
Shared MCP client helper: connects to the MCP server over HTTP
(streamable-http transport) and calls tools through the real MCP
protocol, replacing the temporary direct-import approach used during
initial agent development.
"""

import asyncio
import json
import os

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

# Defaults to localhost for local development. In Docker Compose, this
# is overridden to the service name (e.g. "http://mcp-server:8000/mcp"),
# since containers reach each other by service name, not localhost.
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")


async def _call_tool_async(tool_name: str, arguments: dict) -> dict:
    """
    Opens a fresh MCP session, calls one tool, and returns its result
    as a plain dict. A new session per call is simpler to reason about
    than a long-lived shared session, at the cost of some connection
    overhead per call - an acceptable tradeoff at this project's scale.
    """
    async with streamable_http_client(MCP_SERVER_URL) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)

            # MCP tool results come back as a list of content blocks
            # (usually one text block containing JSON). Extract and parse it.
            text_content = result.content[0].text
            return json.loads(text_content)


def call_tool(tool_name: str, arguments: dict) -> dict:
    """
    Synchronous wrapper around _call_tool_async, so LangGraph nodes
    (which are currently sync functions) can call MCP tools without
    the whole graph needing to become async.
    """
    return asyncio.run(_call_tool_async(tool_name, arguments))