# EduHub Catalog Service

The Catalog Service is a core microservice for the EduHub Academy learning management system. It manages course information, enrollments, and provides APIs for browsing and managing the course catalog.

## Features

- **Course Management**: Full CRUD operations for courses
- **Enrollment System**: Enroll and unenroll students in courses
- **Search & Filter**: Search courses by title, code, or teacher name
- **Teacher Management**: Manage teacher profiles and assignments
- **Student Management**: Student profile management
- **Category Management**: Organize courses into categories
- **Caching**: Redis-based caching for high-performance reads
- **Authentication**: JWT-based authentication with role-based access control
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation

## Technology Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+ with SQLAlchemy ORM
- **Cache**: Redis 7+
- **Authentication**: JWT (JSON Web Tokens)
- **Containerization**: Docker
- **Orchestration**: Kubernetes
- **API Gateway**: NGINX Ingress Controller

## Project Structure

```
eduhub-catalog-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration settings
│   ├── database.py             # Database connection and session
│   ├── cache.py                # Redis cache service
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── course.py
│   │   ├── teacher.py
│   │   ├── student.py
│   │   ├── enrollment.py
│   │   └── category.py
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── course.py
│   │   ├── teacher.py
│   │   ├── student.py
│   │   ├── enrollment.py
│   │   └── category.py
│   ├── api/                    # API routes
│   │   ├── __init__.py
│   │   ├── courses.py
│   │   ├── enrollments.py
│   │   ├── teachers.py
│   │   ├── students.py
│   │   └── categories.py
│   └── middleware/             # Middleware
│       ├── __init__.py
│       └── auth.py
├── alembic/                    # Database migrations
│   ├── env.py
│   └── versions/
├── k8s/                        # Kubernetes manifests
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── hpa.yaml
│   ├── ingress.yaml
│   ├── postgres-deployment.yaml
│   └── redis-deployment.yaml
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Database Schema

### Tables

1. **courses**: Course information
   - id, title, description, code, category_id, teacher_id, max_students, duration_weeks, status, is_active

2. **teachers**: Teacher profiles
   - id, user_id, first_name, last_name, email, bio, specialization, is_active

3. **students**: Student profiles
   - id, user_id, first_name, last_name, email, student_number, grade_level, date_of_birth, is_active

4. **enrollments**: Student course enrollments
   - id, student_id, course_id, enrollment_date, status, is_active

5. **categories**: Course categories
   - id, name, description, slug

## Setup and Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker (optional)
- Kubernetes cluster (for production deployment)

### Local Development Setup

1. **Clone the repository**:
   ```bash
   cd eduhub-catalog-service
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

6. **Start the service**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Access the API**:
   - API: http://localhost:8000
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Docker Setup

1. **Build and run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

2. **Run migrations**:
   ```bash
   docker-compose exec catalog-service alembic upgrade head
   ```

3. **View logs**:
   ```bash
   docker-compose logs -f catalog-service
   ```

## API Endpoints

### Courses

- `POST /api/v1/courses` - Create a new course (Admin/Teacher)
- `GET /api/v1/courses` - List all courses with pagination and filters
- `GET /api/v1/courses/{course_id}` - Get course details
- `PUT /api/v1/courses/{course_id}` - Update a course (Admin/Teacher)
- `DELETE /api/v1/courses/{course_id}` - Delete a course (Admin)
- `GET /api/v1/courses/search/?q={query}` - Search courses

### Enrollments

- `POST /api/v1/enrollments` - Enroll a student in a course
- `DELETE /api/v1/enrollments/{enrollment_id}` - Unenroll a student
- `GET /api/v1/enrollments` - List enrollments with filters
- `GET /api/v1/enrollments/{enrollment_id}` - Get enrollment details
- `GET /api/v1/enrollments/course/{course_id}/students` - List enrolled students (Teachers)

### Teachers

- `POST /api/v1/teachers` - Create a teacher (Admin)
- `GET /api/v1/teachers/{teacher_id}` - Get teacher details

### Students

- `POST /api/v1/students` - Create a student (Admin)
- `GET /api/v1/students/{student_id}` - Get student details

### Categories

- `POST /api/v1/categories` - Create a category (Admin)
- `GET /api/v1/categories` - List all categories
- `GET /api/v1/categories/{category_id}` - Get category details

### Health Checks

- `GET /health` - Health check endpoint
- `GET /ready` - Readiness check endpoint

## Authentication

The service uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### User Roles

- **Admin**: Full access to all endpoints
- **Teacher**: Can create and update courses, view enrolled students
- **Student**: Can enroll/unenroll, view courses

## Caching

The service uses Redis for caching frequently accessed data:

- Course listings (5 minutes TTL)
- Course details (5 minutes TTL)
- Search results (5 minutes TTL)
- Category lists (5 minutes TTL)

Cache is automatically invalidated when data is modified.

## Kubernetes Deployment

### Deploy to Kubernetes

1. **Create namespace**:
   ```bash
   kubectl apply -f k8s/namespace.yaml
   ```

2. **Deploy dependencies**:
   ```bash
   kubectl apply -f k8s/postgres-deployment.yaml
   kubectl apply -f k8s/redis-deployment.yaml
   ```

3. **Create secrets and config**:
   ```bash
   kubectl apply -f k8s/secret.yaml
   kubectl apply -f k8s/configmap.yaml
   ```

4. **Deploy the service**:
   ```bash
   kubectl apply -f k8s/deployment.yaml
   kubectl apply -f k8s/service.yaml
   ```

5. **Set up autoscaling**:
   ```bash
   kubectl apply -f k8s/hpa.yaml
   ```

6. **Configure ingress**:
   ```bash
   kubectl apply -f k8s/ingress.yaml
   ```

### Verify Deployment

```bash
kubectl get pods -n eduhub
kubectl get services -n eduhub
kubectl logs -f deployment/catalog-service -n eduhub
```

## Performance Considerations

- **Horizontal Scaling**: Configured for 3-10 replicas based on CPU/memory usage
- **Database Connection Pooling**: 20 connections per instance with 10 overflow
- **Redis Caching**: 5-minute TTL for read-heavy operations
- **Read Replicas**: PostgreSQL can be configured with read replicas for better performance

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | Required |
| `JWT_SECRET_KEY` | Secret key for JWT signing | Required |
| `JWT_ALGORITHM` | JWT algorithm | HS256 |
| `CACHE_TTL` | Cache TTL in seconds | 300 |
| `DEBUG` | Debug mode | False |
| `DEFAULT_PAGE_SIZE` | Default pagination size | 20 |
| `MAX_PAGE_SIZE` | Max pagination size | 100 |

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black app/
isort app/
flake8 app/
```

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

## Monitoring and Logging

- Health checks at `/health` and `/ready`
- Structured logging to stdout
- Prometheus metrics (can be added)
- Liveness and readiness probes configured in Kubernetes

## Security

- JWT authentication required for all endpoints
- Role-based access control (RBAC)
- SQL injection prevention via SQLAlchemy ORM
- Input validation using Pydantic schemas
- Rate limiting via NGINX Ingress
- TLS/SSL termination at ingress level

## Contributing

1. Create a feature branch
2. Make your changes
3. Write tests
4. Run code formatting and linting
5. Submit a pull request

## License

Copyright © 2025 EduHub Academy. All rights reserved.

## Support

For issues and questions, contact the EduHub development team.