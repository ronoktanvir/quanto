# Security

Quanto is under construction and is not approved for live trading.

Keep API keys in local environment variables or an ignored local `.env` file. Never include keys in code, prompts, logs, screenshots, or issue bodies. The project does not search other applications for credentials. Public sample API identifiers supplied in provider documentation are distinct from user secrets and must be identified as such.

Research processes must not receive live broker credentials. The localhost dashboard exposes read-only status and binds to loopback. It is not an authenticated remote dashboard and must not be exposed publicly through a tunnel.

Report a vulnerability privately to the repository owner or through GitHub private vulnerability reporting when enabled. Include a minimal reproduction with synthetic data and no credentials. Do not create a public issue containing sensitive information.

Local audit records provide application-level append-only behavior and integrity checks. An administrator with filesystem access can replace the database and records; this is not an immutable or independently notarized archive.
