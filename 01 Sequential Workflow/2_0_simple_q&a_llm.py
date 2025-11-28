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
class LLMState(TypedDict):
    question: str 
    answer: str 

#create graph
graph = StateGraph(LLMState)

model = ChatOpenAI(model = 'gpt-5.1')

parser = StrOutputParser()

def llm_qa(state: LLMState) -> LLMState:
    #extract question
    question = state['question']

    #form a prompt 
    promt = PromptTemplate(
        template = 'Answer the following question "{question}"',
        input_variables = ['question']
    )

    #ask llm
    chain = promt | model | parser

    state['answer'] = chain.invoke({'question':question})

    return state



#add nodes
graph.add_node('llm_qa',llm_qa)

#add edges
graph.add_edge(START,'llm_qa')
graph.add_edge('llm_qa',END)

#complie graph
workflow = graph.compile()

workflow.get_graph().print_ascii()


initial_state = {'question': 'How far is earth to sun?'}

final_state = workflow.invoke(initial_state)

print(final_state)