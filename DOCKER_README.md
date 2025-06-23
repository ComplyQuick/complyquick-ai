# ComplyQuick AI - Docker Deployment Guide

This guide explains how to deploy the ComplyQuick AI service using Docker and Docker Compose.

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)
- At least 4GB of available RAM
- 10GB of available disk space

## Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd complyquick-ai
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# AWS Configuration (for S3 storage)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# Google Cloud Configuration (if using Google services)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Environment
ENVIRONMENT=production
```

### 3. Build and Run with Docker Compose

```bash
# Build and start the service
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

### 4. Access the Service

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Service Info**: http://localhost:8000/

## Docker Commands

### Build the Image

```bash
docker build -t complyquick-ai .
```

### Run the Container

```bash
docker run -d \
  --name complyquick-ai \
  -p 8000:8000 \
  --env-file .env \
  complyquick-ai
```

### View Logs

```bash
# Docker Compose
docker-compose logs -f

# Docker
docker logs -f complyquick-ai
```

### Stop the Service

```bash
# Docker Compose
docker-compose down

# Docker
docker stop complyquick-ai
docker rm complyquick-ai
```

## Production Deployment

### 1. Using Docker Compose with Nginx

```bash
# Start with nginx reverse proxy
docker-compose --profile production up -d
```

### 2. Environment-Specific Configurations

#### Development

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

#### Production

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 3. SSL/HTTPS Setup

1. Place your SSL certificates in the `ssl/` directory
2. Update the `nginx.conf` file with your domain
3. Uncomment the HTTPS server block in `nginx.conf`
4. Restart the containers

## Configuration Options

### Environment Variables

| Variable                         | Description                    | Default    | Required |
| -------------------------------- | ------------------------------ | ---------- | -------- |
| `OPENAI_API_KEY`                 | OpenAI API key for AI services | -          | Yes      |
| `AWS_ACCESS_KEY_ID`              | AWS access key for S3 storage  | -          | Yes      |
| `AWS_SECRET_ACCESS_KEY`          | AWS secret key for S3 storage  | -          | Yes      |
| `AWS_REGION`                     | AWS region                     | us-east-1  | No       |
| `GOOGLE_APPLICATION_CREDENTIALS` | Google Cloud credentials path  | -          | No       |
| `ENVIRONMENT`                    | Deployment environment         | production | No       |

### Docker Compose Services

#### complyquick-ai

- **Port**: 8000
- **Health Check**: Every 30 seconds
- **Restart Policy**: unless-stopped
- **Volumes**:
  - `./uploads:/app/uploads`
  - `./downloads:/app/downloads`

#### nginx (Production Profile)

- **Ports**: 80, 443
- **Reverse Proxy**: Routes `/api/*` to complyquick-ai
- **Rate Limiting**: 10 requests/second
- **File Upload**: 100MB max

## Monitoring and Logging

### Health Checks

The service includes health checks that monitor:

- Application responsiveness
- API endpoint availability
- Service status

### Logs

```bash
# View application logs
docker-compose logs complyquick-ai

# View nginx logs (if using production profile)
docker-compose logs nginx

# Follow logs in real-time
docker-compose logs -f
```

### Metrics

- Health check endpoint: `GET /health`
- Service information: `GET /`
- API documentation: `GET /docs`

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
# Check what's using port 8000
lsof -i :8000

# Stop conflicting service or change port in docker-compose.yml
```

#### 2. Memory Issues

```bash
# Increase Docker memory limit
# In Docker Desktop: Settings > Resources > Memory > 4GB+
```

#### 3. Build Failures

```bash
# Clean build cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

#### 4. Permission Issues

```bash
# Fix volume permissions
sudo chown -R $USER:$USER ./uploads ./downloads
```

### Debug Mode

```bash
# Run with debug logging
docker-compose run --rm complyquick-ai python -m uvicorn app:app --host 0.0.0.0 --port 8000 --log-level debug
```

## Security Considerations

### 1. Environment Variables

- Never commit `.env` files to version control
- Use Docker secrets for sensitive data in production
- Rotate API keys regularly

### 2. Network Security

- Use internal Docker networks
- Configure firewall rules
- Enable HTTPS in production

### 3. Container Security

- Run containers as non-root user
- Keep base images updated
- Scan images for vulnerabilities

## Scaling

### Horizontal Scaling

```bash
# Scale the service
docker-compose up --scale complyquick-ai=3
```

### Load Balancing

The nginx configuration includes basic load balancing. For production, consider:

- AWS Application Load Balancer
- Google Cloud Load Balancer
- Azure Application Gateway

## Backup and Recovery

### Data Backup

```bash
# Backup uploads and downloads
docker run --rm -v complyquick-ai_uploads:/data -v $(pwd):/backup alpine tar czf /backup/uploads-backup.tar.gz -C /data .
```

### Configuration Backup

```bash
# Backup configuration files
tar czf config-backup.tar.gz docker-compose.yml nginx.conf .env
```

## Performance Optimization

### 1. Resource Limits

```yaml
# In docker-compose.yml
services:
  complyquick-ai:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: "1.0"
```

### 2. Caching

- Use Docker layer caching
- Implement Redis for session storage
- Configure nginx caching

### 3. Monitoring

- Use Prometheus for metrics
- Configure Grafana dashboards
- Set up alerting

## Support

For issues and questions:

1. Check the logs: `docker-compose logs`
2. Verify environment variables
3. Test health endpoint: `curl http://localhost:8000/health`
4. Review this documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.
