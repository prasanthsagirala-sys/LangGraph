#If Review is +v2, then return a +ve response
#If Review is _ve, then understand issue_type, tone, urgency. Respond using them to the user
from langgraph.graph import StateGraph, START, END
from typing import Literal, Type, TypedDict, Annotated

from pydantic import Field, BaseModel

from pil_image_show import imshow_raw
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

import operator

from pprint import pprint


load_dotenv()

model = ChatOpenAI(model = 'gpt-5.1')

class SentimentSchema(BaseModel):
    sentiment: Literal['positive','negative'] = Field(description='Sentiment of the Review')

class DiagnosisSchema(BaseModel):
    issue_type: Literal["UX", "Performance", "Bug", "Support", "Other"] = Field(description='The category of issue mentioned in the review')
    tone: Literal["angry", "frustrated", "disappointed", "calm"] = Field(description='The emotional tone expressed by the user')
    urgency: Literal["low", "medium", "high"] = Field(description='How urgent or critical the issue appears to be')

sentiment_model = model.with_structured_output(SentimentSchema)
diagnosis_model = model.with_structured_output(DiagnosisSchema)

parser = StrOutputParser()

class ReviewState(TypedDict):
    review: str 
    sentiment: Literal['positive','negative']
    diagnosis: dict 
    response: str 

def find_sentiment(state: ReviewState):
    review = state['review']

    prompt = PromptTemplate(
        template = 'What is the sentiment of following review: {review}',
        input_variables = ['review']
    )

    chain = prompt | sentiment_model

    sentiment = chain.invoke({'review':'The software is too good'}).sentiment

    return {'sentiment':sentiment}

def check_sentiment(state: ReviewState) -> Literal['positive_response', 'run_diagnosis']:
    if state['review']=='positive':
        return 'positive_response'
    else :
        return 'run_diagnosis'

def positive_response(state: ReviewState):
    prompt = PromptTemplate(
        template = "Write a warm thank-you message in response to this review: \n{review} \n Also, kindly ask the user to leave feedback on our website",
        input_variables = ['review']
    )
    response = (prompt | model | parser).invoke(state['review'])

    return {'response':response}

def run_diagnosis(state: ReviewState):
    prompt = PromptTemplate(
        template = '''
        Diagnosis this negative review: \n{review}\n
        Return issue_type , urgency and tone of the review
        ''',
        input_variables = ['review']
    )

    response = (prompt | diagnosis_model).invoke(state['review'])

    return {'diagnosis': response.model_dump()} #model_dump converts the pydantic object to dictionary

def negative_response(state: ReviewState):
    prompt = PromptTemplate(
        template = '''
        """You are a support assistant.
The user had a '{issue_type}' issue, sounded '{tone}', and marked urgency as '{urgency}'.
Write an empathetic, helpful resolution message.
        ''',
        input_variables = ['issue_type', 'tone', 'urgency']
    )

    response = (prompt | model | parser).invoke(state['diagnosis'])

    return {'response':response}

graph = StateGraph(ReviewState)

#nodes
graph.add_node('find_sentiment',find_sentiment)
graph.add_node('positive_response',positive_response)
graph.add_node('run_diagnosis',run_diagnosis)
graph.add_node('negative_response', negative_response)

#edges
graph.add_edge(START, 'find_sentiment')
graph.add_conditional_edges('find_sentiment', check_sentiment)
graph.add_edge('positive_response', END)
graph.add_edge('run_diagnosis', 'negative_response')
graph.add_edge('negative_response', END)

workflow = graph.compile()

initial_state = {'review':'I’ve been trying to log in for over an hour now, and the app keeps freezing on the authentication screen. I even tried reinstalling it, but no luck. This kind of bug is unacceptable, especially when it affects basic functionality.'}
final_state = workflow.invoke(initial_state)
print(final_state)
imshow_raw(workflow)


# print(run_diagnosis(initial_state))
