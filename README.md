# CastorPay (Castor Platform)

> **Production-Grade Payment Gateway & Embedded Finance Infrastructure**  
> Built for High-Throughput Micropayments, Cross-Border Treasury, and Multi-Currency Virtual Accounts.

[![CI/CD Pipeline](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-blue?logo=github-actions)](https://github.com)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![Redux Toolkit](https://img.shields.io/badge/Redux_Toolkit-RTK_Query-764ABC?logo=redux&logoColor=white)](https://redux-toolkit.js.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![AWS LocalStack](https://img.shields.io/badge/AWS-LocalStack_Emulated-FF9900?logo=amazon-aws&logoColor=white)](https://localstack.cloud)

---

## 1. Executive Summary & Domain Context

**CastorPay** is a fintech payment infrastructure platform engineered to solve the complex challenges of **Embedded Finance** and **Cross-Border Payments**. Designed to meet the production standards of institutions processing high-volume transactions (such as gaming micropayments across Africa and UK remittances), CastorPay unifies payment orchestration, multi-currency ledgering, treasury management, and banking partner integrations into a reliable, distributed system.

### Core Product Lines
1. **Embedded Finance & Micropayments**:
   - **Multi-Currency Dynamic Virtual Accounts (DVA)**: Instant issuance of dedicated collection accounts in NGN, GBP, and USD with automated inbound transfer matching.
   - **Gaming Micropayments**: Low-latency, idempotent transaction ingestion designed for sub-second game credits and micro-billing.
   - **Escrow Contracts**: Milestone-based fund lock-up, dispute mediation, and conditional releases.
2. **Cross-Border Payments & Treasury**:
   - **Payment Orchestration**: Smart routing across African rails (Paystack, Flutterwave) and European rails (Stripe / UK Faster Payments) with automated health failover.
   - **FX Quote Locking Engine**: Real-time currency conversions with a guaranteed 60-second quote rate lock and treasury spread management.
   - **Automated 3-Way Reconciliation**: Ledger $\leftrightarrow$ Gateway $\leftrightarrow$ Bank settlement statement verification with automated discrepancy flagging.

---

## 2. Engineering Pillars & Architectural Primitives

Fintech payment systems demand guarantees that typical web applications do not require. CastorPay implements six core engineering primitives:

### A. Immutable Double-Entry General Ledger
- Financial balances are **never** stored as simple mutable numbers (`UPDATE accounts SET balance = balance + 100`).
- Every monetary event writes an immutable **Journal Entry** containing balanced debit and credit **Ledger Lines**:
  $$\sum \text{Debits} = \sum \text{Credits}$$
- Accounts follow the 5 standard financial classes:
  - **Asset** (e.g., Bank Settlement Clearing, Partner Float)
  - **Liability** (e.g., Merchant Available Balances, Customer Escrow Withholdings)
  - **Equity** (e.g., Platform Capital)
  - **Revenue** (e.g., Processing Fees, FX Spread Margin)
  - **Expense** (e.g., Provider Network Fees)
- All monetary amounts are stored as **64-bit integers in minor units** (kobo, pence, cents) to eliminate floating-point rounding errors.

### B. Distributed Idempotency Engine
- Clients supply an `Idempotency-Key: <UUID>` header for state-changing requests.
- Redis-backed distributed locks (`SETNX` with TTL) prevent concurrent duplicate requests from executing twice (e.g., double-charging during network timeouts).
- Completed responses are atomically cached (payload, headers, status) with a 24-hour expiration. Repeated requests immediately return the cached payload without re-executing business logic.

### C. Transactional Outbox & Event-Driven Queues
- Guarantees zero split-brain between database commits and message bus publishing.
- State changes write to a local `outbox_events` table within the same ACID transaction.
- An asynchronous relay worker dispatches outbox events to an AWS SQS queue (emulated locally via LocalStack).
- Workers consume events with **exponential backoff + jitter** retry policies.
- Messages failing more than 3 attempts are isolated in a **Dead-Letter Queue (DLQ)** with an admin inspection and 1-click replay API.

### D. Pluggable Payment Provider Strategy Pattern
- All upstream payment integrations implement `PaymentProviderInterface`:
  - `initialize_payment()`
  - `verify_payment()`
  - `create_virtual_account()`
  - `fetch_settlement_report()`
- Adapters include:
  - **Paystack Rail**: NGN bank transfers, card checkout, NUBAN generation.
  - **Flutterwave Rail**: Pan-African mobile money and card rails.
  - **Stripe Rail**: GBP/EUR cards, SEPA, UK Faster Payments.
  - **Mock Bank Rail**: High-fidelity local simulation rail with configurable latency (50ms–2000ms), simulated network drops, and automated webhook dispatch for chaos and integration testing.

### E. 3-Way Automated Reconciliation Engine
- Ingests external bank settlement files (CSV/JSON).
- Executes 3-way matching:
  $$\text{Internal Ledger} \iff \text{Gateway Transaction Logs} \iff \text{Bank Partner Statements}$$
- Automatically detects and flags variances: `UNMATCHED_IN_BANK`, `UNMATCHED_IN_LEDGER`, `AMOUNT_DISCREPANCY`, `STATUS_MISMATCH`.

### F. Dual-Mode React Dashboard (RTK Query + Tailwind)
- **Merchant Portal**: Real-time multi-currency wallet overview, virtual account generator, FX swap calculator with live 60s countdown timer, payment link creator, API key manager, and live webhook ping tester.
- **Admin & Treasury Portal**: Global liquidity float monitor, provider health and latency metrics, Dead-Letter Queue message explorer & replay, and reconciliation audit interface.

---

## 3. Complete Project Folder Structure

The project is structured into clean micro-layers separating API ingress, business services, financial ledgers, provider adapters, background workers, infrastructure as code, and the frontend web platform:

```
castor_pay/
├── .github/
│   └── workflows/
│       ├── ci.yml                             # Automated linting, type-checking, unit & chaos tests
│       └── docker-build.yml                   # Multi-stage container build and vulnerability scanning
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py                        # FastAPI dependency injection (DB, Redis, Auth, RBAC)
│   │   │   └── v1/
│   │   │       ├── api.py                     # Aggregated v1 router
│   │   │       └── endpoints/
│   │   │           ├── auth.py                # JWT authentication, merchant API keys, Cognito adapter
│   │   │           ├── payments.py            # Charge initialization, checkout sessions, refunds
│   │   │           ├── virtual_accounts.py    # DVA generation (NGN, GBP, USD), inbound transfers
│   │   │           ├── fx_rates.py            # Live exchange rates, 60s quote locks, cross-border swaps
│   │   │           ├── escrow.py              # Escrow contracts, milestone locks, dispute releases
│   │   │           ├── webhooks.py            # Inbound provider webhook listeners (HMAC verification)
│   │   │           ├── ledger.py              # Chart of accounts, journal entries, balance audit
│   │   │           ├── reconciliation.py      # Statement ingestion & discrepancy resolution
│   │   │           └── admin.py               # Treasury reserves, provider status, DLQ inspection/replay
│   │   ├── core/
│   │   │   ├── config.py                      # Pydantic v2 Settings (environment variables)
│   │   │   ├── security.py                    # HMAC-SHA256 signing, API Key hashing, JWT tokens
│   │   │   ├── idempotency.py                 # Redis distributed locking & response cache middleware
│   │   │   ├── exceptions.py                  # Domain exception hierarchy (LedgerImbalance, QuoteExpired)
│   │   │   └── logging.py                     # Structured JSON logging with trace & correlation IDs
│   │   ├── db/
│   │   │   ├── base.py                        # Declarative Base metadata
│   │   │   └── session.py                     # Async SQLAlchemy 2.0 engine & session maker
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py                        # Merchant, Admin, Role-Based Access Control (RBAC)
│   │   │   ├── ledger.py                      # Account, JournalEntry, LedgerLine, AccountBalance
│   │   │   ├── payment.py                     # PaymentTransaction, PaymentMethod, OutboxEvent
│   │   │   ├── virtual_account.py             # DedicatedVirtualAccount, InboundDeposit
│   │   │   ├── fx.py                          # FXRate, FXQuote (with TTL), FXConversion
│   │   │   ├── escrow.py                      # EscrowContract, EscrowMilestone, EscrowDispute
│   │   │   └── reconciliation.py              # ReconBatch, ReconStatementLine, ReconDiscrepancy
│   │   ├── schemas/
│   │   │   ├── auth.py                        # Pydantic request/response schemas
│   │   │   ├── payment.py
│   │   │   ├── virtual_account.py
│   │   │   ├── fx.py
│   │   │   ├── escrow.py
│   │   │   ├── ledger.py
│   │   │   └── reconciliation.py
│   │   ├── services/
│   │   │   ├── ledger_service.py              # Double-entry invariant logic & balance queries
│   │   │   ├── orchestration_service.py       # Smart routing, failover, fee calculation
│   │   │   ├── fx_service.py                  # Rate calculation, treasury spread, 60s TTL validator
│   │   │   ├── escrow_service.py              # Escrow contract state machine
│   │   │   ├── reconciliation_service.py      # 3-Way reconciliation algorithm
│   │   │   └── webhook_service.py             # Outbound merchant webhook dispatcher with HMAC signature
│   │   ├── providers/
│   │   │   ├── base.py                        # PaymentProviderInterface abstract class
│   │   │   ├── mock_bank_adapter.py           # Chaos-ready simulated bank rail (latency, failure, webhooks)
│   │   │   ├── paystack_adapter.py            # Paystack NGN cards, bank transfers, NUBAN
│   │   │   ├── flutterwave_adapter.py         # Flutterwave Pan-African rails
│   │   │   └── stripe_adapter.py              # Stripe cards, UK Faster Payments
│   │   ├── workers/
│   │   │   ├── outbox_relay.py                # Polls outbox_events and publishes to SQS
│   │   │   ├── event_consumer.py              # Consumes SQS messages with exponential backoff & DLQ
│   │   │   └── recon_processor.py             # Async worker processing daily bank statements
│   │   └── main.py                            # FastAPI application factory & lifecycle events
│   ├── alembic/                               # Database migrations
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   ├── tests/
│   │   ├── conftest.py                        # Pytest fixtures, test database, mock Redis/SQS
│   │   ├── unit/
│   │   │   ├── test_ledger_math.py            # Verifies sum(debits) == sum(credits) invariants
│   │   │   ├── test_idempotency.py            # Tests duplicate requests & concurrent lock contention
│   │   │   ├── test_fx_quotes.py              # Verifies quote pricing and 60-second expiration logic
│   │   │   └── test_escrow_state_machine.py   # State transitions: funded -> locked -> released / refunded
│   │   ├── integration/
│   │   │   ├── test_payment_orchestration.py  # End-to-end payment creation, adapter call, and ledger update
│   │   │   ├── test_virtual_account_payin.py  # Inbound transfer webhook -> DVA matching -> ledger credit
│   │   │   └── test_3way_reconciliation.py    # Ingests settlement file, identifies variances
│   │   └── chaos/
│   │       └── test_dlq_and_retries.py        # Simulates 3 network drops -> verifies DLQ isolation -> replayed
│   ├── Dockerfile                             # Multi-stage Docker build for backend & workers
│   ├── pyproject.toml                         # Project metadata, Ruff, MyPy, and Pytest configs
│   ├── requirements.txt                       # Production Python dependencies
│   └── requirements-dev.txt                   # Testing & development dependencies
│
├── frontend/
│   ├── public/                                # Static assets, logos, favicon
│   ├── src/
│   │   ├── api/
│   │   │   ├── baseApi.ts                     # RTK Query root base query with JWT & error interceptors
│   │   │   ├── authApi.ts                     # Login, token refresh, API key management
│   │   │   ├── paymentsApi.ts                 # Payments, checkout sessions, transactions
│   │   │   ├── virtualAccountsApi.ts          # DVA issuance and pay-in history
│   │   │   ├── fxApi.ts                       # Live rates, quote generation, cross-border swaps
│   │   │   ├── escrowApi.ts                   # Escrow contracts & milestones
│   │   │   ├── adminApi.ts                    # DLQ inspection, retry triggering, treasury reserves
│   │   │   └── reconApi.ts                    # Statement upload and discrepancy reports
│   │   ├── components/
│   │   │   ├── layout/                        # Sidebar, Navbar, Breadcrumbs, Notifications
│   │   │   ├── common/                        # Buttons, Badges, Modals, StatCards, LoadingSpinners
│   │   │   ├── payments/                      # CheckoutModal, TransactionTimeline, ReceiptView
│   │   │   ├── virtualAccounts/               # DVACard, CopyableAccountBox, PayinFeed
│   │   │   ├── fx/                            # RateTicker, SwapCalculator, CountdownTimer (60s)
│   │   │   ├── escrow/                        # ContractTimeline, MilestoneProgressBar, DisputeModal
│   │   │   └── admin/                         # DLQMessageInspector, ProviderHealthGrid, ReconDiffTable
│   │   ├── hooks/
│   │   │   ├── useAuth.ts                     # Role-based permission checks
│   │   │   └── useCountdown.ts                # Real-time countdown for FX quotes
│   │   ├── pages/
│   │   │   ├── auth/
│   │   │   │   └── LoginPage.tsx
│   │   │   ├── merchant/
│   │   │   │   ├── DashboardPage.tsx          # Multi-currency balances & transaction velocity
│   │   │   │   ├── TransactionsPage.tsx       # Searchable ledger & transaction history
│   │   │   │   ├── VirtualAccountsPage.tsx    # NGN, GBP, USD account generation
│   │   │   │   ├── FXExchangePage.tsx         # Cross-border conversion with 60s rate lock
│   │   │   │   ├── EscrowPage.tsx             # Escrow contracts and milestone tracking
│   │   │   │   └── DeveloperPage.tsx          # API keys, webhook URLs, and interactive webhook simulator
│   │   │   └── admin/
│   │   │       ├── TreasuryPage.tsx           # Float balances across bank rails & system liquidity
│   │   │       ├── ProvidersPage.tsx          # Provider routing weights, latency & health status
│   │   │       ├── DLQMonitorPage.tsx         # Dead-letter queue viewer and 1-click retry replay
│   │   │       └── ReconciliationPage.tsx     # Bank statement upload & variance reconciliation
│   │   ├── store/
│   │   │   ├── store.ts                       # Redux store configureStore with RTK Query middleware
│   │   │   └── slices/
│   │   │       ├── authSlice.ts               # User session and active role state
│   │   │       └── uiSlice.ts                 # Notification toasts and modal states
│   │   ├── types/                             # TypeScript definitions for entities and API payloads
│   │   ├── App.tsx                            # React router routes & protected route guards
│   │   ├── index.css                          # Tailwind CSS directives
│   │   └── main.tsx                           # Application DOM mount
│   ├── Dockerfile                             # Multi-stage Docker build (Node build -> Nginx alpine)
│   ├── nginx.conf                             # Nginx reverse proxy configuration for SPA routing
│   ├── package.json                           # React 18, Vite, RTK Query, Tailwind dependencies
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── vite.config.ts
│
├── terraform/
│   ├── main.tf                                # AWS provider & base architecture
│   ├── variables.tf                           # VPC, environment, DB credentials variables
│   ├── outputs.tf                             # API Gateway URLs, SQS ARNs, Cognito User Pool IDs
│   ├── modules/
│   │   ├── api_gateway/                       # AWS HTTP API Gateway with Cognito authorizers
│   │   ├── compute/                           # AWS ECS Fargate task definitions or Lambda handlers
│   │   ├── database/                          # Amazon RDS Aurora PostgreSQL & DynamoDB tables
│   │   ├── messaging/                         # AWS SQS FIFO/Standard queues, DLQ, EventBridge bus
│   │   └── monitoring/                        # AWS CloudWatch alarms, SNS error alerts
│   └── environments/
│       ├── localstack.tf                      # LocalStack endpoint overrides for local testing
│       └── production.tfvars
│
├── docker-compose.yml                         # Orchestrates Postgres, Redis, LocalStack, Backend, Worker, Frontend
├── .env.example                               # Annotated environment variable template
├── Makefile                                   # One-touch developer commands (make up, make test, make lint)
└── README.md                                  # Complete architecture design document & developer guide
```

---

## 4. System Architecture Diagram

![System Architecture Diagram](./castor-pay-architectural-diagram.svg)

---

## 5. Technology Stack Matrix

| Layer | Technologies | Rationale |
| :--- | :--- | :--- |
| **Backend API** | Python 3.12, FastAPI, Pydantic v2 | High-throughput asynchronous performance, automatic OpenAPI documentation, strict type validation. |
| **ORM & Database** | SQLAlchemy 2.0 (Async), Alembic, PostgreSQL 16 | ACID-compliant transactional guarantees for double-entry financial ledger lines; zero floating-point math. |
| **Caching & Locking** | Redis 7 (`aioredis`) | Sub-millisecond distributed locks for idempotency keys and TTL storage for 60-second FX quotes. |
| **Event Bus & Queues** | AWS SQS, EventBridge, LocalStack | Reliable asynchronous decoupling, transactional outbox emission, poison-pill isolation via Dead-Letter Queues. |
| **Frontend Web** | React 18, Vite, TypeScript, Tailwind CSS | Fast developer loop, type-safe UI, responsive fintech design. |
| **State & Data Fetching**| Redux Toolkit, RTK Query | Normalized server-cache management, automatic polling, optimistic UI updates. |
| **Infrastructure as Code**| Terraform (AWS Modules) | Repeatable declarative infrastructure provisioning for API Gateway, ECS Fargate, RDS, and SQS. |
| **Containers & CI/CD** | Docker, Docker Compose, GitHub Actions | Identical local & CI environments, multi-stage cached builds, comprehensive automated test suites. |

---

## 6. Getting Started & Running via Docker

### Prerequisites
- Docker Engine & Docker Compose (`docker compose version >= 2.20`)
- Git

### One-Command Quickstart

1. **Clone the repository and enter the directory**:
   ```bash
   cd /home/techyz-admin/sevenwings/03_projects/castor_pay
   ```

2. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   ```

3. **Launch the Entire Stack via Docker Compose**:
   ```bash
   docker compose up --build
   ```

4. **Access the Running Services**:
   - **FastAPI Interactive Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **FastAPI ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
   - **Merchant & Admin Dashboard**: [http://localhost:5173](http://localhost:5173)
   - **LocalStack AWS Health**: [http://localhost:4566/_localstack/health](http://localhost:4566/_localstack/health)
   - **PostgreSQL**: `localhost:5432` (`castor_user` / `castor_password`)
   - **Redis**: `localhost:6379`

---

## 7. Sample API Usage & Workflows

### 1. Initialize an Idempotent Payment
```bash
curl -X POST http://localhost:8000/api/v1/payments/initialize \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Idempotency-Key: c9b2f6b4-21db-49cf-82e7-9a848c9bf723" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 250000,
    "currency": "NGN",
    "customer_email": "gamer@ab-inbev-micropay.com",
    "payment_method": "card",
    "metadata": {
      "game_session_id": "game_10923",
      "platform": "gaming_micropayments"
    }
  }'
