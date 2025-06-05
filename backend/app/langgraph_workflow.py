"""
LangGraph state-machine for the historical-monument chatbot
with e-mail + OTP verification flow.
"""

from __future__ import annotations

import logging
from typing import Optional, List, Dict

from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from backend.app.config import settings
from backend.app.monument_search import monument_search
from backend.app.otp import (
    generate_otp,
    store_otp,
    retrieve_stored_otp,
    delete_otp,
    is_valid_email,     # quick syntactic check
    find_email,         # ← NEW helper: pull e-mail out of a sentence
    extract_otp         # ← NEW helper: pull 6-digit code out of text
)
from backend.app.email_utils import (
    send_otp_email,     # keep OTP template
    send_plain_email    # ← NEW helper: generic, no OTP footer
)

# --------------------------------------------------------------------------- #
# Logging & LLM
# --------------------------------------------------------------------------- #

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

llm = ChatOpenAI(model="gpt-3.5-turbo", openai_api_key=settings.openai_api_key)

# --------------------------------------------------------------------------- #
# Chat-state dataclass
# --------------------------------------------------------------------------- #

class ChatState(BaseModel):
    messages: List[BaseMessage] = Field(default_factory=list)
    user_input: Optional[str] = None

    awaiting_email: bool = False
    awaiting_otp: bool = False
    email: Optional[str] = None
    otp_attempts: int = 0

    monument_results: List[Dict] = Field(default_factory=list)
    response: Optional[str] = None
    next_step: str = "process_user_input"

# --------------------------------------------------------------------------- #
#  Node: process_user_input
# --------------------------------------------------------------------------- #

def process_user_input(state: ChatState) -> ChatState:
    """
    Decide routing based on flags & fresh user_input.
    1. Awaiting_email  → try to extract an e-mail.
    2. Awaiting_otp    → try to extract a 6-digit code.
    3. Otherwise       → treat as a new monument query.
    """
    logger.info(
        "Processing user_input; awaiting_email=%s awaiting_otp=%s input=%r",
        state.awaiting_email, state.awaiting_otp, state.user_input,
    )

    # ------------------------------------------------------- #
    # Record message if present
    # ------------------------------------------------------- #
    if state.user_input:
        state.messages.append(HumanMessage(content=state.user_input))

    # ------------------------------------------------------- #
    # We are waiting for an e-mail address
    # ------------------------------------------------------- #
    if state.awaiting_email:
        if not state.user_input:          # nothing new yet
            state.next_step = END
            return state

        email = find_email(state.user_input)
        if email and is_valid_email(email):
            state.email = email
            state.awaiting_email = False
            state.next_step = "send_otp"
            logger.info("Valid e-mail extracted → send_otp")
            state.user_input = None
            return state

        # If no e-mail, treat entire text as a *new* monument question
        logger.info("No e-mail found; treating as new monument query.")
        state.awaiting_email = False
        # fall through to monument flow

    # ------------------------------------------------------- #
    # We are waiting for an OTP
    # ------------------------------------------------------- #
    if state.awaiting_otp:
        if not state.user_input:
            state.next_step = END
            return state

        code = extract_otp(state.user_input, digits=6)
        if code:
            logger.info("Extracted OTP %s → process_otp_input", code)
            state.next_step = "process_otp_input"
            return state

        # Still no 6-digit number
        msg = "Please enter the 6-digit code that was e-mailed to you."
        state.messages.append(AIMessage(content=msg))
        state.response = msg
        state.next_step = END
        return state

    # ------------------------------------------------------- #
    # Fresh monument query (default route)
    # ------------------------------------------------------- #
    state.next_step = "check_query_type"
    state.user_input = None
    return state

# --------------------------------------------------------------------------- #
#  Remaining nodes (monument flow, OTP flow, etc.)
# --------------------------------------------------------------------------- #

def check_query_type(state: ChatState) -> ChatState:
    query = state.messages[-1].content if state.messages else ""
    results = monument_search.search(query, k=1)
    if results:
        state.monument_results = results
        state.next_step = "generate_monument_response"
        logger.info("Monument found")
    else:
        state.next_step = "generate_non_monument_response"
        logger.info("No monument match")
    return state


def generate_monument_response(state: ChatState) -> ChatState:
    context = "\n".join(
        f"{m['name']} ({m['location']}): {m['description']}"
        for m in state.monument_results
    )
    user_q = state.messages[-1].content
    prompt = (
        "Using the information below, answer concisely.\n\n"
        f"User: {user_q}\n\nInformation:\n{context}\n\nBot:"
    )
    brief = llm.invoke(prompt).content.strip()
    reply = (
        brief
        + "\n\nIf you’d like more details e-mailed to you, please share your "
        "email address."
    )
    state.messages.append(AIMessage(content=reply))
    state.response = reply
    state.next_step = "ask_for_email"
    return state


