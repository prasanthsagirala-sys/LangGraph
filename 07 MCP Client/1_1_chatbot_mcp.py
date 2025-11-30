from langgraph.graph import StateGraph, START, END
from langgraph.graph import message
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import ToolNode, tools_condition

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate, prompt
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient

import operator
from typing import Literal, TypedDict, Annotated
from pydantic import Field, BaseModel
from pprint import pprint 
from dotenv import load_dotenv
import sqlite3
import requests
import asyncio


import os 
os.environ['LANGSMITH_PROJECT'] = 'ChatBot' #To track all LangGraph runs under this project in LangSmith UI

load_dotenv() 

model = ChatOpenAI(model = 'gpt-5.1')

# MCP client for local FastMCP server
client = MultiServerMCPClient(
    {
        'arith':{
            'transport': 'stdio', # stdio is for local servers
            'command': r"C:\Users\sgp\Desktop\GenAI\LangGraph\venv\Scripts\python.exe",
            'args': [r"C:\Users\sgp\Desktop\GenAI\LangGraph\07 MCP Client\mcp-math-server\main.py"]
        },
        # 'expense':{
        #     'transport': 'streamable_http', # if this fails, try 'sse'
        #     'url': 'http://splendid-gold.dingo.fastmcp.app/mcp'
        # }
    }
)

# aiosqlite.connet for async sqlite

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

async def build_graph():

    tools = await client.get_tools()

    print(tools)
    '''
    [StructuredTool(name='calculator',
         description='Perform basic arithmetic on two numbers. Supported operations: add, sub, mul, div.', 
         args_schema={'type': 'object', 
            'properties': {'first_num': {'type': 'number', 'description': 'First number'}, 
                            'second_num': {'type': 'number', 'description': 'Second number'},
                              'operation': {'type': 'string', 'description': 'Operation to perform', 'enum': ['add', 'sub', 'mul', 'div']}
                              }, 
            'required': ['first_num', 'second_num', 'operation']},
         response_format='content_and_artifact', 
         coroutine=<function convert_mcp_tool_to_langchain_tool.<locals>.call_tool at 0x000001E5F37D6E80>)]
    '''

    llm_with_tools = model.bind_tools(tools)

    async def chat_node(state: ChatState):
        messages = state['messages']
        response = llm_with_tools.invoke(messages)
        return {'messages':[response]}

    tool_node = ToolNode(tools) #By default, ToolNode is async

    graph = StateGraph(ChatState)

    #nodes
    graph = StateGraph(ChatState)
    graph.add_node("chat_node", chat_node)
    graph.add_node("tools", tool_node)

    graph.add_edge(START, "chat_node")

    graph.add_conditional_edges("chat_node",tools_condition)
    graph.add_edge('tools', 'chat_node')

    chatbot = graph.compile()

    return chatbot

async def main():

    chatbot = await build_graph() #Asynchronous functions should be called with await

    #run the graph in async mode
    result = await chatbot.ainvoke({
        'messages':[HumanMessage(content="Add a expense - Rs 500 for Udemy course for 30th Novemeber")]
    })

    print(result['messages'][-1].content)

if __name__ == "__main__":
    asyncio.run(main())