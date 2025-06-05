# 🏛️ **Historical Monument Explorer Agent** (Using Langgraph)

## Overview 

Welcome to the Historical Monument Explorer! This project is a sophisticated AI-powered chatbot designed to act as your personal **Virtual Tour Agent**, providing fascinating information about famous historical monuments from around the globe. It features an intelligent backend orchestrated by LangGraph and a modern, interactive frontend built with Next.js.

## ✨ Features

-   **Interactive Chat:** Engage in natural language conversations about historical monuments.
-   **Monument Information:** Get concise summaries and details about various landmarks.
-   **Email Integration:** Request and receive more detailed information via email after a secure OTP verification process.
-   **Dynamic UI:** A modern, eye-catching user interface with a monument-themed background and real-time loading indicators.
-   **Conversational Flow:** Intelligent handling of different user intents, including monument queries, email input, and OTP verification.

## 🛠️ Tools & Technologies

### Backend

-   **Framework:** [FastAPI](https://fastapi.tiangolo.com/) - A modern, fast (high-performance), web framework for building APIs with Python.
-   **State Management/Workflow:** [LangGraph](https://langchain-ai.github.io/langgraph/) - A library for building stateful, multi-actor applications with LLMs, modeling the conversation as a graph.
-   **LLM Integration:** [LangChain](https://www.langchain.com/), [langchain-openai](https://github.com/langchain-ai/langchain-openai), [langchain-community](https://github.com/langchain-ai/langchain-community) - Libraries for developing applications powered by language models.
-   **Vector Store:** [FAISS-CPU](https://github.com/facebookresearch/faiss) - A library for efficient similarity search and clustering of dense vectors.
-   **Caching/OTP Storage:** [Redis](https://redis.io/) - An in-memory data structure store, used here for managing conversation state and OTPs.
-   **Environment Variables:** [python-dotenv](https://github.com/theskumar/python-dotenv) - Loads environment variables from a `.env` file.
-   **Email Sending:** [SendGrid](https://sendgrid.com/) - A platform for transactional and marketing email (requires SendGrid API key).
-   **Data Validation:** [Pydantic](https://pydantic.dev/), [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - For data parsing and validation using Python type hints.
-   **HTTP Client:** [httpx](https://www.python-httpx.org/) - A fully featured HTTP client for Python.
-   **Server:** [Uvicorn](https://www.uvicorn.org/) - An ASGI server implementation, used to serve the FastAPI application.
-   **Other:** itsdangerous - A library to safely pass trusted data to untrusted environments.

### Frontend

-   **Framework:** [Next.js](https://nextjs.org/) (React) - A React framework for building full-stack web applications.
-   **Language:** [TypeScript](https://www.typescriptlang.org/) - A typed superset of JavaScript that compiles to plain JavaScript.
-   **Styling:** CSS Modules - For component-level styling.
-   **Unique ID Generation:** [uuid](https://www.npmjs.com/package/uuid) - For generating unique session IDs.

## 🤖 Agent System Architecture (LangGraph Workflow)

The backend agent system is designed as a state machine using LangGraph to manage the flow of conversation and interactions. The core is the `ChatState`, which tracks the conversation history, user input, and flags for controlling the flow (e.g., waiting for email or OTP).

Here's a simplified view of the LangGraph workflow steps:

1.  ➡️ **`process_user_input`**: Entry point for each user message. Based on the current state (e.g., `awaiting_email`, `awaiting_otp`) and the input, it directs the conversation flow.
    *   *Tools Used:* None (Routing logic)
2.  🔍 **`check_query_type`**: Analyzes the user's query to determine if it's related to a historical monument using semantic search.
    *   *Tools Used:* FAISS (via `MonumentSearch`), LLM (potentially for rephrasing or initial understanding).
3.  💬 **`generate_monument_response`**: If a monument is identified, an LLM generates a concise answer based on retrieved information and offers to send more details via email.
    *   *Tools Used:* LLM (ChatOpenAI).
4.  ❌ **`generate_non_monument_response`**: If the query is not about a monument, the LLM generates a polite, canned response.
    *   *Tools Used:* LLM (ChatOpenAI).
5.  📧 **`ask_for_email`**: Transitions the state to `awaiting_email`, prompting the user for their email address.
    *   *Tools Used:* None (State update).
6.  📬 **`send_otp_step`**: Triggered when a potential email is detected. Generates a unique OTP, stores it temporarily in Redis, and sends an email containing the OTP.
    *   *Tools Used:* Redis, SendGrid.
7.  🔑 **`process_otp_input`**: Handles user input when waiting for an OTP. Validates the provided code against the stored OTP in Redis. Manages incorrect attempts.
    *   *Tools Used:* Redis.
8.  ✅ **`final_confirmation`**: Executed after successful OTP verification. Retrieves detailed monument information and sends a comprehensive email to the user.
    *   *Tools Used:* FAISS (via `MonumentSearch`), SendGrid.
9.  🔚 **`end_conversation`**: A termination point in the graph, used for certain flow endings (e.g., failed OTP verification).

The state (`ChatState`) is persisted in Redis between turns, allowing the conversation to maintain context across multiple user interactions within a session.

## 💡 Use Cases

-   Quickly obtain facts and information about historical monuments worldwide.
-   Receive detailed guides and information directly to your email after verification.
-   Explore the capabilities of an AI agent built with LangGraph for managing complex conversational flows.

## 🚀 Getting Started

Follow these steps to set up and run the Historical Monument Explorer chatbot locally.

### Prerequisites

-   Python 3.8+ and pip
-   Node.js (LTS recommended) and npm
-   [Redis server](https://redis.io/docs/getting-started/installation/) running locally or accessible via a URL.
-   [OpenAI API Key](https://platform.openai.com/api-keys)
-   [SendGrid API Key](https://docs.sendgrid.com/ui/account-and-settings/api-keys)

### Cloning the Repository

```bash
git clone <https://github.com/vaishnavibhavsar1510/Historic_Agent_Bot.git> # Replace with your repository URL
cd Bot_Agent # Or the name of your cloned directory
```

### Backend Setup

1.  Navigate to the `backend` directory:
    ```bash
    cd backend
    ```
2.  Create and activate a Python virtual environment:
    ```bash
    # On Windows
    python -m venv .venv
    .venv\Scripts\activate

    # On macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```
3.  Install backend dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Create a `.env` file in the `backend` directory and add your API keys and Redis URL:
    ```env
    OPENAI_API_KEY='YOUR_OPENAI_API_KEY'
    SENDGRID_API_KEY='YOUR_SENDGRID_API_KEY'
    REDIS_URL='redis://localhost:6379/0' # Adjust if your Redis server is elsewhere
    ```
    Replace the placeholder values with your actual keys and URL.

### Frontend Setup

1.  Navigate to the `frontend/nextjs-app` directory:
    ```bash
    cd ../frontend/nextjs-app
    ```
2.  Install frontend dependencies:
    ```bash
    npm install
    ```

### Running the Application

1.  **Start the Backend:**
    Open a terminal, navigate to the `backend` directory, activate your virtual environment, and run:
    ```bash
    cd backend
    uvicorn app.main:app --reload
    ```
    *(Alternatively, from the project root: `python -m uvicorn backend.app.main:app --reload`)*

2.  **Start the Frontend:**
    Open *another* terminal, navigate to the `frontend/nextjs-app` directory, and run:
    ```bash
    cd frontend/nextjs-app
    npm install
    npm run dev
    ```

The frontend application will start on `http://localhost:3000` (or another port if configured in `frontend/nextjs-app/.env`).

## 🎯 How to Use

1.  Access the chatbot UI by opening your web browser to `http://localhost:3000`.
2.  Type your questions about historical monuments in the input box and press Send.
3.  Follow the prompts for email verification if you wish to receive more detailed information.
4.  Observe the dynamic loading indicator while the bot is processing your request.

## 📁 Project Structure

```
Bot_Agent/
├── backend/                # Backend application files
│   ├── app/
│   │   ├── ...             # Backend Python modules
│   │   └── main.py         # FastAPI application entry point
│   └── requirements.txt    # Python dependencies
├── data/
│   └── monuments.json      # Data for monument search
├── frontend/               # Frontend application files
│   └── nextjs-app/
│       ├── public/
│       │   └── monument-bg.png # Background image (add your file here)
│       ├── src/
│       │   ├── app/
│       │   │   ├── api/            # API routes (frontend proxy)
│       │   │   ├── ...
│       │   │   ├── page.module.css # CSS Modules for styling
│       │   │   └── page.tsx        # Main chat page component
│       │   └── ...
│       ├── package.json          # Frontend dependencies
│       └── ...
└── README.md               # Project README file
```

## 📈 Future Improvements

-   Integrate a wider range of monuments and data sources.
-   Implement more advanced natural language processing for complex queries.
-   Add support for different LLM providers.
-   Enhance the email content formatting.
-   Improve error handling and feedback mechanisms.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details (Note: You may need to create a LICENSE file with the MIT license text if you don't have one).

## 🤝 Contributing

Contributions are welcome! If you'd like to contribute, please fork the repository and submit a pull request. For major changes, please open an issue first to discuss what you would like to change.

## 👥 Authors

-   [ Vaishnavi Bhavsar ] Link to your GitHub profile:https://github.com/vaishnavibhavsar1510

## 📞 Support or Contact

If you have any questions or need support, please open an issue on the GitHub repository or contact [vaishnavibhavsar03@email.com].
