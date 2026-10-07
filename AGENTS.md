# AGENTS.md

## Purpose

Instructions for AI coding agents working on PawConnect.

## Before Making Changes

Read:

- README.md
- AGENTS.md
- RULES.md
- SKILLS.md
- docs/PROJECT.md
- docs/REQUIREMENTS.md
- docs/ARCHITECTURE.md
- IMPLEMENTATION_STATUS.md

For database changes:
- docs/DATABASE.md

For API changes:
- docs/API.md

For cloud changes:
- docs/CLOUD.md
- docs/DEPLOYMENT.md

For security changes:
- docs/SECURITY.md

## Development Rules

The agent must:

- Inspect existing code before creating new code.
- Reuse existing functionality.
- Avoid unnecessary dependencies.
- Follow the documented architecture.
- Keep frontend/backend/database responsibilities separated.
- Never hardcode secrets.
- Use environment variables.
- Validate input.
- Enforce authorization server-side.
- Respect RBAC.
- Maintain API contracts.
- Maintain database consistency.
- Update documentation when architecture changes.
- Make incremental changes.

## Architecture Changes

The agent must not silently change the architecture.

If a requested change conflicts with the documented architecture:

1. Identify the conflict.
2. Explain the impact.
3. Propose alternatives.
4. Wait for approval before making a major architectural change.