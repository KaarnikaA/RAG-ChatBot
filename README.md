# Federal Documents RAG Chat System

A retrieval-augmented generation (RAG) chat system that provides information about recent federal documents and regulations. This system fetches daily updates from the Federal Register API, stores them in a MySQL database, and allows users to query this information through a chat interface powered by an LLM.

## Features

- **Daily Data Updates**: Automatically fetches and processes new documents from the Federal Register API
- **Asynchronous Processing**: Uses asyncio for non-blocking operations
- **LLM-Powered Chat**: Uses Ollama to provide intelligent responses based on federal documents
- **Document Browser**: View recent federal documents with summaries
- **Simple, Clean UI**: Easy-to-use chat interface

## System Architecture

The system consists of four main components:

1. **Data Pipeline**: Fetches, processes, and stores federal documents
2. **Agent**: Interfaces with the LLM to generate responses based on the data
3. **API**: Provides endpoints for the frontend to communicate with the backend
4. **UI**: User interface for interacting with the system

## Setup and Installation

### Prerequisites

- Python 3.8+
- MySQL Server
- [Ollama](https://ollama.ai/) - For running the LLM locally

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# Database Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=federal_docs_db

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=mistral:latest
REQUEST_TIMEOUT=60
MAX_TOKENS=1000
```

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/federal-docs-rag.git
cd federal-docs-rag
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python -m backend.db_init
```

4. Run the data pipeline to fetch initial data:
```bash
python -m pipelines.fetch_fed_register
```

### Running the Application

1. Start the backend server:
```bash
python -m backend.main
```

2. Open the frontend in your browser:
```bash
# Either serve the frontend files using a simple HTTP server
python -m http.server 8080 --directory frontend
```

3. Access the application at `http://localhost:8080`

## Usage

1. Ask questions about federal regulations in the chat interface
2. View recent federal documents in the Documents tab
3. Monitor system status in the header

## Maintenance

- The data pipeline should be scheduled to run daily (e.g., using cron)
- Monitor the logs for any errors or issues
- Update the LLM model as needed in the .env file

## Project Structure

```
federal-docs-rag/
├── backend/
│   ├── agent.py         # LLM interaction and response generation
│   ├── db_utils.py      # Database utility functions
│   ├── main.py          # FastAPI server implementation
│   └── tools.py         # Tools for document retrieval
├── frontend/
│   └── index.html       # User interface
├── pipelines/
│   └── fetch_fed_register.py  # Data pipeline for Federal Register
├── .env                 # Environment variables
└── README.md            # This file
```

## License

MIT License
