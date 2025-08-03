import datetime
import json
import os
import time
import uuid

import anthropic
import dotenv
import streamlit as st

dotenv.load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"


def load_system_prompt():
    with open("system_prompt.md", encoding="utf-8") as f:
        return f.read()


SYSTEM_PROMPT = load_system_prompt()


def log_conversation(user_message, assistant_response, session_id):
    """Log conversation to JSONL file"""
    log_entry = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "session_id": session_id,
        "user_message": user_message,
        "assistant_response": assistant_response,
    }

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Append to log file
    with open("logs/chat_logs.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")


# Streamed response generator using Anthropic
def response_generator():
    try:
        # Create messages for the API call
        messages = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]

        # Get streaming response from Anthropic
        with client.messages.stream(
            model=ANTHROPIC_MODEL,
            messages=messages,
            system=SYSTEM_PROMPT,
            max_tokens=1000,
            temperature=0.2,
        ) as stream:
            yield from stream.text_stream

    except Exception as e:
        # Log the error
        log_conversation(messages, str(e), st.session_state.session_id)

        # Fallback response if API call fails
        error_response = f"Sorry, I encountered an error: {str(e)}"
        for word in error_response.split():
            yield word + " "
            time.sleep(0.05)


# Initialize session ID for tracking conversations
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

st.title("LLM Forecasting Aid (excessively preliminary)")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        response = st.write_stream(response_generator())
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

    # Log the conversation
    log_conversation(prompt, response, st.session_state.session_id)
