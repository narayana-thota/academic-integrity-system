# Academic Integrity & Similarity Case Management System

### Academic Integrity Review, Evidence & Case Management Platform

The Academic Integrity & Similarity Case Management System is a full-stack platform designed to manage academic similarity flags, collect supporting evidence, assign reviewers, record decisions, handle appeals, and maintain complete case history.

The platform provides a structured workflow for academic integrity reviews, ensuring that similarity scores trigger human review rather than automatic conclusions. It emphasizes evidence-based decisions, reviewer accountability, transparent case handling, and operational traceability.

The system combines a React frontend, Python FastAPI REST API, MySQL database, synthetic academic datasets, and Docker-based deployment.

## Features

- **Dashboard:** Monitor academic integrity cases, similarity reports, decisions, appeals, and reviewer workloads.
- **Similarity Report Management:** View similarity scores, matched sources, report categories, and review recommendations.
- **Case Management:** Track cases through their lifecycle, including status, priority, and closure information.
- **Evidence Management:** Maintain evidence records and associate supporting evidence with individual cases.
- **Reviewer Assignment:** Assign reviewers while considering reviewer availability, workload, and conflicts of interest.
- **Decision Management:** Record review decisions, actions, and supporting rationale.
- **Appeal Management:** Manage learner appeals and independent appeal review outcomes.
- **Case Timeline:** Maintain a chronological history of case events and important workflow activities.
- **Audit History:** Preserve traceability of system activities and workflow changes.
- **Data Engineering:** Generate synthetic academic datasets, workflow records, and labelled edge cases.
- **Validation Workflows:** Validate dataset integrity, database records, reviewer assignments, decisions, appeals, and exceptional scenarios.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React.js, JavaScript, Vite |
| Backend | Python, FastAPI, REST API |
| Database | MySQL 8.4 |
| Database Connectivity | Python MySQL Connector |
| Containerization | Docker, Docker Compose |
| Data Processing | Python, Pandas, CSV, JSON |
| API Documentation | FastAPI, OpenAPI, Swagger UI |
| Version Control | Git, GitHub |

## Project Structure

