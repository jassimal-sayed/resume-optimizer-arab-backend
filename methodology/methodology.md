# SmartResume Match: System Methodology

## 1. System Architecture Overview

### 1.1 High-Level Block Diagram

```mermaid
flowchart TB
    subgraph "Client Layer"
        FE[React Frontend]
    end

    subgraph "API Layer"
        GW[Gateway Service]
    end

    subgraph "Business Logic Layer"
        ORCH[Orchestrator Service]
        PARSER[Parser Service]
    end

    subgraph "Data Layer"
        DB[(PostgreSQL)]
        STORAGE[File Storage]
    end

    subgraph "External Services"
        LLM[LLM Providers]
    end

    FE -->|REST API| GW
    GW -->|Internal HTTP| ORCH
    GW -->|Internal HTTP| PARSER
    ORCH -->|SQL| DB
    ORCH -->|API Calls| LLM
    PARSER -->|File Read| STORAGE
    FE -->|Auth| AUTH[Supabase Auth]
```

### 1.2 Detailed Service Architecture

```mermaid
flowchart LR
    subgraph "Gateway Service"
        AUTH_MW[Auth Middleware]
        RATE[Rate Limiter]
        PROXY[HTTP Proxy]
    end

    subgraph "Orchestrator Service"
        API[Internal API]
        WORKER[Background Worker]
        REPO[Repository Layer]
    end

    subgraph "Shared Libraries"
        LIB_AUTH[libs/auth]
        LIB_COMMON[libs/common]
        LIB_DB[libs/db]
        LIB_AI[libs/ai]
    end

    AUTH_MW --> RATE --> PROXY
    PROXY -->|HTTP| API
    API --> REPO
    WORKER --> REPO
    WORKER -->|LLM Calls| LIB_AI
    REPO --> LIB_DB
```

---

## 2. Technology Stack

| Layer                | Technology                   | Purpose                                         |
| -------------------- | ---------------------------- | ----------------------------------------------- |
| **Frontend**         | React 19 + TypeScript        | Single Page Application                         |
| **Build Tool**       | Vite                         | Fast development server & bundler               |
| **Styling**          | CSS/TailwindCSS              | UI styling                                      |
| **Auth**             | Supabase Auth                | User authentication & JWT tokens                |
| **API Gateway**      | FastAPI (Python)             | Request routing, auth validation, rate limiting |
| **Orchestrator**     | FastAPI + AsyncIO            | Business logic, task processing                 |
| **Parser**           | FastAPI                      | PDF/Document parsing                            |
| **Database**         | PostgreSQL (via Supabase)    | Persistent data storage                         |
| **ORM**              | SQLAlchemy 2.0 (Async)       | Database abstraction                            |
| **LLM Providers**    | OpenAI GPT-4 / Google Gemini | AI-powered resume optimization                  |
| **Containerization** | Docker + Docker Compose      | Service isolation & deployment                  |

---

## 3. Development Methodology

### 3.1 Microservices Architecture Pattern

The system follows a **strict microservices architecture** with clear boundaries:

1. **Gateway Service** (Stateless)

   - Handles user authentication
   - Routes requests to downstream services
   - No direct database access

2. **Orchestrator Service** (Stateful)

   - Owns the database schema
   - Processes business logic
   - Runs background workers for AI tasks

3. **Parser Service** (Stateless)
   - Handles document parsing
   - No persistent state

### 3.2 Shared Library Pattern

Common code is organized into granular libraries:

```
libs/
├── auth/        # JWT verification, user context
├── common/      # Config, logging, error handling
├── db/          # SQLAlchemy models, repository pattern
└── ai/          # LLM provider abstraction
```

