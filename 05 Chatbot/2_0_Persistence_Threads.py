from langgraph.graph import StateGraph, START, END
from langgraph.graph import message
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver, InMemorySaver

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate, prompt
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage

import operator
from typing import Literal, TypedDict, Annotated
from pydantic import Field, BaseModel
from pil_image_show import imshow_raw
from pprint import pprint 
from dotenv import load_dotenv

load_dotenv() 

#llm = ChatOpenAI(model = 'gpt-5.1')
llm = ChatOpenAI()

class JokeState(TypedDict):

    topic: str
    joke: str
    explanation: str

def generate_joke(state: JokeState):

    prompt = f'generate a joke on the topic {state["topic"]}'
    response = llm.invoke(prompt).content

    return {'joke': response}

def generate_explanation(state: JokeState):

    prompt = f'write an explanation for the joke - {state["joke"]}'
    response = llm.invoke(prompt).content

    return {'explanation': response}

graph = StateGraph(JokeState)

graph.add_node('generate_joke', generate_joke)
graph.add_node('generate_explanation', generate_explanation)

graph.add_edge(START, 'generate_joke')
graph.add_edge('generate_joke', 'generate_explanation')
graph.add_edge('generate_explanation', END)

checkpointer = InMemorySaver()

workflow = graph.compile(checkpointer=checkpointer)

config1 = {"configurable": {"thread_id": "1"}}
response = workflow.invoke({'topic':'pizza'}, config=config1)
pprint(response)
{'explanation': 'This joke plays on the idea of a pizza having too many '
                'toppings and not being able to hold them all together, much '
                'like a person who is struggling emotionally might seek '
                'therapy to help them handle their issues. The humor comes '
                'from the unexpectedness of a pizza going to therapy and the '
                'clever play on words with the toppings.',
 'joke': 'Why did the pizza go to the therapist? Because it had too many '
         "toppings and couldn't hold it all together!",
 'topic': 'pizza'}
'''
'''
print('-'*75)

pprint(workflow.get_state(config1))
'''
StateSnapshot(values={'topic': 'pizza', 'joke': "Why did the pizza go to the therapist? Because it had too many toppings and couldn't hold it all together!", 'explanation': 'This joke plays on the idea of a pizza having too many toppings and not being able to hold them all together, much like a person who is struggling emotionally might seek therapy to help them handle their issues. The humor comes from the unexpectedness of a pizza going to therapy and the clever play on words with the toppings.'},
 next=(), config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1f0cc539-9f49-6092-8002-94c70c621a94'}}, 
 metadata={'source': 'loop', 'step': 2, 'parents': {}}, 
 created_at='2025-11-28T12:13:08.577909+00:00', 
 parent_config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1f0cc539-926d-6952-8001-a654fd1e2712'}}, 
 tasks=(), interrupts=())
'''

print('-'*75)

pprint(list(workflow.get_state_history(config1))) #Latest State will be at First
'''
[StateSnapshot(values={'topic': 'pizza', 'joke': "Why did the pizza go to the therapist? Because it had too many toppings and couldn't hold it all together!", 'explanation': 'This joke plays on the idea of a pizza having too many toppings and not being able to hold them all together, much like a person who is struggling emotionally might seek therapy to help them handle their issues. The humor comes from the unexpectedness of a pizza going to therapy and the clever play on words with the toppings.'}, 
    next=(), config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1f0cc539-9f49-6092-8002-94c70c621a94'}},
    metadata={'source': 'loop', 'step': 2, 'parents': {}}, created_at='2025-11-28T12:13:08.577909+00:00', 
    parent_config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1f0cc539-926d-6952-8001-a654fd1e2712'}}, 
    tasks=(), interrupts=()),
 StateSnapshot(values={'topic': 'pizza', 'joke': "Why did the pizza go to the therapist? Because it had too many toppings and couldn't hold it all together!"}, 
    next=('generate_explanation',), config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1f0cc539-926d-6952-8001-a654fd1e2712'}},
    metadata={'source': 'loop', 'step': 1, 'parents': {}}, created_at='2025-11-28T12:13:07.229729+00:00', 
    parent_config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1f0cc539-8568-6419-8000-281fecf7ccb1'}}, 
    tasks=(PregelTask(id='dc2d6bf6-1cbd-fbae-3d97-c3b774ba2ae2', 
    name='generate_explanation', path=('__pregel_pull', 'generate_explanation'), 
    error=None, interrupts=(), state=None, 
    result={'explanation': 'This joke plays on the idea of a pizza having too many toppings and not being able to hold them all together, much like a person who is struggling emotionally might seek therapy to help them handle their issues. The humor comes from the unexpectedness of a pizza going to therapy and the clever play on words with the toppings.'}),), 
    interrupts=()),
 StateSnapshot(values={'topic': 'pizza'}, 
    next=('generate_joke',), config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1f0cc539-8568-6419-8000-281fecf7ccb1'}}, 
    metadata={'source': 'loop', 'step': 0, 'parents': {}}, created_at='2025-11-28T12:13:05.864399+00:00', 
    parent_config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1f0cc539-8568-6418-bfff-6d26d353724c'}}, 
    tasks=(PregelTask(id='493a16da-c65e-ea72-16fb-4cd4bef17709', 
    name='generate_joke', path=('__pregel_pull', 'generate_joke'), 
    error=None, interrupts=(), state=None, 
    result={'joke': "Why did the pizza go to the therapist? Because it had too many toppings and couldn't hold it all together!"}),), 
    interrupts=()),
 StateSnapshot(values={}, 
    next=('__start__',), config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1f0cc539-8568-6418-bfff-6d26d353724c'}}, 
    metadata={'source': 'input', 'step': -1, 'parents': {}}, created_at='2025-11-28T12:13:05.864399+00:00', 
    parent_config=None, 
    tasks=(PregelTask(id='4011962c-9313-14b5-9ad9-6a859c54bc3f', 
    name='__start__', path=('__pregel_pull', '__start__'), 
    error=None, interrupts=(), state=None, 
    result={'topic': 'pizza'}),), 
    interrupts=())]
'''
config2 = {'configurable':{'thread_id':'2'}}
workflow.invoke({'topic':'pasta'}, config=config2)

pprint(list(workflow.get_state_history(config2))) #Gets StateHistory for thread_id = 2
