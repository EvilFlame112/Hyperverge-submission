# SensAI Docker Compose Setup

This directory contains Docker Compose configurations for running the SensAI API services in both development and production environments.

## 📁 File Structure

```
sensai-ai/
├── docker-compose.yml          # Development configuration
├── docker-compose.prod.yml     # Production configuration
├── env.example                 # Environment variables template
├── nginx/
│   ├── nginx.conf             # Development Nginx configuration
│   └── nginx.prod.conf        # Production Nginx configuration
└── DOCKER_COMPOSE_README.md   # This file
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git (to clone the repository)
- At least 4GB of available RAM
- At least 10GB of available disk space

### 1. Environment Setup

1. Copy the environment template:

   ```bash
   cp env.example .env
   ```

2. Edit `.env` and fill in your configuration:

   ```bash
   # Required
   OPENAI_API_KEY=your_openai_api_key_here
   GOOGLE_CLIENT_ID=your_google_client_id_here

   # Optional
   ENV=development
   S3_BUCKET_NAME=your_s3_bucket_name
   S3_FOLDER_NAME=your_s3_folder_name
   ```

### 2. Development Environment

Start the development environment:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Services Available:**

- **Main API**: http://localhost:8000
- **Public API**: http://localhost:8002
- **Redis**: localhost:6379
- **Nginx**: http://localhost:80 (optional, use `--profile production`)

### 3. Production Environment

Start the production environment:

```bash
# Start with production profile
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

## 🔧 Configuration

### Environment Variables

| Variable                           | Required | Description                          | Default     |
| ---------------------------------- | -------- | ------------------------------------ | ----------- |
| `OPENAI_API_KEY`                   | Yes      | OpenAI API key                       | -           |
| `GOOGLE_CLIENT_ID`                 | Yes      | Google OAuth client ID               | -           |
| `ENV`                              | No       | Environment (development/production) | development |
| `S3_BUCKET_NAME`                   | No       | S3 bucket for file storage           | -           |
| `S3_FOLDER_NAME`                   | No       | S3 folder name                       | -           |
| `BUGSNAG_API_KEY`                  | No       | Bugsnag error tracking               | -           |
| `PHOENIX_ENDPOINT`                 | No       | Phoenix observability endpoint       | -           |
| `PHOENIX_API_KEY`                  | No       | Phoenix API key                      | -           |
| `SLACK_USER_SIGNUP_WEBHOOK_URL`    | No       | Slack webhook for user signups       | -           |
| `SLACK_COURSE_CREATED_WEBHOOK_URL` | No       | Slack webhook for course creation    | -           |
| `SLACK_USAGE_STATS_WEBHOOK_URL`    | No       | Slack webhook for usage stats        | -           |

### Services

#### 1. SensAI API (`sensai-api`)

- **Port**: 8000
- **Description**: Main FastAPI application
- **Health Check**: `/health` endpoint
- **Features**:
  - User authentication
  - Course management
  - Task management
  - Chat functionality
  - File uploads

#### 2. SensAI Public API (`sensai-public-api`)

- **Port**: 8002
- **Description**: Public API for external integrations
- **Health Check**: `/health` endpoint
- **Features**:
  - Public course access
  - Chat history retrieval
  - API key authentication

#### 3. Redis (`redis`)

- **Port**: 6379
- **Description**: Caching and session management
- **Features**:
  - Session storage
  - API response caching
  - Rate limiting data

#### 4. Nginx (`nginx`)

- **Ports**: 80 (HTTP), 443 (HTTPS)
- **Description**: Reverse proxy and load balancer
- **Features**:
  - SSL termination
  - Rate limiting
  - Gzip compression
  - Security headers
  - Load balancing

## 🛠️ Development Commands

### Basic Operations

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d sensai-api

# View logs
docker-compose logs -f sensai-api

# Execute command in container
docker-compose exec sensai-api python -c "print('Hello World')"

# Rebuild and restart
docker-compose up -d --build

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Database Operations

