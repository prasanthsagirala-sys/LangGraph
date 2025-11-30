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

@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div
    """
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Division by zero is not allowed"}
            result = first_num / second_num
        else:
            return {"error": f"Unsupported operation '{operation}'"}
        
        return {"first_num": first_num, "second_num": second_num, "operation": operation, "result": result}
    except Exception as e:
        return {"error": str(e)}


tools = [calculator]
llm_with_tools = model.bind_tools(tools)

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def build_graph():

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

    chatbot = build_graph()

    #run the graph in async mode
    result = await chatbot.ainvoke({
        'messages':[HumanMessage(content="Find the modulus of 132354 and 23 and give answer like a cricket commentator.")]
    })

    print(result['messages'][-1].content)

if __name__ == "__main__":
    asyncio.run(main())