def generate_non_monument_response(state: ChatState) -> ChatState:
    question = state.messages[-1].content
    prompt = (
        f"The user asked: {question}\n"
        "Please politely say you only answer questions about historical monuments."
    )
    answer = llm.invoke(prompt).content
    state.messages.append(AIMessage(content=answer))
    state.response = answer
    state.next_step = END
    return state


def ask_for_email(state: ChatState) -> ChatState:
    state.awaiting_email = True
    state.next_step = END
    return state


def send_otp_step(state: ChatState) -> ChatState:
    email = state.email
    otp = generate_otp()
    store_otp(email, otp, ttl_seconds=300)

    if send_otp_email(email, otp):
        msg = (
            f"Thank you. An OTP has been sent to {email}. "
            "Please enter the 6-digit code here to verify your email "
            "and receive more details."
        )
        state.awaiting_otp = True
    else:
        msg = (
            f"Sorry, I couldn’t send the OTP to {email}. "
            "Please check the address or provide a different one."
        )
        state.awaiting_email = True

    state.response = msg
    state.messages.append(AIMessage(content=msg))
    state.next_step = END
    return state


def process_otp_input(state: ChatState) -> ChatState:
    code = extract_otp(state.messages[-1].content, digits=6) or ""
    email = state.email
    stored = retrieve_stored_otp(email)

    if stored and code == stored:
        delete_otp(email)
        state.awaiting_otp = False
        state.next_step = "final_confirmation"
        msg = "Thank you! Your email is verified. I will send more details shortly."
        state.response = msg
        state.messages.append(AIMessage(content=msg))
        return state

    # Incorrect / expired
    state.otp_attempts += 1
    if state.otp_attempts >= 3 or stored is None:
        msg = "Too many incorrect attempts or code expired. Email verification failed."
        state.awaiting_otp = False
        state.next_step = "end_conversation"
    else:
        msg = "That code is incorrect. Please try again."
        state.next_step = END

    state.response = msg
    state.messages.append(AIMessage(content=msg))
    return state


def final_confirmation(state: ChatState) -> ChatState:
    """
    Compose a detailed guide and e-mail it *without* OTP footer.
    """
    email = state.email or ""
    last_q = state.messages[-1].content
    info = monument_search.search(last_q, k=1)

    if info:
        m = info[0]
        subject = f"More about {m['name']}"
        body = (
            f"Here’s more detailed information on {m['name']} ({m['location']}):\n\n"
            f"{m['description']}\n\nEnjoy your visit!"
        )
    else:
        subject = "Requested monument information"
        body = "Thank you for verifying. Stay tuned for more historical details."

    send_plain_email(email, subject, body)

    # reset for fresh session
    state.email = None
    state.next_step = END
    return state


def end_conversation(state: ChatState) -> ChatState:
    state.next_step = END
    return state

# --------------------------------------------------------------------------- #
# Build & compile graph
# --------------------------------------------------------------------------- #

graph = StateGraph(ChatState)

graph.add_node("process_user_input", process_user_input)
graph.add_node("check_query_type", check_query_type)
graph.add_node("generate_monument_response", generate_monument_response)
graph.add_node("generate_non_monument_response", generate_non_monument_response)
graph.add_node("ask_for_email", ask_for_email)
graph.add_node("send_otp", send_otp_step)
graph.add_node("process_otp_input", process_otp_input)
graph.add_node("final_confirmation", final_confirmation)
graph.add_node("end_conversation", end_conversation)

graph.set_entry_point("process_user_input")

graph.add_conditional_edges(
    "process_user_input",
    lambda s: s.next_step,
    {
        "send_otp": "send_otp",
        "process_otp_input": "process_otp_input",
        "check_query_type": "check_query_type",
        END: END,
    },
)
graph.add_conditional_edges(
    "check_query_type",
    lambda s: s.next_step,
    {
        "generate_monument_response": "generate_monument_response",
        "generate_non_monument_response": "generate_non_monument_response",
    },
)
graph.add_conditional_edges(
    "generate_monument_response",
    lambda s: s.next_step,
    {"ask_for_email": "ask_for_email", END: END},
)
graph.add_edge("generate_non_monument_response", END)
graph.add_edge("ask_for_email", END)
graph.add_edge("send_otp", END)
graph.add_conditional_edges(
    "process_otp_input",
    lambda s: s.next_step,
    {"final_confirmation": "final_confirmation", END: END, "end_conversation": "end_conversation"},
)
graph.add_edge("final_confirmation", END)
graph.add_edge("end_conversation", END)

compiled_chat_graph = graph.compile()

__all__ = ["compiled_chat_graph", "ChatState"]
