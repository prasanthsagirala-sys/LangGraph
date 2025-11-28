from langgraph.graph import StateGraph, START, END
from typing import Literal, TypedDict, Annotated
from langgraph.graph import message
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

count_convo = 0

messages = []

while True:
    user_message = input('User: ')

    if user_message.strip().lower() in ['exit','quit','bye']:
        break 
     
    messages.append(HumanMessage(content = user_message))

    #Invoke always creates a new conversation. We need to use Persistence to avoid calling multiple times
    response = chatbot.invoke({'messages': messages})

    messages.append(response['messages'][-1])

    print('AI: ', response['messages'][-1].content)

# pprint(messages)
# print('-'*75)
# pprint(response)


