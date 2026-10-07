# PawConnect Rules

## Architecture

- Frontend must not directly access the database.
- Database access must go through the backend.
- Business logic belongs in the backend.
- APIs must validate input.
- Authorization must be enforced server-side.

## Security

- Never commit `.env`.
- Never hardcode secrets.
- Never expose database credentials.
- Never store passwords in plaintext.
- Validate uploaded files.
- Protect administrative operations.
- Apply RBAC.

## Database

- Use primary keys.
- Use foreign keys where appropriate.
- Maintain referential integrity.
- Avoid unnecessary duplication.
- Keep naming consistent.

## API

- Follow REST conventions.
- Use appropriate HTTP methods.
- Maintain consistent responses.
- Handle errors properly.
- Do not silently break existing endpoints.

## Cloud

Every cloud service must have a clear purpose.

Do not add technologies merely to make the project look complex.

Avoid unnecessary:

- Kubernetes
- Kafka
- Redis
- Microservices
- Service meshes
- Complex event-driven systems

Priority:

Understandability
↓
Correctness
↓
Security
↓
Cloud Integration
↓
Scalability