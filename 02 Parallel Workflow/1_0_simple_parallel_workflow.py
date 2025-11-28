from os import set_inheritable
from langgraph.graph import StateGraph, START, END
from typing import Type, TypedDict

from pydantic import Field

from pydantic_core.core_schema import SetSchema
from pil_image_show import imshow_raw
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

class BatsmanState(TypedDict):
    runs: int 
    balls: int 
    fours: int 
    sixes: int 

    sr: float #Strike Rate
    bpb: float #balls per boundary
    boundary_percent: float
    summary: str

graph = StateGraph(BatsmanState)

def calculate_sr(state: BatsmanState):
    sr = (state['runs']/state['balls'])*100
    # state['sr'] = sr 
    return {'sr':sr} 

def calculate_bpb(state: BatsmanState) :
    bpb = (state['balls']/(state['fours']+state['sixes']))
    # state['bpb'] = bpb 
    return {'bpb':bpb}

def calculate_boundary_percentage(state: BatsmanState) :
    bp = ((state['fours']*4 + state['sixes']*6)/state['runs'])*100
    # state['boundary_percent'] = bp 
    return {'boundary_percent':bp}

model = ChatOpenAI(model = 'gpt-5.1')
parser = StrOutputParser()

def create_summary(state: BatsmanState) -> BatsmanState:

    #form a prompt 
    promt = PromptTemplate(
        template = 'Generate summary for below batsman details:\n {batsman_details}',
        input_variables = ['batsman_details']
    )

    #ask llm
    chain = promt | model | parser

    print(state)

    #state['summary'] = chain.invoke(state)
    summary = chain.invoke(str(state))

    return {'summary':summary}

#nodes
graph.add_node('calculate_sr',calculate_sr)
graph.add_node('calculate_bpb', calculate_bpb)
graph.add_node('calculate_boundary_percentage',calculate_boundary_percentage)
graph.add_node('summary', create_summary)

#edges
graph.add_edge(START,'calculate_sr')
graph.add_edge(START,'calculate_bpb')
graph.add_edge(START,'calculate_boundary_percentage')

graph.add_edge('calculate_sr','summary')
graph.add_edge('calculate_bpb','summary')
graph.add_edge('calculate_boundary_percentage','summary')

graph.add_edge('summary', END)

#complie
workflow = graph.compile()

#workflow.get_graph().print_ascii()
#imshow_raw(workflow)

initial_state = {'runs': 100, 'balls':50, 'fours': 6, 'sixes': 4}

final_state = workflow.invoke(initial_state)

print(final_state)






