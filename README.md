# Digital Banking API

A backend banking API built with **Python, Django, Django REST Framework, PostgreSQL, and Docker**. The project demonstrates JWT authentication, account management, deposits, account-to-account transfers, transaction history, ledger entries, and audit logging.

> **Project Status:** This is a learning and portfolio project, not a production-ready banking system. The current AWS EC2 deployment uses HTTP, and deposits are simulated rather than verified through an external payment provider. Do not use real customer data, credentials, or money with this application.

## Features

### Authentication

- Custom Django user model
- User registration
- JWT access and refresh tokens
- Token refresh endpoint
- Authenticated user profile endpoint
- Email-based authentication

### Banking

- Create and list bank accounts
- Support for BDT, USD, and EUR currencies
- Account status validation: ACTIVE, FROZEN, and CLOSED
- Deposit operations
- Account-to-account fund transfers
- Transfer transaction history

### Transaction Integrity

- Atomic database transactions
- Row-level locking using `select_for_update()`
- Idempotency keys to prevent duplicate deposit and transfer requests
- Positive amount validation
- Insufficient balance protection
- Sender account ownership validation
- Receiver account validation
- Currency and account status validation
- Debit and credit ledger entries
- Audit logging

### API Security

- JWT authentication for protected endpoints
- Explicit public access for user registration
- Input validation through Django REST Framework serializers
- Account ownership checks
- Request throttling where configured

### Development and Deployment

- Docker and Docker Compose
- PostgreSQL 16
- Gunicorn application server
- Nginx reverse proxy
- Pytest and Factory Boy
- Code coverage reporting
- GitHub Actions CI workflow
- AWS EC2 deployment
- GitHub Actions self-hosted runner
- Automated Docker-based deployment
- Database migrations during deployment

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.12 |
| Backend | Django 5.2 |
| API | Django REST Framework |
| Authentication | Simple JWT |
| Database | PostgreSQL 16 |
| Application Server | Gunicorn |
| Reverse Proxy | Nginx |
| Containerization | Docker, Docker Compose |
| Testing | Pytest, pytest-django, pytest-cov |
| Test Factories | Factory Boy |
| CI/CD | GitHub Actions |
| Cloud Platform | AWS EC2 |
| Deployment | Self-hosted GitHub Actions Runner |

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
- Git
- Docker
- Docker Compose

### 1. Clone the Repository

```bash
git clone https://github.com/MKdir75/digital-banking-api.git

cd digital-banking-api
```

### 2. Configure Environment Variables

Create a local `.env` file using the example configuration.

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env
```

**Linux/macOS:**

```bash
cp .env.example .env
```

Update the environment variables in `.env`.

Important configuration:

- Set a strong, randomly generated Django `SECRET_KEY`.
- Set `DEBUG=False` outside local development.
- Configure `ALLOWED_HOSTS` with the appropriate hostnames or IP addresses.
- Configure database credentials matching the PostgreSQL environment variables.
- Keep application secrets outside the Git repository.

Never commit your actual `.env` file or production credentials.

### 3. Build and Start the Application

```bash
docker compose up -d --build
```

The application is accessible at:

```text
http://localhost/
```

Nginx publishes port `80` on the host and forwards requests to the Django application running through Gunicorn.

PostgreSQL and Django communicate through the internal Docker network.

The Django container runs database migrations during startup.

### 4. Check Application Status

```bash
docker compose ps
```

Run Django system checks:

```bash
docker compose exec web python manage.py check
```

### 5. Run Database Migrations

```bash
docker compose exec web python manage.py migrate
```

## API Endpoints

Base URL for local development:

```text
http://localhost
```

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register/` | Register a user |
| POST | `/api/auth/token/` | Obtain JWT access and refresh tokens |
| POST | `/api/auth/token/refresh/` | Refresh access token |
| GET | `/api/auth/me/` | Retrieve authenticated user profile |

The custom user model uses email as the login identifier.

