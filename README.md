# SensAI - AI-Powered Learning Platform

A comprehensive AI-powered learning platform with FastAPI backend and Next.js frontend.

## 🏗️ Project Structure

```
Hyperverge/
├── sensai-ai/           # FastAPI Backend
├── sensai-frontend/     # Next.js Frontend
└── README.md           # This file
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+
- Python 3.11+

### 1. Environment Setup

```bash
# Backend
cd sensai-ai
cp env.example .env
# Edit .env with your API keys

# Frontend
cd ../sensai-frontend
cp .env.example .env.local
# Edit .env.local with your configuration
```

### 2. Start Services

```bash
# Backend
cd sensai-ai
docker-compose up -d

# Frontend
cd ../sensai-frontend
npm install
npm run dev
```

## 🌐 Services

| Service         | URL                        | Description           |
| --------------- | -------------------------- | --------------------- |
| **Frontend**    | http://localhost:3000      | Next.js application   |
| **Backend API** | http://localhost:8000      | FastAPI main API      |
| **API Docs**    | http://localhost:8000/docs | Swagger documentation |

## 🔧 Environment Variables

### Backend (.env)

```bash
OPENAI_API_KEY=your_openai_api_key
GOOGLE_CLIENT_ID=your_google_client_id
ENV=development
```

### Frontend (.env.local)

```bash
NEXTAUTH_SECRET=your_nextauth_secret
NEXTAUTH_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🛠️ Development

### Backend

```bash
cd sensai-ai
pip install -r requirements.txt
uvicorn src.api.main:app --reload --port 8000
```

### Frontend

```bash
cd sensai-frontend
npm install
npm run dev
```

## 🐳 Docker

```bash
# Backend
cd sensai-ai
docker-compose up -d

# Frontend
cd ../sensai-frontend
docker-compose -f docker-compose.dev.yml up -d
```

## 🔒 Security

- Never commit `.env` files
- Use `.env.example` as templates
- Keep API keys secure

## 📚 Documentation

- [Backend API Docs](http://localhost:8000/docs)
- [Frontend README](./sensai-frontend/README.md)
- [Docker Setup](./sensai-ai/DOCKER_COMPOSE_README.md)

## 🆘 Support

For issues:

1. Check troubleshooting sections in individual READMEs
2. Review logs: `docker-compose logs -f`
3. Open an issue on GitHub

---

**Built with ❤️ using FastAPI, Next.js, and Docker**
