# PawConnect - System Architecture

## 1. Overview

PawConnect follows a layered web application architecture.

The major layers are:

1. Frontend
2. Backend/API
3. Database
4. Cloud services
5. Authentication
6. Storage
7. Monitoring

---

# 2. High-Level Architecture

```text
                         USERS
                           |
                         HTTPS
                           |
                           v
                Application Load Balancer
                           |
                +----------+----------+
                |                     |
                v                     v
          Flask Instance 1      Flask Instance 2
                |                     |
                +----------+----------+
                           |
                      REST API
                           |
          +----------------+----------------+
          |                |                |
          v                v                v
      Cognito             RDS              S3
   Authentication      PostgreSQL       Image Storage
          |
          |
      User Identity

                           |
                       CloudWatch
                    Monitoring & Logs