```
*Note: Amount is passed in minor units (250,000 NGN kobo = 2,500.00 NGN).*

### 2. Generate a Dedicated Virtual Account (DVA)
```bash
curl -X POST http://localhost:8000/api/v1/virtual-accounts \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "currency": "NGN",
    "merchant_customer_id": "cust_90218",
    "customer_name": "Tunde Bakare",
    "bvn_verified": true
  }'
```

### 3. Request a 60-Second Guaranteed FX Quote
```bash
curl -X POST http://localhost:8000/api/v1/fx/quotes \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "source_currency": "GBP",
    "target_currency": "NGN",
    "source_amount": 10000
  }'
```
*Response returns guaranteed rate, target amount, and an `expires_at` timestamp locked for exactly 60 seconds.*

---

## 8. Verification & Automated Test Matrix

Run all tests inside Docker or directly with Pytest:

```bash
# Run unit & ledger invariant tests
docker compose run --rm backend pytest tests/unit/ -v

# Run concurrency & idempotency chaos tests
docker compose run --rm backend pytest tests/unit/test_idempotency.py -v

# Run end-to-end integration flows
docker compose run --rm backend pytest tests/integration/ -v

# Run full test suite with coverage
docker compose run --rm backend pytest --cov=app --cov-report=term-missing
```

---

## 9. License
Distributed under the MIT License.
