# SensAI Local Development Setup

## Overview
Both repositories have been cloned and set up for local development.

## Setup Summary

### ✅ Completed:
1. **Backend (sensai-ai)**: 
   - Repository cloned
   - `.env` file created with required environment variables
   - Note: Dependencies installation was skipped due to Windows uvloop compatibility issue

2. **Frontend (sensai-frontend)**:
   - Repository cloned  
   - Dependencies installed via `pnpm install`
   - `.env.local` file created from `.env.example`

3. **Docker Setup**:
   - Created `docker-compose.local.yml` that builds from source instead of pulling pre-built images

## Running the Application

### Option 1: Using Docker (Recommended for avoiding Python dependencies issues)

```bash
# Build and run both services
docker compose -f docker-compose.local.yml up --build

# The services will be available at:
# - Backend API: http://localhost:8000
# - Frontend: http://localhost:3000
# - API Documentation: http://localhost:8000/docs
```

### Option 2: Running Individually (Development Mode)

#### Backend:
```bash
cd sensai-ai

# Install dependencies (fix uvloop issue first by removing it from requirements.txt)
# Edit requirements.txt and remove or comment out line 31: uvloop==0.21.0
pip install -r requirements.txt

# Initialize database
cd src && python startup.py

# Run the API
uvicorn api.main:app --reload --port 8001
# Available at: http://localhost:8001
```

#### Frontend:
```bash
cd sensai-frontend

# Already installed dependencies with pnpm install
# Run development server
pnpm dev
# Available at: http://localhost:3000
```

## Environment Configuration

### Backend (.env)
Update `sensai-ai/.env` with your actual values:
- `GOOGLE_CLIENT_ID`: Your Google OAuth client ID
- `OPENAI_API_KEY`: Your OpenAI API key

### Frontend (.env.local)
Update `sensai-frontend/.env.local` with your actual values:
- `GOOGLE_CLIENT_ID` & `GOOGLE_CLIENT_SECRET`: Google OAuth credentials
- `NEXTAUTH_SECRET`: A random secret for NextAuth
- `JUDGE0_API_URL`: Judge0 API endpoint for code execution

## Known Issues

1. **uvloop on Windows**: The backend's `uvloop==0.21.0` dependency doesn't support Windows. Either:
   - Use Docker (recommended)
   - Remove uvloop from requirements.txt for local development

2. **Pre-built Docker Images**: The original docker-compose files reference private Docker Hub images. Use `docker-compose.local.yml` instead.

## Next Steps

1. Fill in the actual API keys and credentials in the .env files
2. Choose your preferred running method (Docker or individual)
3. Test the health endpoints:
   - Backend health: http://localhost:8000/health
   - Frontend: http://localhost:3000