### Banking

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/banking/accounts/` | List user's bank accounts |
| POST | `/api/banking/accounts/` | Create a bank account |
| POST | `/api/banking/transfers/` | Transfer funds |
| GET | `/api/banking/transfers/history/` | Retrieve transfer history |
| POST | `/api/banking/deposits/` | Create a deposit |

### Authentication Header

Protected endpoints require a JWT access token.

```http
Authorization: Bearer <access_token>
```

## Testing

The project uses Pytest, pytest-django, pytest-cov, and Factory Boy.

Run the complete test suite:

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

Coverage results depend on the current codebase and test suite. Run the commands above to obtain the latest test count and coverage.

## Continuous Integration and Deployment

The project uses GitHub Actions for continuous integration and automated deployment to AWS EC2.

Two workflows are configured in:

```text
.github/workflows/
├── ci.yml
└── deploy.yml
```

### Continuous Integration (CI)

Workflow file:

```text
.github/workflows/ci.yml
```

The CI workflow performs automated validation of the application.

The configured workflow includes:

1. Checking out the repository.
2. Setting up Python 3.12.
3. Starting a PostgreSQL 16 service.
4. Installing development dependencies.
5. Running Django system checks.
6. Applying database migrations.
7. Executing automated tests.

The CI workflow runs independently of the deployment workflow.

### Continuous Deployment (CD)

Workflow file:

```text
.github/workflows/deploy.yml
```

The application is deployed to an AWS EC2 Ubuntu instance using a **GitHub Actions self-hosted runner**.

The runner is installed directly on the EC2 instance and registered with the GitHub repository.

It runs as a Linux systemd service.

#### Deployment Triggers

The deployment workflow supports:

- Automatic deployment when code is pushed to the `main` branch.
- Manual deployment using GitHub Actions `workflow_dispatch`.

#### Deployment Process

The deployment workflow performs the following steps:

1. Runs on the EC2 self-hosted runner.
2. Navigates to the application directory.
3. Pulls the latest code from the `main` branch.
4. Builds and starts Docker containers using Docker Compose.
5. Runs Django database migrations.
6. Checks the status of Docker containers.

#### Deployment Architecture

```text
Developer
   |
   | Git Push
   v
GitHub Repository
   |
   v
GitHub Actions
   |
   | Job dispatched to self-hosted runner
   v
AWS EC2 Instance (Ubuntu)
   |
   v
GitHub Actions Runner
   |
   v
Docker Compose
   |
   +-------------------+
   |                   |
   v                   v
  Nginx             Django API
                        |
                        v
                    PostgreSQL
```

#### Self-hosted Runner Configuration

The self-hosted runner uses:

| Configuration | Value |
|---|---|
| Operating System | Linux |
| Architecture | x64 |
| Runner Type | Self-hosted |
| Hosting Platform | AWS EC2 |
| Runner User | ubuntu |
| Runner Service | systemd |

Default runner labels:

```text
self-hosted
Linux
X64
```

The runner is configured as a systemd service so it can operate in the background and start with the EC2 instance.

#### Deployment Prerequisites

The EC2 instance must have:

- Ubuntu operating system.
- Git installed.
- Docker installed.
- Docker Compose plugin installed.
- Application repository cloned at `/home/ubuntu/digital-banking-api`.
- A properly configured server-side `.env` file.
- GitHub Actions self-hosted runner registered and online.
- Required permissions for the runner user to execute Docker Compose commands.

The current deployment workflow does not require the old `DEPLOY_HOST`, `DEPLOY_USER`, or `DEPLOY_SSH_KEY` repository secrets because the deployment job executes directly on the EC2 instance.

Application secrets remain on the EC2 server and should never be committed to GitHub.

#### Self-hosted Runner Security

A self-hosted runner executes repository workflow code directly on the EC2 host.

Because the runner has access to Docker and the deployment environment:

- Only trusted repository code should execute on this runner.
- Protect the `main` branch.
- Restrict permissions to modify deployment workflow files.
- Do not execute untrusted pull-request code on this runner.
- Keep the runner and EC2 operating system updated.
- Never expose private SSH keys, registration tokens, or application secrets in workflow logs or commits.

## Current Deployment Status

The application has been successfully deployed to an AWS EC2 Ubuntu instance.

Current deployment components:

| Component | Status |
|---|---|
| AWS EC2 | Deployed |
| Docker Compose | Running |
| Django API | Running |
| PostgreSQL | Running |
| Nginx | Running |
| GitHub Actions CI | Successful |
| Self-hosted Runner | Online |
| Automated Deployment | Successful |

**Deployment notes:**

- Nginx currently serves the application over HTTP.
- HTTPS/TLS has not yet been configured.
- The EC2 instance uses an automatically assigned public IPv4 address rather than an Elastic IP. This address may change if the instance is stopped and started.
- Do not submit real passwords, personal information, or financial data to the current HTTP deployment.

## Important Financial Limitations

This project is a learning and portfolio backend application, not a production-ready banking system.

- Deposits currently simulate account balance credits. They are not verified through an external payment provider or bank.
- The ledger records debit and credit entries, but it is not a complete, independently reconciled general-ledger system.
- Real financial operations would require payment-provider verification, transaction reconciliation, fraud prevention, monitoring, alerting, backups, disaster recovery, secure secret management, operational controls, and independent security review.
- The current HTTP-only deployment is not suitable for real user credentials or financial information.

## License

No license is specified unless a `LICENSE` file is present in the repository.

Add an appropriate license file before describing the project as MIT-licensed or granting others explicit reuse rights.