```bash
# Access SQLite database
docker-compose exec sensai-api sqlite3 /appdata/db.sqlite

# Backup database
docker-compose exec sensai-api cp /appdata/db.sqlite /appdata/db.sqlite.backup

# Restore database
docker-compose exec sensai-api cp /appdata/db.sqlite.backup /appdata/db.sqlite
```

### Logs and Monitoring

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f sensai-api

# View nginx logs
docker-compose logs -f nginx

# Check service health
curl http://localhost:8000/health
curl http://localhost:8002/health
```

## 🔒 Production Deployment

### 1. SSL Certificate Setup

For production, you need SSL certificates:

```bash
# Create SSL directory
mkdir -p nginx/ssl

# Generate self-signed certificate (for testing)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem
```

### 2. Production Environment Variables

Create a production `.env` file:

```bash
# Copy and edit production environment
cp env.example .env.prod
```

Set production-specific variables:

```bash
ENV=production
OPENAI_API_KEY=your_production_openai_key
GOOGLE_CLIENT_ID=your_production_google_client_id
# ... other production variables
```

### 3. Start Production Services

```bash
# Start production environment
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Check service status
docker-compose -f docker-compose.prod.yml ps

# View production logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 4. Production Monitoring

```bash
# Check resource usage
docker stats

# Monitor logs
docker-compose -f docker-compose.prod.yml logs -f --tail=100

# Health checks
curl -k https://localhost/health
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
# Check what's using the port
lsof -i :8000

# Stop conflicting service or change port in docker-compose.yml
```

#### 2. Permission Issues

```bash
# Fix volume permissions
sudo chown -R $USER:$USER ./src
```

#### 3. Database Issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d
```

#### 4. Memory Issues

```bash
# Check memory usage
docker stats

# Increase Docker memory limit in Docker Desktop settings
```

### Debugging

#### 1. Container Access

```bash
# Access running container
docker-compose exec sensai-api bash

# Check container logs
docker-compose logs sensai-api
```

#### 2. Network Issues

```bash
# Check network connectivity
docker-compose exec sensai-api ping redis

# Inspect network
docker network ls
docker network inspect sensai-ai_sensai-network
```

#### 3. Volume Issues

```bash
# Check volume mounts
docker-compose exec sensai-api ls -la /appdata

# Inspect volumes
docker volume ls
docker volume inspect sensai-ai_sensai_data
```

## 📊 Performance Optimization

### Development

- Use volume mounts for code changes
- Enable hot reload with `--reload` flag
- Use single worker for debugging

### Production

- Use multiple workers (`--workers 4`)
- Enable Redis for caching
- Use Nginx for load balancing
- Implement proper SSL/TLS
- Set resource limits

## 🔐 Security Considerations

### Development

- Use environment variables for secrets
- Don't commit `.env` files
- Use development SSL certificates

### Production

- Use proper SSL certificates
- Implement rate limiting
- Set security headers
- Use strong passwords
- Regular security updates
- Monitor access logs

## 📝 Maintenance

### Regular Tasks

1. **Update Dependencies**

   ```bash
   docker-compose pull
   docker-compose up -d --build
   ```

2. **Backup Database**

   ```bash
   docker-compose exec sensai-api cp /appdata/db.sqlite /appdata/db.sqlite.$(date +%Y%m%d)
   ```

3. **Clean Up**

   ```bash
   docker system prune -f
   docker volume prune -f
   ```

4. **Monitor Logs**
   ```bash
   docker-compose logs --tail=100 -f
   ```

## 🤝 Contributing

When contributing to the Docker setup:

1. Test changes in development environment
2. Update documentation
3. Test production deployment
4. Follow security best practices
5. Update environment variables template

## 📞 Support

For issues with the Docker setup:

1. Check the troubleshooting section
2. Review logs: `docker-compose logs -f`
3. Check service health: `curl http://localhost:8000/health`
4. Verify environment variables
5. Check Docker and Docker Compose versions

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Redis Documentation](https://redis.io/documentation)
