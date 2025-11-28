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

user_input = st.chat_input('Type here')

if user_input:

    message_history.append({'role':'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)
    
    with st.chat_message('assistant'):
        stream = chatbot.stream(
            {'messages': [HumanMessage(content = user_input)]}, 
            config = {'configurable':{'thread_id':'thread-1'}},
            stream_mode = 'messages'
        )
        ai_message = st.write_stream(message_chunk.content for message_chunk, metadata in stream)
    
    message_history.append({'role':'assistant', 'content': ai_message})