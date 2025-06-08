# Historical Monument Agent

This is a conversational AI chatbot, the **Historical Monument Agent**, designed to provide information about historical monuments. The agent leverages a FastAPI backend for its core logic and uses Streamlit for a rich, interactive user interface.

## Features:
- **Conversational AI:** Ask questions about various historical monuments.
- **Email Integration:** Optionally receive detailed information about monuments via email after OTP verification.
- **Interactive UI:** Built with Streamlit for an engaging chat experience.

## Technologies Used:
- **Frontend:** Streamlit
- **Backend:** FastAPI, LangGraph, OpenAI, FAISS, Redis
- **Email Service:** SendGrid (for OTP and detailed emails)

## Setup and Installation:

### Prerequisites:
- Python 3.9+
- pip (Python package installer)
- Redis server (for backend state management and OTP storage)
- OpenAI API Key
- SendGrid API Key (for email functionalities)

### Local Development Setup:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/vaishnavibhavsar1510/Historical_Monument_Agent_Streamlit.git
    cd Historical_Monument_Agent_Streamlit
    ```

2.  **Create and activate virtual environments:**

    *   **For the Backend:**
        ```bash
        cd backend
        python -m venv venv
        .\venv\Scripts\activate  # On Windows
        # source venv/bin/activate  # On macOS/Linux
        pip install -r requirements.txt
        cd .. # Go back to project root
        ```

    *   **For the Frontend (Streamlit):**
        ```bash
        python -m venv venv
        .\venv\Scripts\activate  # On Windows
        # source venv/bin/activate  # On macOS/Linux
        pip install -r requirements.txt
        ```

3.  **Configure Environment Variables:**
    Create a `.env` file in the project root (`Historical_Monument_Agent_Streamlit/`) with the following:
    ```
    OPENAI_API_KEY="your_openai_api_key_here"
    SENDGRID_API_KEY="your_sendgrid_api_key_here"
    REDIS_URL="redis://localhost:6379/0" # Or your Redis connection string
    BACKEND_URL="http://localhost:8000" # Default for local FastAPI backend
    ```
    *Replace `your_openai_api_key_here` and `your_sendgrid_api_key_here` with your actual keys.*

4.  **Run the Backend (FastAPI):**
    Open a new terminal, navigate to the `backend/` directory, activate its virtual environment, and run:
    ```bash
    cd backend
    .\venv\Scripts\activate  # On Windows
    # source venv/bin/activate  # On macOS/Linux
    uvicorn app.main:app --reload
    ```
    The backend will run on `http://localhost:8000` by default.

5.  **Run the Frontend (Streamlit):**
    Open another terminal, navigate to the project root (`Historical_Monument_Agent_Streamlit/`), activate its virtual environment, and run:
    ```bash
    streamlit run app.py
    ```
    Your Streamlit app will open in your web browser.

## Deployment:

This project can be deployed on platforms like Render (for FastAPI backend) and Streamlit Community Cloud (for Streamlit frontend). Ensure all `requirements.txt` files are updated and environment variables are configured on your chosen deployment platforms.

For `backend/requirements.txt`:
```
fastapi
uvicorn
langchain
langgraph
openai
faiss-cpu
redis
python-dotenv
sendgrid
pydantic
httpx
pydantic-settings
langchain-community
starlette-context==0.3.6
starlette-sessions==0.3.0
itsdangerous==2.2.0
langchain-openai
```

For `requirements.txt` (at project root, for Streamlit):
```
streamlit
httpx
python-dotenv
```

*(Note: Always generate your `requirements.txt` files using `pip freeze > requirements.txt` after installing all dependencies to ensure accurate versions.)*
