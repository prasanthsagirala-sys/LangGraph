from langgraph.graph import StateGraph, START, END
from typing import Literal, TypedDict, Annotated

from pydantic import Field, BaseModel

from pil_image_show import imshow_raw
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate, prompt
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import operator

from pprint import pprint


load_dotenv()

generate_model = ChatOpenAI(model = 'gpt-4o-mini')
model = ChatOpenAI(model = 'gpt-5.1')

#state
class TweetState(TypedDict):
    topic: str 
    tweet: str 
    evaluation: Literal['approved','needs_improvemnet']
    feedback: str 
    max_iteration: int 
    iteration: int

    tweet_history: Annotated[list[str], operator.add]
    feedback_history: Annotated[list[str], operator.add]

#Schema 
class TweetEvaluation(BaseModel):
    evaluation: Literal["approved", "needs_improvement"] = Field(description="Final evaluation result.")
    feedback: str = Field(description="feedback for the tweet.")

eval_model_structured = model.with_structured_output(TweetEvaluation)

def generate_tweet(state: TweetState):

    # prompt
    messages = [
        SystemMessage(content="You are a funny and clever Twitter/X influencer."),
        HumanMessage(content=f"""
Write a short, original, and hilarious tweet on the topic: "{state['topic']}".

Rules:
- Do NOT use question-answer format.
- Max 280 characters.
- Use observational humor, irony, sarcasm, or cultural references.
- Think in meme logic, punchlines, or relatable takes.
- Use simple, day to day english
""")
    ]

    # send generator_llm
    response = generate_model.invoke(messages).content

    # return response
    return {'tweet': response, 'tweet_history':[response]}

def evaluate_tweet(state: TweetState):

    # prompt
    messages = [
    SystemMessage(content="You are a ruthless, no-laugh-given Twitter critic. You evaluate tweets based on humor, originality, virality, and tweet format."),
    HumanMessage(content=f"""
Evaluate the following tweet:

Tweet: "{state['tweet']}"

Use the criteria below to evaluate the tweet:

1. Originality – Is this fresh, or have you seen it a hundred times before?  
2. Humor – Did it genuinely make you smile, laugh, or chuckle?  
3. Punchiness – Is it short, sharp, and scroll-stopping?  
4. Virality Potential – Would people retweet or share it?  
5. Format – Is it a well-formed tweet (not a setup-punchline joke, not a Q&A joke, and under 280 characters)?

Auto-reject if:
- It's written in question-answer format (e.g., "Why did..." or "What happens when...")
- It exceeds 280 characters
- It reads like a traditional setup-punchline joke
- Dont end with generic, throwaway, or deflating lines that weaken the humor (e.g., “Masterpieces of the auntie-uncle universe” or vague summaries)

### Respond ONLY in structured format:
- evaluation: "approved" or "needs_improvement"  
- feedback: One paragraph explaining the strengths and weaknesses 
""")
]

    response = eval_model_structured.invoke(messages)

    return {'evaluation':response.evaluation, 'feedback': response.feedback, 'feedback_history':[response.feedback]}

def optimize_tweet(state: TweetState):

    messages = [
        SystemMessage(content="You punch up tweets for virality and humor based on given feedback."),
        HumanMessage(content=f"""
Improve the tweet based on this feedback:
"{state['feedback']}"

Topic: "{state['topic']}"
Original Tweet:
{state['tweet']}

Re-write it as a short, viral-worthy tweet. Avoid Q&A style and stay under 280 characters.
""")
    ]

    response = model.invoke(messages).content
    iteration = state['iteration'] + 1

    return {'tweet': response, 'iteration': iteration, 'tweet_history':[response]}

def route_evaluation(state: TweetState):

    if state['evaluation'] == 'approved' or state['iteration'] >= state['max_iteration']:
        return 'approved'
    else: 
        return 'needs_improvement'



graph = StateGraph(TweetState)

#nodes 
graph.add_node('generate_tweet',generate_tweet)
graph.add_node('evaluate_tweet',evaluate_tweet)
graph.add_node('optimize_tweet',optimize_tweet)

#edges
graph.add_edge(START,'generate_tweet')
graph.add_edge('generate_tweet','evaluate_tweet')
#conditional edge
graph.add_conditional_edges('evaluate_tweet', route_evaluation, {'approved': END, 'needs_improvement': 'optimize_tweet'})
graph.add_edge('optimize_tweet', 'evaluate_tweet')

