# C3-M1 open questions

Points the spec leaves open, contradicts or that the scaffold does not carry yet. Each names the
spec section, the reading implemented here and who can decide. Nothing here is a silent guess: the
reading is in the code, marked as such.

| No. | Question | Spec | Reading implemented | To be decided by |
|---|---|---|---|---|
| 1 | The README makes the own database `c3_m1` (PostgreSQL, own user) obligatory, but the scaffold has no database driver, no `DATABASE_URL` reader and no database service in `docker-compose.yml`. How does the module run without them? | C3-M1 4, 5 (`DATABASE_URL`); FRAMEWORK 1; FRAMEWORK 4.8 (a value without an empty-value meaning is required) | `DATABASE_URL` **empty = in-memory transport** (`store_memory.py`), set = the PostgreSQL transport (`store_postgres.py`, schema `schema.sql`). Both answer the same functions and the same invariants, so the module runs at the hackathon without a server and switches over without a code change. If `DATABASE_URL` is set but the driver is missing, the module answers `501 not-implemented` and names the package — the same answer every unimplemented operation gives. | Maintainers (dependency and compose service), spec authors |
