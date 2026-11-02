# Security and data boundaries

This is a local, synthetic-data demonstration. Do not use real banking/customer information.

- Runtime SQL is parameterized, selected from named tools and executed on a read-only SQLite connection.
- No tool transfers funds or modifies balances. Raw SQL is not accepted in the API schema.
- An optional shared API key protects analysis/configuration/metrics routes. There is no per-user identity,
  role-based access control or tenant isolation. Health and OpenAPI remain public.
- Default launchers and Compose host bindings use loopback. Authentication and HTTPS are required before
  exposing a service to other machines; that deployment is outside the delivered demonstration.
- Input checks are simple patterns. They do not provide complete PII detection or prompt-injection defense.
- External LLM use sends the question and evidence to the configured provider. TLS verification stays on.
- LLM response checks enforce format, known citations and numeral-token membership, not full faithfulness.
- Application audit events omit prompts, credentials and financial values. Counters are local/in-memory.
- `.env` and runtime data are ignored by Git. Manual website uploads must exclude them explicitly.

When reporting an issue, use a synthetic reproduction and exclude secrets or real customer data.
