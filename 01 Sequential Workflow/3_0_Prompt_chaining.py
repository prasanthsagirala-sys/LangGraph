from langgraph.graph import StateGraph, START, END
from typing import TypedDict

from pydantic_core.core_schema import SetSchema
from pil_image_show import imshow_raw
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

#create a state
class BlogState(TypedDict):
    topic: str 
    outline: str 
    blog_content: str

#create graph
graph = StateGraph(BlogState)

model = ChatOpenAI(model = 'gpt-5.1')

parser = StrOutputParser()

def create_outline(state: BlogState) -> BlogState:
    #extract question
    topic = state['topic']

    #form a prompt 
    promt = PromptTemplate(
        template = 'Create a detailed outline for a blog on topic: "{topic}"',
        input_variables = ['topic']
    )

    #ask llm
    chain = promt | model | parser

    state['outline'] = chain.invoke({'topic':topic})

    return state

def create_blog(state: BlogState) -> BlogState:
    #extract question
    outline = state['outline']
    topic = state['topic']

    #form a prompt 
    promt = PromptTemplate(
        template = 'Write a detailed blog for topic "{topic}" from outline:\n "{outline}"',
        input_variables = ['outline','topic']
    )

    #ask llm
    chain = promt | model | parser

    state['blog_content'] = chain.invoke({'outline':outline,'topic':topic})

    return state



#add nodes
graph.add_node('create_outline',create_outline)
graph.add_node('create_blog',create_blog)

#add edges
graph.add_edge(START,'create_outline')
graph.add_edge('create_outline','create_blog')
graph.add_edge('create_blog',END)

#complie graph
workflow = graph.compile()

workflow.get_graph().print_ascii()

initial_state = {'topic': 'LangGraph vs LangChain'}

final_state = workflow.invoke(initial_state)

print(final_state)
