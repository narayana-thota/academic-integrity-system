# Academic Integrity & Similarity Case Management System – AI Prompt History

This document records the AI-assisted discussions used during the development of the Academic Integrity & Similarity Case Management System for the YottaFlex AI 72-hour recruitment challenge.

The prompts are organized chronologically according to the development process. They cover problem understanding, requirements analysis, database engineering, synthetic dataset generation, backend development, frontend integration, Docker configuration, debugging, testing, and submission preparation.

The purpose of this document is to transparently explain how LLM assistance was used throughout development and what I personally reviewed, modified, and validated.

---

## Phase 1 – Challenge Understanding and Project Planning

I received a 72-hour coding challenge from YottaFlex AI Technologies. Help me understand what exactly they expect from this challenge. Explain the problem statement in simple terms, identify the actual business problem, and tell me what kind of application I should develop.

I don't want to build a basic CRUD application. I want to understand how an academic integrity system works in a real educational institution and how the complete process should be handled.

Explain the workflow from student submission to similarity report generation, evidence collection, reviewer assignment, decision making, appeal handling, and case closure.

Help me identify the main entities, actors, business rules, and required outputs before starting development.

## Phase 2 – Understanding Business Workflow and Requirements

I understand that when students submit an assessment, the system generates similarity reports. However, a similarity percentage alone should not mean that a student is guilty.

Explain how the system should handle students whose similarity percentage crosses a defined threshold. What should happen next? How should evidence be collected? When should a reviewer be assigned? How can a student appeal a decision?

Help me convert the problem statement into functional requirements and identify the important exceptions that should be handled.

I have only 72 hours, so prioritize the essential functionality and avoid adding unnecessary features.

## Phase 3 – Database Design and Entity Relationships

Now let's focus on database design. Identify the main entities required for this application, including Learner, Assessment, Submission, Similarity Report, Integrity Rule, Case, Evidence Item, Reviewer, Decision, and Appeal.

Design the MySQL database with proper primary keys, foreign keys, unique constraints, and relationships.

Explain how one learner can have multiple submissions, how a submission is connected to a similarity report, and how cases are associated with evidence, reviewers, decisions, and appeals.

I want to understand the relationships instead of simply copying SQL code. Explain the cardinalities and why separate tables are required.

## Phase 4 – Database Schema and Implementation

Convert the database design into a complete MySQL schema.sql file.

Create tables in the correct dependency order and include the required constraints and indexes.

Explain how to execute the schema inside MySQL 8.4 and verify whether all tables are created correctly.

When an SQL error occurs, identify the actual cause and provide the corrected implementation without unnecessarily changing the existing database design.

## Phase 5 – Synthetic Dataset Design and Generation

The challenge requires a meaningful dataset with related records. We are not going to use external or confidential student data. We want to generate synthetic academic records.

Help me design a realistic dataset for learners, assessments, submissions, similarity reports, report matches, integrity rules, and cases.

Use the required baseline scale of 2,000 learners, 100 assessments, 30 reviewers, 10,000 submissions, 1,000 similarity reports, and 300 cases.

Every generated record must have valid identifiers and relationships. Explain how deterministic IDs should be generated and how the records should be connected.

I also want legitimate similarity scenarios, false positives, reviewer conflicts, appeals, and exceptional cases. Keep ground-truth information separate from the input records.

## Phase 6 – Dataset Validation and Reproducibility

I have generated the initial datasets. Now help me validate the generated records.

Check record counts, primary key uniqueness, relationships, and consistency between parent and child records.

I want to generate workflow records such as evidence items, case evidence links, reviewer conflicts, reviewer assignments, case events, and audit logs.

Make sure reviewer assignments respect conflict-of-interest rules and reviewer workload limits.

Help me validate the generated records without modifying the original baseline dataset unnecessarily.

I also want to understand how reproducibility can be demonstrated using a fixed random seed and dataset checksums.

## Phase 7 – FastAPI Backend Architecture

The database and dataset generation are ready. Now let's implement the backend using FastAPI.

I don't want to put all backend logic in a single Python file. Separate API routes, Pydantic schemas, service modules, and database connectivity.

Explain the responsibilities of each module and how an API request travels through the application.

Implement the required endpoints for dashboard information, cases, similarity reports, evidence, reviewers, decisions, appeals, submissions, and audit history.

Ensure that API responses are structured properly and that validation and database errors are handled correctly.

## Phase 8 – Backend Business Logic and API Integration

Now implement the business logic for academic integrity case management.

The system should treat similarity thresholds as review triggers rather than automatic decisions.

Help me implement the reviewer assignment workflow, including workload and conflict checks.

Evidence records must be associated with the correct cases. Decisions should contain outcomes and rationales. Appeals should have their own review records.

I also want to preserve case events and audit history so that important changes can be traced.

Check that the API endpoints and service logic follow the database relationships and business rules.

## Phase 9 – React Frontend Development

The backend is implemented. Now let's build the React frontend.

I want a professional dashboard that looks like a real-world enterprise application rather than a basic college project.

Create separate pages for Dashboard, Cases, Similarity Reports, Case Details, Reviewers, Decisions, Appeals, and Audit History.

Use reusable components for statistics, tables, filters, status badges, and case details.

Maintain a consistent dark visual theme and make sure the interface is responsive and easy to navigate.

## Phase 10 – Frontend and Backend Integration

Now connect the React frontend with the FastAPI backend.

Check the API endpoint paths and response structures before connecting the pages.

Some frontend pages are not displaying the expected information even though the backend contains records. Help me identify whether the problem is in the API response, frontend mapping, or database query.

Handle loading states, empty results, API errors, filters, and pagination properly.

