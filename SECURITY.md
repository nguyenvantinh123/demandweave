# Security policy

Report vulnerabilities privately to the repository owner. Do not open public issues containing exploitable details.

Never commit credentials. Rotate `JWT_SECRET` and `MANDATE_SECRET` in production. Production deployments must use TLS, managed secrets, database backups and external identity verification.
