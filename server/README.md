# Clarity API

Clarity API is the backend service for the Clarity client and project management application. It provides REST APIs for creating, updating, deleting, and retrieving client projects, plus dashboard summaries and team-level analytics.

## Features

- CRUD operations for client projects
- Project completion and reopen actions
- Dashboard summary metrics
- Deadline alerts
- Team contribution and payout insights
- Firebase Firestore integration
- CORS-enabled FastAPI app

## Tech Stack

- Python 3.13
- FastAPI
- Pydantic
- Firebase Admin SDK
- Google Cloud Firestore

## Project Structure

```text
server/
├── app/
│   ├── api/
│   │   └── router/
│   │       └── client.py
│   ├── core/
│   │   ├── config.py
│   │   └── firebase.py
│   ├── model/
│   │   ├── __init__.py
│   │   └── client.py
│   ├── repository/
│   │   └── client_repository.py
│   ├── service/
│   │   └── client_service.py
│   ├── __init__.py
│   └── main.py
├── requirements.txt
├── .gitignore
├── README.md
└── serviceAccountKey.json
```

## Prerequisites

Before running the backend, make sure you have:

- Python 3.11+
- A Firebase project with Firestore enabled
- A Firebase service account JSON key

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment variables

Create a `.env` file in the server directory for local development. Example:

```env
APP_NAME=Clarity
DEBUG=true
CORS_ORIGINS=http://localhost:5173
FIREBASE_CREDENTIALS_PATH=serviceAccountKey.json
```

## Firebase setup

Place your Firebase Admin service account JSON file in the server directory as:

```text
serviceAccountKey.json
```

This file is secret and should never be committed to Git.

## Run locally

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

```text
http://localhost:8000
```

## API endpoints

### Clients

- `GET /api/v1/clients`
- `GET /api/v1/clients/{client_id}`
- `POST /api/v1/clients`
- `PATCH /api/v1/clients/{client_id}`
- `DELETE /api/v1/clients/{client_id}`
- `POST /api/v1/clients/{client_id}/complete`
- `POST /api/v1/clients/{client_id}/reopen`

### Dashboard

- `GET /api/v1/dashboard/summary`
- `GET /api/v1/dashboard/deadline-alerts?days=7`
- `GET /api/v1/team`

## Production deployment

For production, deploy this service on Render or any Python hosting platform that supports FastAPI.

### Required environment variables on Render

```env
APP_NAME=Clarity
DEBUG=false
CORS_ORIGINS=https://your-frontend-domain.netlify.app
FIREBASE_CREDENTIALS_PATH=/etc/secrets/serviceAccountKey.json
```

In production, use a secure secret file or environment variable injection for the Firebase credentials instead of committing them to source control.

## Notes

- The backend should be treated as a separate service from the frontend.
- The frontend uses a local proxy in development, but production should talk directly to the deployed backend URL.
- Firestore document IDs are created automatically by Firestore and used as the client/project identifier.

## License

This project is for internal or personal use unless otherwise specified.
