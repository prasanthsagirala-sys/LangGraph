import streamlit as st

from langgraph_backend import chatbot
from langchain_core.messages import HumanMessage

# st.session_State -> Is a dict but won't get refreshed when user presses Enter

if 'message_history' not in st.session_state:
    st.session_state['message_history']  = []

message_history = st.session_state['message_history']

config = {'configurable':{'thread_id':'thread-1'}}

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Type here') #once user press ENTER, whole code runs again

if user_input:

    message_history.append({'role':'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    response = chatbot.invoke({'messages': [HumanMessage(content = user_input)]}, config = config)
    ai_message = response['messages'][-1].content

    message_history.append({'role':'assistant', 'content': ai_message})
    with st.chat_message('assistant'):
        st.text(ai_message)