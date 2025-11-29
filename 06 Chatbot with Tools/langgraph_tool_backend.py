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

import os 
os.environ['LANGSMITH_PROJECT'] = 'ChatBot' #To track all LangGraph runs under this project in LangSmith UI

load_dotenv() 

model = ChatOpenAI(model = 'gpt-5.1')


# -------------------
# 2. Tools
# -------------------
# Tools
search_tool = DuckDuckGoSearchRun(region="us-en")

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




@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
    using Alpha Vantage with API key in the URL.
    """
    alphavantage_api_key = os.environ['alphavantage_api_key'] 
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={alphavantage_api_key}"
    r = requests.get(url)
    return r.json()



tools = [search_tool, get_stock_price, calculator]
llm_with_tools = model.bind_tools(tools)

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    return {'messages':[response]}

tool_node = ToolNode(tools)

#Checkpointer
path = os.path.join(os.path.dirname(__file__), 'chatbot.db')
conn = sqlite3.connect(database=path, check_same_thread=False)
checkpointer = SqliteSaver(conn)

# Create thread_names table if it doesn't exist
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS thread_names (
        thread_id TEXT PRIMARY KEY,
        thread_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

graph = StateGraph(ChatState)

#nodes
graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "chat_node")

graph.add_conditional_edges("chat_node",tools_condition)
graph.add_edge('tools', 'chat_node')

chatbot = graph.compile(checkpointer=checkpointer)

# #Instead of .invoke, call .stream 
# # Stream uses generator to generate chunks one by one 
# stream = chatbot.stream(
#     {'messages': [HumanMessage(content = 'What is recipe to pasta?')]}, 
#     config = {'configurable':{'thread_id':'thread-1'}},
#     stream_mode= 'messages'
# )

# for message_chunk, metadata in stream:
#     if message_chunk.content:
#         print(message_chunk.content, end ='', flush = True) 
#         #When flush=True, cursor is moving along the text while printing
#         #when it's not used, the cursor is at the end completely like printing each line everytime instead of each character

class SummaryTitleSchema(BaseModel):
    summary_title: str = Field(description='Title of a LLM chat with user')

summary_tilte_model = model.with_structured_output(SummaryTitleSchema)

prompt = PromptTemplate(
    template = 'Generate a Short Chat title that can be displayed at the side bar in UI for below chat: \n{chat}',
    input_variables = ['chat']
)

summary_title_chain = prompt | summary_tilte_model

# config = {'configurable':{'thread_id':'thread-1'}}
# #response = chatbot.invoke({'messages': [HumanMessage(content = 'Hi my name is Prasanth')]}, config = config) #This reponse will be saved in db
# response = chatbot.invoke({'messages': [HumanMessage(content = 'what is my name?')]}, config = config) #This can answer my name as previous response got saved the messages in db
# #print(response) 

# #Please open the chatbot.db in DB browser to see the saved messages. Refer column Checkpoint 

# config = {'configurable':{'thread_id':'thread-2'}}
# response = chatbot.invoke({'messages': [HumanMessage(content = 'Hi my name is Geetha')]}, config = config) #This reponse will be saved in db
# #response = chatbot.invoke({'messages': [HumanMessage(content = 'what is my name?')]}, config = config) #This can answer my name as previous response got saved the messages in db
# print(response) 

def retrieve_all_threads():
    all_threads = set()
    for cp in checkpointer.list(None):
        all_threads.add(cp.config['configurable']['thread_id']) #Gets all the checkpoint ids saved in the db
    return list(all_threads)

def save_thread_name(thread_id, thread_name):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO thread_names (thread_id, thread_name, created_at, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(thread_id) DO UPDATE SET
            thread_name = excluded.thread_name,
            updated_at = CURRENT_TIMESTAMP
    """, (str(thread_id), thread_name))
    conn.commit()

def get_thread_name(thread_id):
    """Retrieve thread name from database"""
    cursor = conn.cursor()
    cursor.execute('SELECT thread_name FROM thread_names WHERE thread_id = ?', (str(thread_id),))
    result = cursor.fetchone()
    return result[0] if result else None

def get_all_thread_names():
    """Retrieve all thread names from database"""
    cursor = conn.cursor()
    # Get latest thread first
    cursor.execute('SELECT thread_id, thread_name FROM thread_names order by created_at')
    results = cursor.fetchall()
    return {str(row[0]): row[1] for row in results}

# print(retrieve_all_threads())
#print(get_all_thread_names())
# print(get_thread_name('7aef5e9d-2b52-4b4a-9d09-9e86d749d39c'))

# out = chatbot.invoke(
#     {'messages': [HumanMessage(content = 'what is stock price of facebook today?')]}, 
#     config = {'configurable':{'thread_id':'thread-1'}}
# )

# print(out['messages'][-1].content)