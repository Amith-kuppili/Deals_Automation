# Extreme Deal Hunter

A 24/7 Extreme Deal Hunter and Alert System that monitors product APIs and detects genuine exceptional discounts.

## 🚀 Architecture

The system uses a distributed architecture:
- **API**: FastAPI for management and triggering tasks.
- **Worker**: Celery for asynchronous processing of product updates and deal scoring.
- **Broker**: Redis for task queuing.
- **Database**: PostgreSQL for persistent storage of products, price history, and deal scores.
- **Scheduler**: Celery Beat for periodic polling of product feeds.

## 🛠️ Tech Stack

- Python 3.12+
- FastAPI
- Celery & Redis
- PostgreSQL & SQLAlchemy (Async)
- Docker & Docker Compose

## 📦 Local Setup

### 1. Environment Configuration
Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

## 🛒 E-Commerce Providers

The system supports multiple marketplaces with a provider-based architecture:

### Flipkart
- **Marketplace**: Flipkart
- **Provider**: QuickCommerce
- **Role**: Primary

### Amazon
- **Marketplace**: Amazon
- **Primary**: OpenWeb Ninja
- **Fallback**: Bright Data

**Failover Logic**: The system attempts OpenWeb Ninja first. If the provider is unavailable, rate limited, unauthorized, or its quota is exhausted, the system automatically falls back to Bright Data.

## 📈 Price History & Deal Engine (Milestone 4)

The system continuously builds a long-term source of truth for product prices to detect genuine extreme discounts.

### How it Works
1. **Local History**: Every price observation is stored in `PriceHistory`.
2. **Deduplication**: Only meaningful price changes are recorded to save space.
3. **ReefAPI Bootstrap**: If a product is new or has insufficient local history, the system optionally fetches historical data from ReefAPI to bootstrap the dataset.
4. **Robust Baseline**: Instead of trusting MRP, the system calculates a baseline using the historical median (e.g., 30-day median).
5. **Genuine Discount Detection**:
   - **Effective Discount**: Calculated as `1 - (current_price / historical_baseline)`.
   - **Extreme Deal**: A product is classified as an `EXTREME_DEAL` only if the effective discount is $\ge 90\%$ and historical confidence is high.
   - **False Discount Protection**: If the marketplace claims a huge discount but the current price is close to the historical median, it is classified as a `FALSE_DISCOUNT`.

### Deal Classifications
- `EXTREME_DEAL`: Genuine, highly unusual discount.
- `GOOD_DEAL`: Meaningful historical discount.
- `WATCH`: Interesting price movement.
- `FALSE_DISCOUNT`: Misleading marketplace discount.
- `INSUFFICIENT_HISTORY`: Not enough data to classify reliably.

### 2. Run with Docker Compose
```bash
docker compose up -d --build
```

### 3. Database Migrations
The database is managed by Alembic. To run migrations:
```bash
docker compose exec api alembic upgrade head
```

### 4. Test the Pipeline
You can trigger a test task via the API:
```bash
curl -X POST http://localhost:8000/test-task -H "Content-Type: application/json" -d '{"test": "data"}'
```
Then check the status using the `task_id` returned:
```bash
curl http://localhost:8000/task-status/<task_id>
```

## Railway Deployment

Create separate Railway services that deploy this same repository:

1. **PostgreSQL**: add a Railway PostgreSQL plugin/service and copy `DATABASE_URL`
   into the API, worker, and Beat services.
2. **Redis**: add a Railway Redis plugin/service and set `REDIS_URL`,
   `CELERY_BROKER_URL`, and `CELERY_RESULT_BACKEND` to the Redis connection URL.
3. **API**: use `railway.toml`; Railway sets `PORT` automatically.
4. **Worker**: set the start command to
   `celery -A src.redis.celery_app worker --loglevel=info --pool=solo`.
5. **Beat**: set the start command to
   `celery -A src.redis.celery_app beat --loglevel=info --schedule=/tmp/celerybeat-schedule`.

The API service runs `alembic upgrade head` before starting. At least one
PostgreSQL and one Redis service must be reachable by every service.

## 🛣️ Roadmap

- [x] Milestone 1: Core Infrastructure (FastAPI, Postgres, Redis, Celery)
- [x] Milestone 2: Mock Provider Pipeline
- [x] Milestone 3: E-Commerce Integration (Flipkart & Amazon)
- [ ] Milestone 4: Deal Engine & Price History
-
- [ ] Milestone 6: Telegram Alerts
- [ ] Milestone 7: Smart Polling & Deduplication
- [ ] Milestone 8: Amazon Creators API
- [ ] Milestone 9: Dockerization (Complete)
- [ ] Milestone 10: Railway Deployment
