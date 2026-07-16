# Architecture

The API owns deterministic domain logic. AI adapters are optional. PostgreSQL stores tenant-scoped records, Redis supports workers, React provides the operator interface, and the ledger records sensitive transitions.

```mermaid
flowchart TD
UI-->API
Connectors-->API
API-->DB[(PostgreSQL)]
API-->Redis
Redis-->Worker
Worker-->Compiler
Compiler-->DB
API-->Ledger
```
