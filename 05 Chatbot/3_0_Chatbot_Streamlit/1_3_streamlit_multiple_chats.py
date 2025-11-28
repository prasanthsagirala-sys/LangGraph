from threading import ThreadError
import streamlit as st

from langgraph_backend import chatbot
from langchain_core.messages import HumanMessage

import uuid 

# ************************************************** utility functions **************************

def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    st.session_state['message_history'] = []
    add_thread(st.session_state['thread_id'])

def add_thread(thread_id):
    # Add thread id to the thread history, only if the thread has any messages
    if thread_id not in st.session_state['chat_threads'] and st.session_state['message_history']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    if st.session_state['message_history']:
        return chatbot.get_state(config = {'configurable':{'thread_id': thread_id}}).values['messages']
    else :
        return []

# ************************************************** Session Setup *******************************
if 'message_history' not in st.session_state:
    st.session_state['message_history']  = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []

add_thread(st.session_state['thread_id'])


# ************************************************** Sidebar UI **********************************

#setup sidebar
st.sidebar.title('LangGraph Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('My Conversations')


#Show up the thread_id in sidebar
for thread_id in st.session_state['chat_threads'][::-1]:  #Display latest thread first
    #st.sidebar.text(thread_id)
    if st.sidebar.button(str(thread_id)):
        st.session_state['thread_id'] = thread_id 
        messages = load_conversation(thread_id)

        temp_messages = []

        for message in messages:
            if isinstance(message, HumanMessage):
                temp_messages.append({'role':'user', 'content': message.content})
            else:
                temp_messages.append({'role':'assistant', 'content': message.content})
        
        st.session_state['message_history'] = temp_messages

# ************************************************** Main UI **********************************
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Type here')

if user_input:

    st.session_state['message_history'].append({'role':'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)
    
    with st.chat_message('assistant'):
        CONFIG = {'configurable':{'thread_id': st.session_state['thread_id']}}
        stream = chatbot.stream(
            {'messages': [HumanMessage(content = user_input)]}, 
            config = CONFIG,
            stream_mode = 'messages'
        )
        ai_message = st.write_stream(message_chunk.content for message_chunk, metadata in stream)
    
    st.session_state['message_history'].append({'role':'assistant', 'content': ai_message})