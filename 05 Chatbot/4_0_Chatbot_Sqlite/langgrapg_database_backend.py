from langgraph.graph import StateGraph, START, END
from langgraph.graph import message
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate, prompt
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage

import operator
from typing import Literal, TypedDict, Annotated
from pydantic import Field, BaseModel
from pprint import pprint 
from dotenv import load_dotenv
import sqlite3

load_dotenv() 

model = ChatOpenAI(model = 'gpt-5.1')

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    messages = state['messages']
    response = model.invoke(messages)
    return {'messages':[response]}

#Checkpointer
conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)  #Make it multi thread accessible
checkpointer = SqliteSaver(conn)

graph = StateGraph(ChatState)

#nodes
graph.add_node('chat_node',chat_node)

graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node',END)

chatbot = graph.compile(checkpointer= checkpointer)

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

config = {'configurable':{'thread_id':'thread-1'}}
#response = chatbot.invoke({'messages': [HumanMessage(content = 'Hi my name is Prasanth')]}, config = config) #This reponse will be saved in db
response = chatbot.invoke({'messages': [HumanMessage(content = 'what is my name?')]}, config = config) #This can answer my name as previous response got saved the messages in db
print(response) 