```text
academic-integrity-system/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   ├── core/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── database.py
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── database/
│   ├── schema.sql
│   └── data_dictionary.md
│
├── data_engineering/
│   ├── generators/
│   ├── loaders/
│   ├── validation/
│   ├── output/
│   ├── generate_dataset.py
│   ├── generate_workflow_records.py
│   ├── generate_decision_appeal_records.py
│   └── load_to_mysql.py
│
├── docs/
│   ├── BUSINESS_RULES.md
│   ├── DATA_DICTIONARY.md
│   ├── ER_DIAGRAM.md
│   └── REQUIREMENTS.md
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── services/
│   │   └── styles/
│   ├── package.json
│   └── vite.config.js
│
├── tests/
│
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

## Prerequisites

Install the following:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/)
- [Node.js](https://nodejs.org/) (optional for running the frontend outside Docker)
- [Python](https://www.python.org/) (optional for running data engineering scripts locally)

Make sure Docker Desktop is running before starting the application.

For the Docker-based setup, Python, Node.js, and MySQL do not need to be installed separately.

## Installation and Execution

### Step 1: Clone the Repository

Open PowerShell or the VS Code terminal:

```powershell
git clone https://github.com/narayana-thota/academic-integrity-system.git
```

Navigate into the project:

```powershell
cd academic-integrity-system
```

### Step 2: Configure Environment Variables

Create your environment file:

```powershell
Copy-Item .env.example .env
```

Open `.env` and configure your own database credentials:

```env
MYSQL_ROOT_PASSWORD=your_secure_root_password
MYSQL_DATABASE=academic_integrity
MYSQL_USER=your_app_user
MYSQL_PASSWORD=your_secure_app_password
```

Important:

- Replace example passwords with your own secure credentials.
- Keep `.env` private.
- Never upload `.env` or real database credentials to GitHub.
- Use the same database credentials expected by the application configuration.

### Step 3: Start the Application

Run:

```powershell
docker compose up --build -d
```

Docker Compose builds and starts the configured application services, including the backend and MySQL database.

Wait for the containers to initialize.

### Step 4: Verify Docker Containers

Run:

```powershell
docker compose ps
```

Check that the configured services are running.

### Step 5: Access the Frontend

Open the following address in your browser:

```text
http://localhost:5173/
```

### Step 6: Verify the Backend

Open another terminal and run:

```powershell
Invoke-RestMethod http://localhost:8001/health
```

A successful response indicates that the backend health endpoint is reachable.

### Step 7: Access API Documentation

FastAPI provides interactive API documentation through Swagger UI:

```text
http://localhost:8001/docs
```

You can explore available API endpoints and test supported operations directly from the browser.

## Application Access

After successful startup:

| Component | Local Address |
|---|---|
| Web Application | http://localhost:5173 |
| Backend Health | http://localhost:8001/health |
| API Documentation | http://localhost:8001/docs |
| MySQL Database | localhost:3307 |

**Note:** These are local development addresses. They are accessible from the computer running the application and are not public deployment URLs.

## Database Design

The application uses MySQL 8.4 to manage academic integrity workflows.

The database includes tables for:

- Learners
- Assessments
- Submissions
- Similarity Reports
- Report Matches
- Integrity Rules
- Cases
- Evidence Items
- Case Evidence
- Reviewers
- Reviewer Assignments
- Reviewer Conflicts
- Decisions
- Appeals
- Appeal Reviews
- Case Events
- Audit Logs

The database schema is available at:

```text
database/schema.sql
```

The data dictionary and entity relationships are documented in:

```text
database/data_dictionary.md
docs/DATA_DICTIONARY.md
docs/ER_DIAGRAM.md
```

## Synthetic Data Generation

The project uses synthetic academic data for demonstration, workflow simulation, and validation.

The generated baseline dataset includes:

| Entity | Records |
|---|---:|
| Learners | 2,000 |
| Assessments | 100 |
| Reviewers | 30 |
| Submissions | 10,000 |
| Similarity Reports | 1,000 |
| Report Matches | 3,059 |
| Cases | 300 |
| Ground Truth Records | 1,000 |

Additional workflow records include evidence, reviewer assignments, case events, audit logs, decisions, and appeals.

The data engineering pipeline supports:

- Synthetic dataset generation.
- Workflow record generation.
- Reviewer conflict simulation.
- Decision and appeal generation.
- Database loading.
- Dataset and workflow validation.

Generated datasets are stored under:

```text
data_engineering/output/
```

## Data Validation

Validation scripts are available under:

```text
data_engineering/validation/
```

The validation workflows cover:

- Dataset record counts and primary key uniqueness.
- Database structure and data integrity.
- Workflow record consistency.
- Reviewer assignment and conflict scenarios.
- Decision and appeal validation.
- Edge-case and exception handling.

Run the relevant validation modules from the project root:

```powershell
python -m data_engineering.validation.validate_dataset
```

```powershell
python -m data_engineering.validation.validate_workflow
```

```powershell
python -m data_engineering.validation.validate_decision_appeal
```

```powershell
python -m data_engineering.validation.validate_edge_cases
```

These commands require the Python dependencies used by the data engineering scripts.

## Managing the Application

**Start the application:**

```powershell
docker compose up -d
```

**Rebuild after source-code changes:**

```powershell
docker compose up --build -d
```

**Display backend logs:**

```powershell
docker compose logs -f backend
```

**Display all service logs:**

```powershell
docker compose logs -f
```

**Check container status:**

```powershell
docker compose ps
```

**Stop the application:**

```powershell
docker compose down
```

**Reset the database:**

```powershell
docker compose down -v
docker compose up --build -d
```

**Warning:** Removing volumes deletes persistent database data. Only perform a reset when you intentionally want to recreate the database.

## Documentation

Supporting project documentation is available in the repository:

| Document | Description |
|---|---|
| `docs/REQUIREMENTS.md` | Functional requirements and system scope |
| `docs/ER_DIAGRAM.md` | Database entities and relationships |
| `docs/DATA_DICTIONARY.md` | Entity fields and data definitions |
| `docs/BUSINESS_RULES.md` | Academic integrity workflow rules |
| `database/schema.sql` | MySQL database schema |

Additional technical decisions, testing evidence, and AI usage disclosures are maintained in the `DOCUMENTATION/` directory.

## Project Purpose

The Academic Integrity & Similarity Case Management System demonstrates how similarity detection results can be managed through a structured, evidence-based academic review process.

The system focuses on ensuring that similarity flags initiate review rather than automatically determine misconduct. It provides reviewer assignment, evidence management, decision recording, appeal handling, and audit traceability within a unified platform.

This is a development and demonstration project using synthetic data. It is not an automated plagiarism verdict system or a replacement for institutional academic integrity policies.

**Academic Integrity & Similarity Case Management System — Evidence-Based Review, Transparent Decisions, and Complete Traceability.**