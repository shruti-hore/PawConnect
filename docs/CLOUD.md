
---

# 7. `CLOUD.md`

```md
# PawConnect - Cloud Architecture

## 1. Cloud Objective

PawConnect uses cloud computing to provide:

- Remote accessibility
- Managed infrastructure
- Scalability
- Cloud storage
- Managed authentication
- Monitoring
- Load balancing
- CI/CD deployment

---

# 2. Cloud Model

PawConnect uses a public cloud environment.

The primary cloud provider is AWS.

---

# 3. Cloud Services

| AWS Service | Purpose |
|---|---|
| EC2 | Host for the Docker Compose frontend and API containers |
| Elastic Beanstalk | Optional managed application deployment environment |
| RDS | PostgreSQL database |
| S3 | Image/object storage |
| Cognito | Authentication |
| Application Load Balancer | Load balancing |
| CloudWatch | Monitoring and logs |

---

# 4. Service Models

### PaaS

Elastic Beanstalk is an optional managed deployment target. The direct EC2
deployment described in [EC2-DOCKER.md](EC2-DOCKER.md) runs the containers on
EC2 instead.

### IaaS

EC2 provides virtual compute infrastructure underneath the application environment.

### Managed Database

Amazon RDS manages PostgreSQL infrastructure.

### Object Storage

Amazon S3 provides cloud object storage.

---

# 5. Deployment Architecture

```text
Internet
   |
   v
Application Load Balancer
   |
   +----------------+
   |                |
   v                v
App Instance 1   App Instance 2
   |                |
   +-------+--------+
           |
           v
        RDS
     PostgreSQL

           +
           |
           v
          S3

           +
           |
           v
       Cognito

           +
           |
           v
      CloudWatch