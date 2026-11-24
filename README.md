# Digital Banking API

A backend banking application built with **Django, Django REST Framework, PostgreSQL, and Docker**. It provides JWT-based authentication, account management, deposits, fund transfers, transaction history, and audit logging.

## Features

### Authentication
- Custom Django user model
- User registration
- JWT access and refresh tokens
- Token refresh endpoint
- Authenticated user profile endpoint

### Banking
- Create and list bank accounts
- Support for BDT, USD, and EUR currencies
- Account status management: ACTIVE, FROZEN, and CLOSED
- Deposit operations
- Account-to-account fund transfers
- Transaction history

### Transaction Integrity
- Database transactions for financial operations
- Row-level locking using `select_for_update()`
- Idempotency keys to prevent duplicate deposit and transfer requests
- Balance validation
- Sender and receiver ownership validation
- Currency and account-status validation
- Debit and credit ledger entries
- Audit logging

### API Security
- JWT authentication
- Authenticated-by-default API permissions
- Request throttling
- Input validation
- Account ownership checks

### Development and Deployment
- Docker and Docker Compose
- PostgreSQL 16
- Gunicorn application server
- Pytest and Factory Boy
- Code coverage reporting
- GitHub Actions CI workflow
- EC2 deployment workflow
- Nginx configuration prepared for reverse proxy use

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.12 |
| Backend | Django 5.2 |
| API | Django REST Framework |
| Authentication | Simple JWT |
| Database | PostgreSQL 16 |
| Application Server | Gunicorn |
| Containerization | Docker |
| Testing | Pytest, pytest-django |
| Test Factories | Factory Boy |
| CI/CD | GitHub Actions |
| Reverse Proxy Configuration | Nginx |

## Project Structure

```text
digital-banking-api/
│
├── accounts/
│   ├── migrations/
│   ├── tests/
│   ├── admin.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   └── views.py
│
├── banking/
│   ├── migrations/
│   ├── tests/
│   ├── admin.py
│   ├── models.py
│   ├── serializers.py
│   ├── services.py
│   ├── urls.py
│   └── views.py
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── deploy/
│   └── nginx.conf
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── .env.example
└── manage.py
```

## Getting Started

### Prerequisites

Install the following tools:

- Python 3.12
- Docker
- Docker Compose
- Git

### 1. Clone the repository

```bash
git clone https://github.com/MKdir75/digital-banking-api.git
cd digital-banking-api
```

### 2. Configure environment variables

Create a `.env` file from the example:

**PowerShell:**

```powershell
Copy-Item .env.example .env
```

Update the environment variables in `.env`.

The database credentials must match the PostgreSQL credentials configured in `docker-compose.yml`.

Never commit your actual `.env` file or production secrets.

### 3. Build and start the application

```bash
docker compose up -d --build
```

The application runs on:

```text
http://localhost:8001
```

The Django container runs database migrations during startup.

### 4. Check application status

```bash
docker compose ps
```

Check Django configuration:

```bash
docker compose exec web python manage.py check
```

### 5. Run database migrations manually

```bash
docker compose exec web python manage.py migrate
```

## API Endpoints

Base URL:

```text
http://localhost:8001
```

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register/` | Register a user |
| POST | `/api/auth/token/` | Obtain JWT tokens |
| POST | `/api/auth/token/refresh/` | Refresh access token |
| GET | `/api/auth/me/` | Get authenticated user |

### Banking

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/banking/accounts/` | List user's accounts |
| POST | `/api/banking/accounts/` | Create a bank account |
| POST | `/api/banking/transfers/` | Transfer funds |
| GET | `/api/banking/transfers/history/` | Retrieve transfer history |
| POST | `/api/banking/deposits/` | Deposit funds |

### Authentication Header

For protected endpoints, include the JWT access token:

```http
Authorization: Bearer <access_token>
```

## Testing

The project uses Pytest, pytest-django, Factory Boy, and pytest-cov.

Run all tests inside the Docker container:

```bash
docker compose exec web pytest -v
```

Run tests with coverage:

```bash
docker compose exec web pytest \
  --cov=accounts \
  --cov=banking \
  --cov-report=term-missing \
  -v
```

The latest recorded local test run:

- **43 tests passed**
- **99% code coverage**

Coverage results may change as the codebase evolves.

## CI/CD

GitHub Actions workflows are included.

### Continuous Integration

The CI workflow:

1. Checks out the repository.
2. Sets up Python 3.12.
3. Starts a PostgreSQL 16 service.
4. Installs development dependencies.
5. Runs Django system checks.
6. Applies database migrations.
7. Executes the test suite.

Workflow file:

```text
.github/workflows/ci.yml
```

### Deployment to AWS EC2

A deployment workflow is included for an EC2 instance.

It connects to the server through SSH and:

1. Pulls the latest code from the `main` branch.
2. Builds and starts Docker containers.
3. Runs database migrations.
4. Checks container status.

Workflow file:

```text
.github/workflows/deploy.yml
```

Configure these GitHub Actions repository secrets before using the deployment workflow:

| Secret | Description |
|---|---|
| `DEPLOY_HOST` | EC2 public IP or hostname |
| `DEPLOY_USER` | EC2 SSH username |
| `DEPLOY_SSH_KEY` | Private SSH key |

The EC2 instance must already have the repository, Docker, Docker Compose, and a correctly configured `.env` file.

## Important Financial Limitations

This project is a learning and portfolio backend application, not a production-ready banking platform.

- Deposits currently simulate crediting an account; they are not verified through an external payment provider.
- The ledger implementation records debit and credit entries but is not a complete, independently reconciled general-ledger system.
- Production use would require additional controls, including payment verification, reconciliation, monitoring, secure secret management, backups, and security review.

## License

This project is available under the MIT License if an MIT license is added to the repository. Otherwise, no license is currently specified.