### 3.3 Request Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Gateway
    participant Orchestrator
    participant LLM
    participant Database

    User->>Frontend: Upload Resume + Job Description
    Frontend->>Gateway: POST /jobs (JWT Token)
    Gateway->>Gateway: Validate JWT
    Gateway->>Orchestrator: POST /internal/jobs
    Orchestrator->>Database: Create Job Record
    Orchestrator->>Database: Enqueue Task
    Orchestrator-->>Gateway: {job_id, status: "queued"}
    Gateway-->>Frontend: {job_id}

    Note over Orchestrator: Background Worker
    Orchestrator->>Database: Poll Task Queue
    Orchestrator->>LLM: Generate Optimization
    LLM-->>Orchestrator: Optimization Result
    Orchestrator->>Database: Save Result, Update Status

    Frontend->>Gateway: GET /jobs/{id}
    Gateway->>Orchestrator: GET /internal/jobs/{id}
    Orchestrator->>Database: Fetch Job + Result
    Orchestrator-->>Gateway: {job, result}
    Gateway-->>Frontend: Optimized Resume
```

---

## 4. Tools & Resources

### 4.1 Development Tools

| Tool              | Purpose                 |
| ----------------- | ----------------------- |
| VS Code           | Primary IDE             |
| Git               | Version control         |
| Docker Desktop    | Local container runtime |
| Postman/Insomnia  | API testing             |
| pgAdmin/TablePlus | Database management     |

### 4.2 Python Libraries

| Library             | Version | Purpose           |
| ------------------- | ------- | ----------------- |
| FastAPI             | 0.100+  | Web framework     |
| Uvicorn             | 0.20+   | ASGI server       |
| SQLAlchemy          | 2.0+    | Async ORM         |
| Pydantic            | 2.0+    | Data validation   |
| httpx               | 0.25+   | Async HTTP client |
| openai              | 1.0+    | OpenAI API client |
| google-generativeai | 0.3+    | Gemini API client |

### 4.3 Frontend Libraries

| Library               | Purpose         |
| --------------------- | --------------- |
| React 19              | UI framework    |
| TypeScript            | Type safety     |
| @supabase/supabase-js | Auth & realtime |
| react-router          | Client routing  |

---

## 5. Brief Summary: What Will Be Done

### Phase 1: Foundation (Completed)

- [x] Project structure setup (Monorepo)
- [x] Shared library scaffolding
- [x] LLM abstraction layer (OpenAI + Gemini)
- [x] Database models (SQLAlchemy)
- [x] Authentication middleware

### Phase 2: Core Services (In Progress)

- [x] Gateway Service (HTTP Proxy)
- [x] Orchestrator Service (API + Worker)
- [ ] Parser Service (PDF extraction)
- [ ] End-to-end testing

### Phase 3: Frontend Integration (Planned)

- [ ] Connect frontend to Gateway API
- [ ] Job status polling/websockets
- [ ] Result display & download

### Phase 4: Deployment (Planned)

- [ ] Docker Compose production config
- [ ] Cloud deployment (Railway/Render)
- [ ] Environment variable management

---

## 6. Database Schema (ERD)

```mermaid
erDiagram
    USERS ||--o{ RESUMES : owns
    USERS ||--o{ JOBS : creates
    RESUMES ||--o{ RESUME_VERSIONS : has
    JOBS ||--o{ OPTIMIZATIONS : produces
    RESUME_VERSIONS ||--o{ OPTIMIZATIONS : uses

    USERS {
        uuid id PK
        string email
        timestamp created_at
    }

    RESUMES {
        uuid id PK
        uuid user_id FK
        string title
        string source
        timestamp created_at
    }

    JOBS {
        uuid id PK
        uuid user_id FK
        string title
        text job_description
        enum status
        timestamp created_at
    }

    OPTIMIZATIONS {
        uuid id PK
        uuid job_id FK
        uuid resume_version_id FK
        int score
        json report
        text preview_md
    }

    TASK_QUEUE {
        uuid id PK
        enum task_type
        json payload
        enum status
        int attempts
    }
```

---

_Document generated for SmartResume Match school project methodology section._