workflow = graph.compile()

# workflow.get_graph().print_ascii() # Not showing the Routing conditions and loops in workflow
imshow_raw(workflow) #Shows the routing condtitons

initial_state = {
    'topic': "Boys Hostel life in India",
    'iteration': 1, #Given as iterations, with extra s at the end and it didn't show up in output. I think we need a way to say/ask for all required inputs to continue
    'max_iteration':5
}

final_state = workflow.invoke(initial_state)
pprint(final_state)
'''
{'evaluation': 'approved',
 'feedback': 'Decent hostel-life tweet: the imagery is vivid (illegal kettle, '
             'WWE over stale pizza, attendance shortage as a natural disaster) '
             'and clearly tailored to Indian college kids, which helps '
             'relatability and shareability. Humor is more “knowing smile” '
             'than laugh-out-loud, but it works because the details feel '
             'specific rather than generic. Format is clean, under 280 chars, '
             'not a setup–punchline, and the emojis/hashtag are on-brand for '
             'the topic. Where it falls short is originality—Maggi + illegal '
             'kettle + attendance shortage are very overused hostel tropes on '
             'Indian Twitter, so it risks blending into the “seen this 1000 '
             'times” pile. If you want it to stand out more, swap at least one '
             'cliché image for a weirder, more personal detail from actual '
             'hostel chaos.',
 'feedback_history': ['Stock hostel tropes: maggi-in-the-kettle, hiding food, '
                      'bunking class—this is the hostel meme starter pack, so '
                      'originality is low. There’s mild relatability, but '
                      'nothing actually sharp or surprising enough to be '
                      'funny; it reads more like a caption under a hostel '
                      'Instagram reel than a tweet that punches. It’s also too '
                      'wordy and meandering for Twitter—no real hook, no '
                      'escalation, just a cozy list of clichés padded with '
                      '“path to greatness” faux-grandiosity. Format-wise it’s '
                      'under 280 and not a Q&A or setup-punchline, so it '
                      'passes the technical checks, but it won’t stop thumbs. '
                      'Tighten it, add a specific absurd detail (e.g., how '
                      'many recipes you’ve invented with one kettle, or the '
                      'level of violence over that pizza slice), and cut the '
                      'generic “path to greatness” line to land on a sharper, '
                      'funnier image.',
                      'Decent hostel-life tweet: the imagery is vivid (illegal '
                      'kettle, WWE over stale pizza, attendance shortage as a '
                      'natural disaster) and clearly tailored to Indian '
                      'college kids, which helps relatability and '
                      'shareability. Humor is more “knowing smile” than '
                      'laugh-out-loud, but it works because the details feel '
                      'specific rather than generic. Format is clean, under '
                      '280 chars, not a setup–punchline, and the '
                      'emojis/hashtag are on-brand for the topic. Where it '
                      'falls short is originality—Maggi + illegal kettle + '
                      'attendance shortage are very overused hostel tropes on '
                      'Indian Twitter, so it risks blending into the “seen '
                      'this 1000 times” pile. If you want it to stand out '
                      'more, swap at least one cliché image for a weirder, '
                      'more personal detail from actual hostel chaos.'],
 'iteration': 2,
 'max_iteration': 5,
 'topic': 'Boys Hostel life in India',
 'tweet': 'Boys hostel life in India is just: 27 Maggi recipes, cooking in one '
          'illegal kettle, WWE over the last slice of 3-day-old pizza, and '
          'treating “attendance shortage” like a natural disaster. 🍕🥲 '
          '#HostelLife',
 'tweet_history': ['Boys hostel life in India: where the biggest achievements '
                   'include mastering the art of cooking maggi in a kettle and '
                   "hiding your roommate's leftover pizza like it's national "
                   'treasure. A place where “bunking class” is a minor, minor '
                   'inconvenience on the path to greatness! 🍕🎓#HostelLife',
                   'Boys hostel life in India is just: 27 Maggi recipes, '
                   'cooking in one illegal kettle, WWE over the last slice of '
                   '3-day-old pizza, and treating “attendance shortage” like a '
                   'natural disaster. 🍕🥲 #HostelLife']}
'''