# Many Tiny Judges

Many Tiny Judges is a two-part project (Python backend + React frontend) that sends a reasoning question through multiple AI "judge" roles and then synthesizes a final answer through a Chief Arbiter.

## What it does

Given a single question, the backend runs:

- **Domain Expert**
- **Adversarial Skeptic**
- **Fact Verifier**
- **Chief Arbiter** (final consolidation)

The frontend provides a desktop-style interface to submit questions, inspect judge status, and view the final verdict.

## Key features

- Multi-role reasoning pipeline in `backend/app.py`
- Flask API with CORS in `backend/server.py`
- React + Vite GUI in `frontend/src/main.jsx`
- Terminal demo client in `backend/terminal_demo.py`
- Health endpoint at `/api/health`

## Repository structure

```text
many_tiny_judges/
├─ backend/
│  ├─ app.py              # Judge pipeline and arbiter logic
│  ├─ server.py           # Flask API server
│  ├─ terminal_demo.py    # CLI demo client for the backend
│  └─ README.txt
└─ frontend/
   ├─ src/
   │  ├─ main.jsx         # React app entry and UI logic
   │  └─ styles.css       # UI styling
   ├─ package.json
   └─ package-lock.json
```

## Prerequisites

- Python 3
- Node.js + npm
- A Google AI Studio API key (exported as `GOOGLE_API_KEY`)

## Setup

### 1) Backend

From the repository root:

```bash
cd backend
python -m pip install flask flask-cors google-genai pydantic
```

Set your API key:

```bash
export GOOGLE_API_KEY="your_api_key_here"
```

If `GOOGLE_API_KEY` is not set, `server.py` prompts for it interactively at startup.

### 2) Frontend

From the repository root:

```bash
cd frontend
npm install
```

## Run the project

Use two terminals.

### Terminal 1: start backend API

```bash
cd backend
python server.py
```

Backend runs on `http://127.0.0.1:5000`.

### Terminal 2: start frontend

```bash
cd frontend
npm run dev
```

Open the Vite local URL shown in the terminal (typically `http://127.0.0.1:5173`).

## API

### `GET /api/health`

Returns service status and model id.

### `POST /api/analyze`

Request body:

```json
{
  "question": "If it takes 5 machines 5 minutes to make 5 widgets, how long for 100 machines to make 100 widgets?"
}
```

The response is JSON generated from the backend judge pipeline result.

## Terminal demo usage

After starting the backend:

```bash
cd backend
python terminal_demo.py
```

It prompts for a question (or uses a built-in example) and prints the backend response sections.

## Frontend scripts

From `frontend/`:

```bash
npm run dev      # start Vite dev server
npm run build    # production build
npm run preview  # preview built app
```

## Testing and linting

No dedicated test or lint scripts are currently defined in this repository's `package.json`, and no Python test configuration is present.

## Development notes

- Frontend API URL is hardcoded to `http://127.0.0.1:5000` in `frontend/src/main.jsx`.
- Backend model id is set in `backend/app.py` as `gemma-4-26b-a4b-it`.

## Contributing

1. Create a branch for your change.
2. Keep changes focused and small.
3. Run the backend and frontend locally to verify behavior.
4. Open a pull request with a clear summary and rationale.
