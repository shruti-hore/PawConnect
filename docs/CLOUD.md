
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
| Elastic Beanstalk | Application deployment |
| EC2 | Underlying compute |
| RDS | PostgreSQL database |
| S3 | Image/object storage |
| Cognito | Authentication |
| Application Load Balancer | Load balancing |
| CloudWatch | Monitoring and logs |

---

# 4. Service Models

### PaaS

Elastic Beanstalk provides a managed application deployment environment.

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