When a component has an issue, modify the existing implementation without unnecessarily redesigning the entire frontend.

## Phase 11 – Docker and Environment Configuration

I want to run the application using Docker Compose.

Explain how the frontend, FastAPI backend, and MySQL database should be configured as separate services.

Help me understand Docker networking, port mapping, environment variables, persistent volumes, and service dependencies.

I faced issues with Docker Desktop and WSL. Help me identify why Docker commands were failing and how to verify that the required services are running.

I also want the application to be runnable on another laptop after cloning the GitHub repository.

## Phase 12 – Debugging and Application Refinement

I will share terminal errors, API responses, screenshots, and existing source code when something is not working.

Identify the actual root cause before suggesting a correction.

When modifying an existing file, provide the complete corrected file so I can replace it without missing any required changes.

Preserve the existing architecture, database structure, frontend styling, and working functionality.

Do not introduce unnecessary features or change unrelated files while fixing a specific issue.

## Phase 13 – Testing and Validation

The main modules are implemented. Now help me validate the application using the existing validation scripts and API tests.

Check dataset integrity, MySQL structure, API responses, case relationships, reviewer assignments, conflict scenarios, decisions, appeals, and audit history.

I have already executed several validation scripts. Help me understand what the results demonstrate and how to present them as evidence.

Avoid rerunning the entire test suite unnecessarily or changing the working baseline dataset.

## Phase 14 – GitHub Repository and Documentation

The application is working locally. I want to upload the complete project to a public GitHub repository.

Help me create a clean repository and ensure that environment files, database passwords, temporary files, and unnecessary generated artifacts are not uploaded.

Prepare a professional README containing the project overview, features, technology stack, project structure, prerequisites, installation steps, Docker commands, API documentation, database information, and validation instructions.

I also need a separate AI prompt history document for the YottaFlex submission. Explain how to organize it by development phases and include an honest disclosure of AI usage.

## Phase 15 – Final YottaFlex Submission Preparation

Now I want to prepare the project for the YottaFlex final evaluation.

Review the project against the four submission requirements:

1. Make it run – working executable code and clear setup and verification instructions.
2. Show your work – public GitHub repository, meaningful commits, and supporting context.
3. Use LLMs transparently – prompt history and explanation of AI assistance.
4. Make reasoning visible – assumptions, technical decisions, trade-offs, testing approach, and limitations.

Help me identify missing documentation and prepare a technical walkthrough.

I need to explain the database design, architecture, synthetic dataset generation, similarity threshold logic, evidence management, reviewer assignment, decisions, appeals, audit history, and validation approach.

Prepare a demonstration flow that shows the actual working application and helps me explain why the important technical decisions were made.

---

## Where I Relied Heavily on AI

I relied heavily on AI assistance during requirement analysis, architecture planning, database schema development, synthetic dataset generation, FastAPI implementation, React frontend development, Docker configuration, debugging, and documentation.

AI helped me break down the challenge into manageable phases and understand technical concepts that I was not completely familiar with.

During database development, AI helped me reason about entity relationships, constraints, and schema organization. During data engineering, it helped me design generation workflows, deterministic identifiers, ground-truth records, and validation logic.

During backend and frontend development, I used AI to accelerate implementation, organize modules, understand API integration, and troubleshoot errors.

I also relied on AI for Docker and WSL troubleshooting and for preparing the project documentation.

AI assistance was significant throughout the development process. However, I did not treat generated suggestions as automatically correct. They needed to be checked against the actual project requirements, database structure, source code, and runtime behavior.

## What I Personally Reviewed, Changed and Validated

My responsibility was to understand the challenge requirements, decide the project scope, integrate the application components, and validate the implementation.

I personally worked through the business workflow and identified how similarity reports, evidence, reviewers, decisions, appeals, and case closure should be connected.

I reviewed the database entities and relationships and worked on the schema implementation.

I executed the synthetic dataset generation process and verified the generated baseline counts:

- 2,000 learners.
- 100 assessments.
- 30 reviewers.
- 10,000 submissions.
- 1,000 similarity reports.
- 3,059 report matches.
- 300 cases.
- 1,000 ground-truth records.

I also generated dependent workflow records, including evidence items, reviewer assignments, conflict records, case events, and audit logs.

I executed the existing dataset and workflow validation scripts and reviewed the validation results.

I worked on the integration between the FastAPI backend and React frontend. When the interface displayed missing or incorrect information, I examined the API responses and modified the relevant frontend components.

I configured Docker and WSL, initialized the MySQL database, and verified the backend services and database connectivity during development.

I also worked on the frontend modules, including the dashboard, cases, similarity reports, reviewers, decisions, appeals, and audit history.

I executed the frontend production build and reviewed the resulting output. I used the existing validation scripts and API tests as evidence rather than assuming that successful code generation meant the system was correct.

Finally, I organized the GitHub repository, reviewed the environment configuration, and prepared the project documentation so that another developer could understand and run the application.

## My Understanding and Responsibility

I consider AI an important development assistant, but not a replacement for understanding the application.

I used LLM assistance to accelerate requirement analysis, technical learning, coding, debugging, and documentation.

I was responsible for understanding the business requirements, choosing the implementation approach, integrating the frontend and backend, reviewing generated suggestions, and validating the actual application behavior.

I understand that AI-generated code can contain errors and that an application should not be considered complete simply because the code has been generated.

The implementation must be checked through database validation, API testing, frontend behavior, Docker execution, and workflow verification.

This project helped me improve my understanding of full-stack development, relational database design, synthetic data engineering, API development, Docker, and end-to-end software validation.

My objective was to build a working Academic Integrity & Similarity Case Management System while using LLM assistance transparently and taking responsibility for the implementation and its results.