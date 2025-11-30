#!/usr/bin/env python

import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# ---------- Create MCP server ----------

server = Server("arith")

# ---------- Advertise tools ----------

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="calculator",
            description="Perform basic arithmetic on two numbers. Supported operations: add, sub, mul, div.",
            inputSchema={
                "type": "object",
                "properties": {
                    "first_num": {
                        "type": "number",
                        "description": "First number",
                    },
                    "second_num": {
                        "type": "number",
                        "description": "Second number",
                    },
                    "operation": {
                        "type": "string",
                        "description": "Operation to perform",
                        "enum": ["add", "sub", "mul", "div"],
                    },
                },
                "required": ["first_num", "second_num", "operation"],
            },
        )
    ]


# ---------- Handle tool calls ----------

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name != "calculator":
        return [
            TextContent(
                type="text",
                text=f"Unknown tool '{name}'",
            )
        ]

    try:
        first_num = float(arguments.get("first_num"))
        second_num = float(arguments.get("second_num"))
        operation = str(arguments.get("operation"))
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=f"Invalid arguments: {e}",
            )
        ]

    # Core calculator logic
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return [
                    TextContent(
                        type="text",
                        text="Error: Division by zero is not allowed",
                    )
                ]
            result = first_num / second_num
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Error: Unsupported operation '{operation}'",
                )
            ]

        payload = {
            "first_num": first_num,
            "second_num": second_num,
            "operation": operation,
            "result": result,
        }

        return [
            TextContent(
                type="text",
                text=str(payload),
            )
        ]
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=f"Error: {e}",
            )
        ]


# ---------- Entry point (STDIO MCP server) ----------

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
