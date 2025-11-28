#Quadratic equation workflow ax^2 + bx + c = 0
#It has Roots and Discriminent(d = b^2-4ac). If d>0 -> 2 real roots, d=0 -> 1 repeated root, d<0 -> no real roots
# roots = (-b +- (d)**0.5)/2a 

from langgraph.graph import StateGraph, START, END
from typing import Literal, TypedDict
from pil_image_show import imshow_raw

class QuadState(TypedDict):
    a: int 
    b: int 
    c: int 

    equation: str 
    discriminant: float 
    result: str 

graph = StateGraph(QuadState)

def show_equation(state: QuadState):

    b_sign = '+' if state['b']>=0 else ''
    c_sign = '+' if state['c']>=0 else ''

    equation = f"{state['a']}x2{b_sign}{state['b']}x{c_sign}{state['c']}"

    return {"equation":equation}

def calculate_discriminant(state: QuadState):
    discriminant = state['b']**2 - (4*state['a']*state['c'])

    return {'discriminant': discriminant}

def real_roots(state: QuadState):

    root1 = (-state['b'] + state['discriminant']**0.5)/(2*state['a'])
    root2 = (-state['b'] - state['discriminant']**0.5)/(2*state['a'])

    result = f'The roots are {root1} and {root2}'

    return {'result':result}

def repeated_roots(state: QuadState):

    root = (-state['b'])/(2*state['a'])
    

    result = f'Only repeating root is {root}'

    return {'result':result}

def no_real_roots(state: QuadState):

    result = f'No real roots'

    return {'result':result}

def check_condition(state: QuadState) -> Literal['real_roots','repeated_roots','no_real_roots']:
    if state['discriminant']>0:
        return 'real_roots'
    elif state['discriminant']==0:
        return 'repeated_roots'
    else:
        return 'no_real_roots'


#nodes
graph.add_node('show_equation', show_equation)
graph.add_node('calculate_discriminant',calculate_discriminant)
graph.add_node('real_roots', real_roots)
graph.add_node('repeated_roots', repeated_roots)
graph.add_node('no_real_roots', no_real_roots)

graph.add_edge(START,'show_equation')
graph.add_edge('show_equation','calculate_discriminant')

graph.add_conditional_edges('calculate_discriminant',check_condition)
graph.add_edge('real_roots', END)
graph.add_edge('repeated_roots', END)
graph.add_edge('no_real_roots', END)

workflow = graph.compile()

initial_State  = {'a':4, 'b':2, 'c':-4}

workflow.get_graph().print_ascii()
imshow_raw(workflow)

final_state = workflow.invoke(initial_State)

print(final_state)