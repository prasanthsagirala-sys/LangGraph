from threading import ThreadError
import streamlit as st

from langgraph_tool_backend import (chatbot, summary_title_chain, 
        retrieve_all_threads, save_thread_name, 
        get_thread_name, get_all_thread_names)
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
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
# ----- Sidebar UI -----
st.sidebar.title('LangGraph Chatbot')

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

new_chat_button = st.sidebar.button('New Chat')

if new_chat_button:
    reset_chat()
    st.session_state.uploaded_file = None
    st.session_state.uploader_key += 1   # reset uploader widget

st.sidebar.header('My Conversations')

# give the uploader a key so we can control it
uploaded = st.sidebar.file_uploader(
    "Choose a file",
    type=["pdf"],
    key=f"uploader_{st.session_state.uploader_key}"
)

if uploaded:
    st.write("File uploading:", uploaded.name)

    # Save manually to disk
    with open(
        f"C:/Users/sgp/Desktop/GenAI/LangGraph/08 Chatbot with RAG as Tool/streamlit_uploads/{uploaded.name}", 
        "wb"
    ) as f:
        f.write(uploaded.getbuffer())

    st.success("File uploaded successfully!")

    st.session_state['uploaded_file'] = (
        f"C:/Users/sgp/Desktop/GenAI/LangGraph/08 Chatbot with RAG as Tool/streamlit_uploads/{uploaded.name}"
    )
else:
    st.session_state['uploaded_file'] = None


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
        
        # Use a mutable holder so the generator can set/modify it
        status_holder = {"box": None}

        rag_prompt = SystemMessage(content = f'You are a helpful assistant. Use the pdf document from path ({st.session_state.uploaded_file}) if required')
        if st.session_state.uploaded_file:
            rag_prompt = SystemMessage(content = f'You are a helpful assistant. Use the pdf document from path ({st.session_state.uploaded_file}) if required')
            messages = [rag_prompt, HumanMessage(content = user_input)]
        else:
            messages = [HumanMessage(content = user_input)]
        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": messages},
                config=CONFIG,
                stream_mode="messages",
            ):
                # Lazily create & update the SAME status container when any tool runs
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Using `{tool_name}` …", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"🔧 Using `{tool_name}` …",
                            state="running",
                            expanded=True,
                        )

                # Stream ONLY assistant tokens
                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content

        ai_message = st.write_stream(ai_only_stream())

        # Finalize only if a tool was actually used
        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="✅ Tool finished", state="complete", expanded=False
            )



    st.session_state['message_history'].append({'role':'assistant', 'content': ai_message})
    
    set_thread_title(st.session_state['thread_id'])
