import streamlit as st
import os
from dotenv import load_dotenv
import httpx # Import httpx for making HTTP requests

# Load environment variables
load_dotenv()

# Backend API URL (adjust if your backend is running on a different host/port)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000") # Assuming FastAPI runs on port 8000

# Set page config
st.set_page_config(
    page_title="Historical Monument Agent", # Updated page title
    page_icon="🏛️", # Changed to a monument icon
    layout="centered" # Changed to centered layout for the card effect
)

# Custom CSS for overall styling based on the new sample image
st.markdown(
    """
    <style>
    /* Overall App Background (Teal Blue Gradient) */
    .stApp {
        background: linear-gradient(to bottom right, #008080, #20B2AA, #48D1CC); /* Ombre teal gradient */
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }

    /* Fixed-width White Card Container */
    section.main > div.block-container {
        max-width: 600px; /* Fixed width for the card */
        margin: 50px auto; /* Center the card with vertical margin */
        background-color: rgba(255, 255, 255, 0.95); /* White, slightly transparent */
        border-radius: 15px; /* Rounded corners */
        padding: 20px; /* Padding inside the card */
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2); /* Soft shadow */
        height: calc(100vh - 100px); /* Adjust height to fit viewport, leave space for margins */
        display: flex;
        flex-direction: column;
    }

    /* Chat History Container (Scrollable) */
    .st-emotion-cache-1jm6gsa { /* Target for the main chat messages column */
        flex-grow: 1;
        overflow-y: auto; /* Make chat history scrollable */
        padding-right: 15px; /* Space for scrollbar */
        margin-bottom: 10px; /* Space above input */
    }
    
    /* Individual Chat Messages - Rounded, Smaller, Aligned */
    .stChatMessage {
        max-width: 85% !important; /* Smaller width */
        border-radius: 18px; /* More rounded */
        padding: 12px 18px;
        margin-bottom: 10px;
        word-break: break-word; /* Ensure long words wrap */
        white-space: pre-wrap; /* Preserve whitespace and line breaks */
        background-color: #2F4F4F !important; /* Dark slate grey background */
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important; /* Stronger shadow */
    }
    
    /* User Messages (Dark Background, White Text) */
    .stChatMessage.st-chat-message-user {
        background-color: #2F4F4F !important; /* Dark slate grey background */
        color: white !important; /* White text for contrast */
        margin-left: auto; /* Align to right */
        margin-right: 0; /* No right margin */
        border-bottom-right-radius: 5px; /* Sharper corner for user message tail */
        border: 2px solid #1F3F3F !important; /* Even darker border */
    }
    .stChatMessage.st-chat-message-user div[data-testid="stMarkdownContainer"] p,
    .stChatMessage.st-chat-message-user div[data-testid="stMarkdownContainer"] {
        color: white !important;
        font-size: 1.2em !important; /* Apply to p tags within user messages */
        line-height: 1.4 !important; /* Improve readability */
    }

    /* Bot Messages (Dark Background, White Text, with Icon) */
    .stChatMessage.st-chat-message-assistant {
        background-color: #2F4F4F !important; /* Dark slate grey background */
        color: white !important; /* White text for contrast */
        margin-left: 0; /* Align to left */
        margin-right: auto; /* No left margin */
        border-bottom-left-radius: 5px; /* Sharper corner for assistant message tail */
        border: 2px solid #1F3F3F !important; /* Even darker border */
    }
    .stChatMessage.st-chat-message-assistant div[data-testid="stMarkdownContainer"] p,
    .stChatMessage.st-chat-message-assistant div[data-testid="stMarkdownContainer"] {
        color: white !important;
        font-size: 1.2em !important; /* Apply to p tags within assistant messages */
        line-height: 1.4 !important; /* Improve readability */
    }
    
    /* Chat Input Field Styling */
    div[data-testid="stForm"] div[data-testid="stTextInput"] div[data-testid="stDecoratedInput-container"] {
        border-radius: 25px; /* Rounded input field container */
        background-color: #F0F0F0; /* Light grey background for input area */
        border: 1px solid #D0D0D0; /* Subtle border */
        padding: 5px 15px; /* Adjust padding */
        box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1); /* Inner shadow */
    }
    div[data-testid="stForm"] div[data-testid="stTextInput"] div[data-testid="stDecoratedInput-container"] input {
        background-color: #F0F0F0 !important; /* Match input background */
        color: black !important; /* Text color for input field */
        padding: 8px 0; /* Vertical padding */
    }
    /* Placeholder text color */
    div[data-testid="stForm"] div[data-testid="stTextInput"] input::placeholder {
        color: #888888 !important; /* Darker placeholder */
    }

    /* Send Button Styling */
    div[data-testid="stForm"] button[data-testid="baseButton-secondary"] {
        background-color: transparent !important; /* No background */
        color: #6A5ACD !important; /* Purple icon color */
        border: none !important; /* No border */
        font-size: 1.8em; /* Larger icon */
        padding: 0; /* No padding */
    }
    div[data-testid="stForm"] button[data-testid="baseButton-secondary"] svg {
        fill: #6A5ACD !important; /* Ensure SVG color is purple */
    }

    /* Remove default Streamlit header/footer */
    header, footer {
        visibility: hidden;
        height: 0px;
    }

    /* Title styling */
    .st-emotion-cache-ue6h2c.e1nzilvr5 {
        color: #6A5ACD; /* Purple title */
        text-align: center;
        margin-bottom: 20px;
        font-weight: bold;
    }

    /* Typing indicator (will be implemented in Python) */
    .typing-indicator span {
        display: inline-block;
        background-color: #6A5ACD; /* Purple dots */
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin: 0 2px;
        animation: bounce 1s infinite alternate;
    }
    .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
    .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes bounce {
        0% { transform: translateY(0); }
        100% { transform: translateY(-10px); }
    }

    /* Ensure chat input area is centered and within the outer box */
    div[data-testid="stForm"] {
        max-width: 90% !important; /* Adjust to fit within the outer box */
        margin-left: auto;
        margin-right: auto;
        margin-top: 150px; /* Increased space above the input to shift it significantly up */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize session state for chat messages and flags
if "messages" not in st.session_state:
    st.session_state.messages = []
if "awaiting_email" not in st.session_state:
    st.session_state.awaiting_email = False
if "awaiting_otp" not in st.session_state:
    st.session_state.awaiting_otp = False
if "email" not in st.session_state:
    st.session_state.email = None
if "last_monument_query" not in st.session_state: # Initialize last_monument_query
    st.session_state.last_monument_query = None

# Function to display messages in chat format
def display_message(role, content, icon=None):
    if icon:
        with st.chat_message(role, avatar=icon):
            st.markdown(content)
    else:
        with st.chat_message(role):
            st.markdown(content)

# Main app
def main():
    st.title("🏛️Historical Monument Agent") # Updated title at the top of the card

    # Initial agent message (as seen in the image)
    if not st.session_state.messages:
        initial_agent_message = "Hey there 👋\nHow can I help you today?"
        st.session_state.messages.append({"role": "assistant", "content": initial_agent_message})

    # Display chat messages from session state
    for message in st.session_state.messages:
        if message["role"] == "assistant":
            display_message(message["role"], message["content"], icon="🤖") # Bot icon
        else:
            display_message(message["role"], message["content"]) # User message

    # User input
    user_query = None
    if not st.session_state.awaiting_email and not st.session_state.awaiting_otp:
        user_query = st.chat_input("Message...") # Updated placeholder text
    
    # Handle user input from chat_input or forms
    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query})
        # Ensure user_input in session state reflects the latest input
        st.session_state.user_input_from_frontend = user_query
        display_message("user", user_query)
    
    # Conditional rendering for email input
    if st.session_state.awaiting_email and not st.session_state.awaiting_otp:
        with st.form("email_form"):
            email_input = st.text_input("Please share your email address:", key="email_field")
            submit_email = st.form_submit_button("Send Email")

            if submit_email and email_input:
                # Set user_input in session state, which will trigger the API call on next rerun
                st.session_state.user_input_from_frontend = email_input
                st.rerun()

    # Conditional rendering for OTP input
    if st.session_state.awaiting_otp:
        with st.form("otp_form"):
            otp_input = st.text_input("Please enter the 6-digit code here to verify your email and receive more details.", key="otp_field")
            
            col1, col2 = st.columns(2) # Create two columns for buttons
            with col1:
                submit_otp = st.form_submit_button("Verify OTP")
            with col2:
                cancel_otp = st.form_submit_button("Cancel")

            if submit_otp and otp_input:
                # Set user_input in session state, which will trigger the API call on next rerun
                st.session_state.user_input_from_frontend = otp_input
                st.rerun()

            if cancel_otp:
                st.session_state.awaiting_email = False
                st.session_state.awaiting_otp = False
                st.session_state.email = None
                st.session_state.otp_attempts = 0
                st.session_state.user_input_from_frontend = None # Clear user input on cancel
                st.session_state.messages.append({"role": "assistant", "content": "Email verification cancelled. How can I help you now?"})
                st.rerun()

    # Make the backend API call only if there is a pending user_input_from_frontend
    if "user_input_from_frontend" in st.session_state and st.session_state.user_input_from_frontend is not None:
        # Show typing indicator
        typing_placeholder = st.empty()
        with typing_placeholder:
            st.markdown("<div class='typing-indicator'><span></span><span></span><span></span></div>", unsafe_allow_html=True)

        # st.info(f"Sending to backend: user_input='{st.session_state.user_input_from_frontend}', awaiting_email={st.session_state.awaiting_email}, awaiting_otp={st.session_state.awaiting_otp}, last_monument_query={st.session_state.last_monument_query}") # Frontend logging

        try:
            response = httpx.post(
                f"{BACKEND_URL}/chat",
                json={
                    "messages": st.session_state.messages,
                    "awaiting_email": st.session_state.awaiting_email,
                    "awaiting_otp": st.session_state.awaiting_otp,
                    "email": st.session_state.email,
                    "user_input": st.session_state.user_input_from_frontend,
                    "last_monument_query": st.session_state.last_monument_query # Send it to the backend
                },
                timeout=30 # Increased timeout for potential long responses
            )
            response.raise_for_status()  # Raise an exception for HTTP errors
            backend_response = response.json()

        except httpx.RequestError as e:
            st.error(f"Error connecting to backend: {e}")
        except httpx.HTTPStatusError as e:
            st.error(f"Backend error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
        finally:
            typing_placeholder.empty() # Clear typing indicator

        # Clear the user input from session state after sending to backend
        st.session_state.user_input_from_frontend = None

        agent_response = backend_response.get("response", "No response from agent.")
        st.session_state.awaiting_email = backend_response.get("awaiting_email", False)
        st.session_state.awaiting_otp = backend_response.get("awaiting_otp", False)
        st.session_state.email = backend_response.get("email", None)
        st.session_state.last_monument_query = backend_response.get("last_monument_query", None) # Update from backend

        st.session_state.messages.append({"role": "assistant", "content": agent_response})
        st.rerun() # Rerun to display the new message and potentially the email/OTP input

if __name__ == "__main__":
    main() 