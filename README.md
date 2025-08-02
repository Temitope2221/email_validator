# Email Validator

A comprehensive email validation service built with FastAPI, Celery, and Redis. This service validates email addresses from CSV files with support for both simple and detailed validation results.

## Features

- **Comprehensive Email Validation**: Checks email format, DNS MX records, and SMTP connectivity
- **CSV File Processing**: Upload CSV files with email addresses for bulk validation
- **Background Processing**: Uses Celery for asynchronous processing of large files
- **Progress Tracking**: Real-time progress updates for validation tasks
- **Detailed Results**: Optional detailed validation results with error information
- **Web Interface**: Simple web UI for easy file upload and status checking
- **RESTful API**: Full API documentation with OpenAPI/Swagger support
- **Docker Support**: Containerized deployment with Docker Compose

## Email Validation Process

The validator performs three levels of validation:

1. **Format Validation**: Checks email format using comprehensive regex patterns
2. **Domain Validation**: Verifies domain existence and MX record availability
3. **SMTP Validation**: Tests SMTP connectivity (optional, can be disabled for performance)

## Quick Start

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/Temitope2221/email_validator.git
cd email_validator
```

2. Start the services:
```bash
docker-compose up -d
```

3. Access the application:
   - Web Interface: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/api/health

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start Redis (required for Celery):
```bash
# On Windows (using WSL or Docker)
docker run -d -p 6379:6379 redis:alpine

# On Linux/Mac
redis-server
```

3. Start the Celery worker:
```bash
celery -A app.workers.tasks worker --loglevel=info
```

4. Start the FastAPI application:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Upload CSV File
```http
POST /api/upload/
Content-Type: multipart/form-data

Parameters:
- file: CSV file with email addresses
- detailed: boolean (optional) - Include detailed validation results
```

### Get Validation Results
```http
GET /api/results/{job_id}
```

### Check Task Status
```http
GET /api/status/{task_id}
```

### Health Check
```http
GET /api/health
```

## CSV Format

Your CSV file should contain an `email` column with email addresses:

```csv
email
user1@example.com
user2@domain.com
invalid-email
test@nonexistentdomain.xyz
```

## Output Formats

### Simple Validation
```csv
email,valid
user1@example.com,True
user2@domain.com,True
invalid-email,False
test@nonexistentdomain.xyz,False
```

### Detailed Validation
```csv
email,is_valid,format_valid,domain_valid,smtp_valid,errors
user1@example.com,True,True,True,True,"[]"
user2@domain.com,True,True,True,False,"['SMTP validation error: connection timeout']"
invalid-email,False,False,False,False,"['Invalid email format']"
test@nonexistentdomain.xyz,False,True,False,False,"['Domain does not exist']"
```

## Configuration

### Environment Variables

- `REDIS_URL`: Redis connection URL (default: `redis://redis:6379/0`)
- `CELERY_BROKER_URL`: Celery broker URL (default: `redis://redis:6379/0`)

### Performance Tuning

For large files, consider:
- Disabling SMTP validation for faster processing
- Adjusting Celery worker concurrency
- Using Redis persistence for better reliability

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   FastAPI   │    │   Celery    │    │    Redis    │
│   Web App   │◄──►│   Worker    │◄──►│   Broker    │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │
       ▼                   ▼
┌─────────────┐    ┌─────────────┐
│   CSV File  │    │ Validated   │
│   Upload    │    │   Results   │
└─────────────┘    └─────────────┘
```

## Development

### Project Structure
```
email_validator/
├── app/
│   ├── api/
│   │   └── routes.py          # API endpoints
│   ├── core/
│   │   └── validator.py       # Email validation logic
│   ├── workers/
│   │   └── tasks.py          # Celery tasks
│   └── main.py               # FastAPI application
├── docker-compose.yml         # Docker services
├── Dockerfile                 # Docker image
├── requirements.txt           # Python dependencies
└── README.md                 # This file
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the API documentation at `/docs`
- Review the health check endpoint at `/api/health` 