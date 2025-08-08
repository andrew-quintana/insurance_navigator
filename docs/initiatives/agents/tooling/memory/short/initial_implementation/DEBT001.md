# DEBT001.md — Technical Debt Summary (Short-Term Chat Memory MVP)

## Outstanding Assumptions

- Heuristic token counting instead of exact tokenizer
- In-memory rate limit; no shared store across replicas
- `trigger_source` not persisted in queue schema (observability gap)

## Known Debt Areas

- Metrics/monitoring: no built-in counters/gauges for success rate, queue depth, or latency
- Load testing: no automated suite for 1,000+ concurrent updates / 10,000 stored memories
- Integration tests: memory endpoints not yet covered by running-server tests
- Size management: guidance message only; no automatic chat rollover tooling

## Mitigation Plans

- Add minimal metrics hooks and a simple exporter compatible with Prometheus in future iteration
- Extend integration tests to include memory POST/GET path with auth
- Add lightweight Locust or asyncio-based load script targeting update and retrieval benchmarks
- Consider persisting `trigger_source` and adding an index for analytics

## Follow-up Actions

1) Implement metrics and dashboards (success rate, queue time, retrieval p95)
2) Add integration tests for memory endpoints; run in CI with server boot
3) Create load/perf scripts and include in CI (nightly)
4) Evaluate shared rate limiter (Redis) for multi-replica readiness
5) Consider exact tokenizer swap-in behind interface if needed