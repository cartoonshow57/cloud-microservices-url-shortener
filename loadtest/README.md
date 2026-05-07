# Load Testing

Benchmarks for the URL Shortener microservices using [wrk](https://github.com/wg/wrk).

## Usage

```bash
# Test against local Docker setup
./loadtest/run_loadtest.sh http://localhost

# Test against Azure VM
./loadtest/run_loadtest.sh http://<VM_IP>

# Custom parameters: target, duration, connections, threads
./loadtest/run_loadtest.sh http://localhost 60s 50 4
```

## Tests Run

1. **Health endpoint** (GET /api/health) — baseline latency with no business logic
2. **Shorten endpoint** (POST /shorten) — write path through API service to Redis
3. **Redirect endpoint** (GET /r/{code}) — read path through redirect service from Redis

## Collecting Results

- Raw results are saved to `loadtest/results/`
- While tests run, open Grafana at `http://<host>:3000` (admin/admin) to watch live metrics
- Take screenshots of the Grafana dashboard during load for your presentation
