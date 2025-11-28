from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from pil_image_show import imshow_raw

# define state
class BMIState(TypedDict):
    #Any field not added here won't be added from node or will be ignored once the node is executed
    weight_kg:float 
    height_m: float 
    bmi: float
    category : str

def calculate_bmi(state: BMIState) -> BMIState:

    weight = state['weight_kg']
    height = state['height_m']

    bmi = weight/(height**2)

    state['bmi'] = round(bmi,2)

    bmi = state['bmi']

    if bmi < 18.5:
        state['category'] = 'Underweight'
    elif 18.5 <= bmi <25:
        state['category'] = 'Normal'
    elif 25 <= bmi < 30:
        state['category'] = 'Overweight'
    else:
        state['category'] = 'Obese'

    return state

#define graph 
graph = StateGraph(BMIState)

#Add nodes to your graph
graph.add_node('calculate_bmi', calculate_bmi)

# add edges to graph
graph.add_edge(START,'calculate_bmi')
graph.add_edge('calculate_bmi',END)

# compile the graph
workflow = graph.compile()

# execute the graph
initial_state = {'weight_kg':80,'height_m':1.73}
final_State = workflow.invoke(initial_state)

print(final_State)

print(workflow.get_graph().print_ascii())

# Generate PNG bytes
#png_bytes = workflow.get_graph().draw_mermaid_png()   # <-- CALL the method ()

imshow_raw(workflow)
