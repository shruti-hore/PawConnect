
---

# 10. `DEPLOYMENT.md`

```md
# PawConnect - Deployment Strategy

## 1. Deployment Objective

The objective is to deploy PawConnect to AWS and create a repeatable deployment process.

The deployment pipeline uses:

```text
Developer
    ↓
GitHub
    ↓
GitHub Actions
    ↓
Build
    ↓
Test
    ↓
AWS Deployment
    ↓
PawConnect

