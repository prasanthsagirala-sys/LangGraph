from langgraph.graph import StateGraph, START, END
from typing import Type, TypedDict, Annotated

from pydantic import Field, BaseModel

from pydantic_core.core_schema import SetSchema
from pil_image_show import imshow_raw
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

import operator

from pprint import pprint


load_dotenv()

model = ChatOpenAI(model = 'gpt-5.1')

class EvaluationSchema(BaseModel):

    feedback: str = Field(description='Detailed feedback for the essay')
    score: int = Field(description='Score out of 10', ge=0, le=10)

structured_model = model.with_structured_output(EvaluationSchema)

with open('2_0_Essay.txt',encoding='utf-8') as f:
    essay = ''.join(f.readlines())

class UPSCState(TypedDict):

    essay: str 
    language_feedback: str 
    analysis_feedback: str 
    clarity_feedback: str 
    overall_feedback: str 
    individual_scores: Annotated[list[int], operator.add] #[score1]+[score2]+[score3]
    avg_score: float 

graph = StateGraph(UPSCState)

parser = StrOutputParser()

def evaluate_language(state: UPSCState):

    prompt = PromptTemplate(
        template = 'Evaluate the language quality of the following eassay and provide a feedback and assign score out of 0-10: \n {essay}',
        input_variables = ['essay']
    )
    
    chain = prompt | structured_model

    final_result = chain.invoke(state['essay'])

    return {'language_feedback':final_result.feedback, 'individual_scores':[final_result.score]}

def evaluate_analysis(state: UPSCState):

    prompt = PromptTemplate(
        template = 'Evaluate the depth of analysis of the following eassay and provide a feedback and assign score out of 0-10: \n {essay}',
        input_variables = ['essay']
    )
    
    chain = prompt | structured_model

    final_result = chain.invoke(state['essay'])

    return {'analysis_feedback':final_result.feedback, 'individual_scores':[final_result.score]}

def evaluate_thought(state: UPSCState):

    prompt = PromptTemplate(
        template = 'Evaluate the Clarity of thought of the following eassay and provide a feedback and assign score out of 0-10: \n {essay}',
        input_variables = ['essay']
    )
    
    chain = prompt | structured_model

    final_result = chain.invoke(state['essay'])

    return {'clarity_feedback':final_result.feedback, 'individual_scores':[final_result.score]}

def final_evaluation(state: UPSCState):

    prompt = PromptTemplate(
        template = '''
        Based on following feedbacks, generate a final summary feedback.

        Language Feedback: {language_feedback}

        Depth of Analysis Feedback: {analysis_feedback}

        Clarity of Thought Feedback : {clarity_feedback}

        ''',
        input_variables = ['language_feedback', 'analysis_feedback', 'clarity_feedback']
    )
    
    chain = prompt | model | parser #No need to use structured model

    final_feedback = chain.invoke({'language_feedback':state['language_feedback'],
                                 'analysis_feedback':state['analysis_feedback'], 
                                 'clarity_feedback':state['clarity_feedback']
                                })

    final_score =  sum(state['individual_scores'])/len(state['individual_scores'])

    return {'overall_feedback':final_feedback, 'avg_score':final_score}


#add nodes 
graph.add_node('evaluate_language',evaluate_language)
graph.add_node('evaluate_analysis',evaluate_analysis)
graph.add_node('evaluate_thought',evaluate_thought)
graph.add_node('final_evaluation',final_evaluation)

#add edges 
graph.add_edge(START, 'evaluate_language')
graph.add_edge(START, 'evaluate_analysis')
graph.add_edge(START, 'evaluate_thought')

graph.add_edge('evaluate_language','final_evaluation')
graph.add_edge('evaluate_analysis','final_evaluation')
graph.add_edge('evaluate_thought','final_evaluation')

graph.add_edge('final_evaluation', END)

workflow = graph.compile()

#imshow_raw(workflow)

initial_state = {'essay':essay}

final_state = workflow.invoke(initial_state)

pprint(final_state)