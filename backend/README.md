# Agentic QA Backend

FastAPI backend for the Agentic QA application. Provides the API, job queue consumption, and test execution via the worker process.

## Running the worker

The worker consumes run jobs from the Redis queue, executes tests with Playwright via AgentExecutor, and emits events to Redis streams.

From the backend directory:

```bash
python scripts/run_worker.py
```

Or with `uv`:

```bash
uv run python scripts/run_worker.py
```

Requires `REDIS_URL` and `DATABASE_URL` in the environment (or in a `.env` file). See `.env.example` for all variables.

## Environment variables

See [.env.example](.env.example) for the full list. Worker-specific variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_CONSUMER_NAME` | `worker-{hostname}-{pid}-{uuid}` | Unique consumer name for Redis consumer group. Override for debugging or multi-worker setups. |
| `STUCK_RUN_TIMEOUT_MINUTES` | `10` | Runs left in `running` longer than this are marked `failed` with "Execution timeout". |
| `RECOVERY_CHECK_INTERVAL_SECONDS` | `60` | How often the worker checks for stuck runs. |

## Graceful shutdown

The worker handles **SIGTERM** and **SIGINT** (e.g. Ctrl+C):

1. Sets an internal shutdown flag.
2. Finishes processing the current job (if any).
3. Stops the stuck-run recovery task.
4. Closes the database connection pool and Redis connection.
5. Exits with code 0.

No new jobs are picked up after the signal; in-flight work is completed before exit.

## Stuck run recovery

Runs that stay in `running` (e.g. after a crash) are recovered by a background task:

- Every `RECOVERY_CHECK_INTERVAL_SECONDS` (default 60s), the worker queries for runs with `status = 'running'` and `started_at` older than `STUCK_RUN_TIMEOUT_MINUTES` (default 10 minutes).
- Each such run is updated to `status = 'failed'`, `error = 'Execution timeout'`, and `completed_at = NOW()`.
- An error event is appended to the run’s Redis stream so clients see the timeout.

This prevents runs from staying "running" indefinitely when the worker dies mid-execution.

## Troubleshooting

### Redis not configured (REDIS_URL)

Ensure `REDIS_URL` is set in `.env` or the environment. The worker exits with an error if Redis is not available at startup.

### Database connection errors

Check `DATABASE_URL` (e.g. Neon connection string). The worker retries transient DB/Redis connection errors up to 3 times with exponential backoff; persistent failures are logged and the run is marked failed.

### Consumer group

The worker creates the Redis consumer group on the `runs:queue` stream at startup (`ensure_consumer_group`). If this fails (e.g. Redis down), the worker logs the error and exits. You can inspect consumer groups with Redis CLI: `XINFO GROUPS runs:queue`.

### Run stuck in "running"

If a run stays in `running`:

1. Confirm the worker is running and that `STUCK_RUN_TIMEOUT_MINUTES` / `RECOVERY_CHECK_INTERVAL_SECONDS` are as expected.
2. After the timeout, the recovery task will mark it failed. To force it immediately, set `started_at` to an old timestamp (or wait for the next recovery cycle).
3. Check worker logs for "Recovered stuck run run_id=..." to confirm recovery ran.

### Worker logs

The worker uses the `worker` logger with timestamps and log levels. Startup logs include consumer name, Redis/DB configuration presence, and recovery/timeout settings. Health and idle heartbeats are logged periodically for monitoring.
