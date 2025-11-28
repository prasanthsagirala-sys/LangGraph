from langgraph.graph import StateGraph, START, END
from typing import Literal, TypedDict, Annotated
from langgraph.graph.message import add_messages

from pydantic import Field, BaseModel

from pil_image_show import imshow_raw
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate, prompt
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
import operator

from pprint import pprint


load_dotenv()

model = ChatOpenAI(model = 'gpt-5.1')

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    messages = state['messages']
    response = model.invoke(messages)
    return {'messages':[response]}

graph = StateGraph(ChatState)

#nodes
graph.add_node('chat_node',chat_node)

graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node',END)

chatbot = graph.compile()

# imshow_raw(chatbot)

initial_state = {
    'messages' : [HumanMessage(content = 'What is captial of India')]
}

final_state = chatbot.invoke(initial_state)

print(final_state)