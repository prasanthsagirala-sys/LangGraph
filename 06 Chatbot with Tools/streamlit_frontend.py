from threading import ThreadError
import streamlit as st

from langgraph_tool_backend import chatbot, summary_title_chain, retrieve_all_threads, save_thread_name, get_thread_name, get_all_thread_names
from langchain_core.messages import HumanMessage, AIMessage
from langsmith import traceable
import random

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
        set_thread_title(thread_id)

#@traceable(name = "Set Thread Title", metadata={'thread_id': thread_id})
def set_thread_title(thread_id):
    if thread_id in st.session_state['chat_threads'] and st.session_state['message_history']:
        messages = random.sample(st.session_state['message_history'], min(10, len(st.session_state['message_history'])))
        temp_messages = []
        for message in messages:
            if message['role']=='user':
                temp_messages.append('user content: ' + message['content'][:1000])
            # else:
            #     temp_messages.append('assistant content: ' + message['content'][:1000])
        msg_str = '\n\n'.join(temp_messages)

        summary_title = summary_title_chain.invoke(msg_str).summary_title

        #st.session_state['thread_names'][str(thread_id)] = summary_title
        # Save thread name to database
        save_thread_name(thread_id, summary_title)


def load_conversation(thread_id):
    
    return chatbot.get_state(config = {'configurable':{'thread_id': thread_id}}).values['messages']
    

# ************************************************** Session Setup *******************************
if 'message_history' not in st.session_state:
    st.session_state['message_history']  = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()

# if 'thread_names' not in st.session_state:
#     # Load thread names from database
#     st.session_state['thread_names'] = get_all_thread_names()

add_thread(st.session_state['thread_id'])


# ************************************************** Sidebar UI **********************************

#setup sidebar
st.sidebar.title('LangGraph Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('My Conversations')


#Show up the thread_id in sidebar
thread_names = get_all_thread_names()
for thread_id in st.session_state['chat_threads'][::-1]: 
    #st.sidebar.text(thread_id)
    if str(thread_id) in thread_names:
        thread_name = get_thread_name(str(thread_id))
    else:
        thread_name = str(thread_id)
    if st.sidebar.button(thread_name):
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
        CONFIG = {'configurable':{'thread_id': st.session_state['thread_id']},
                'metadata': {'thread_id': st.session_state['thread_id']},
                'run_name': 'assistant response'
            }
        stream = chatbot.stream(
            {'messages': [HumanMessage(content = user_input)]}, 
            config = CONFIG,
            stream_mode = 'messages'
        )

        #Stream write only if its a AI message. Ignore other message chunks like tool calls
        ai_message = st.write_stream(message_chunk.content for message_chunk, metadata in stream if isinstance(message_chunk, AIMessage))
    
    st.session_state['message_history'].append({'role':'assistant', 'content': ai_message})
    
    set_thread_title(st.session_state['thread_id'])
