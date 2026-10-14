# PawConnect

## Overview

PawConnect is a secure, cloud-deployed animal welfare platform that connects NGOs, rescuers, volunteers, donors, adopters, and general users.

## Problem Statement

Animal rescue, adoption, volunteering, and welfare activities are often distributed across different platforms. This makes it difficult for users to discover animals, report animals in need, connect with organizations, and track cases.

## Proposed Solution

PawConnect provides a centralized platform for:

- Animal adoption
- Rescue reporting
- NGO/rescuer management
- Volunteer opportunities
- Donation records
- Adoption applications
- Administrative moderation

## Main Features

- User authentication
- Animal listings
- Animal details
- Rescue case reporting
- Image upload
- Adoption applications
- Volunteer management
- Donation records
- NGO verification
- Admin moderation

## User Roles

- General User
- Adopter
- Donor
- Volunteer
- NGO / Rescuer
- Administrator

## Technology Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python Flask
- API: REST
- Database: PostgreSQL
- Cloud: AWS
- Storage: Amazon S3
- Authentication: Amazon Cognito
- Deployment: AWS EC2 with Docker Compose
- Monitoring: Amazon CloudWatch
- CI/CD: GitHub Actions
- Version Control: Git + GitHub

## High-Level Architecture

User
↓
Frontend
↓
Flask REST API
↓
Authentication + Business Logic
↓
PostgreSQL / S3 / AWS Services

## Project Structure

Brief explanation of root folders and docs.

## Docker on AWS EC2

The Docker Compose deployment packages the Flask API and static frontend and is
designed to connect to an external PostgreSQL database such as Amazon RDS. See
[docs/EC2-DOCKER.md](docs/EC2-DOCKER.md) for setup and deployment instructions.

### Quick deployment steps (Ubuntu 24.04 EC2)

1. Launch an Ubuntu 24.04 EC2 instance in the same VPC as your RDS database.
   In its security group, allow inbound TCP 80 from your intended users and
   restrict SSH (TCP 22) to your IP. Do not expose backend port 5000. Allow
   inbound TCP 5432 to the RDS security group from the EC2 security group.
2. Connect to the instance over SSH and install Docker, Compose, and Git:

   ```sh
   sudo apt update
   sudo apt install -y docker.io docker-compose-v2 git
   sudo systemctl enable --now docker
   ```

3. Clone the repository and enter its directory:

   ```sh
   git clone https://github.com/shruti-hore/PawConnect.git
   cd PawConnect
   ```

4. Create and edit the production environment file:

   ```sh
   cp .env.example .env
   nano .env
   ```

   Set `DATABASE_URL` to the RDS PostgreSQL connection URL, `SECRET_KEY` to a
   strong random value (for example, generate one with `openssl rand -hex 32`),
   and configure the Cognito values. Compose will not start without
   `DATABASE_URL` and `SECRET_KEY`. Keep `.env` private and never commit it.
5. Build the images, run the database migrations, and start the app:

   ```sh
   sudo docker compose build
   sudo docker compose run --rm backend flask --app "app:create_app()" db upgrade
   sudo docker compose up -d
   ```

6. Verify it is running, then open `http://EC2_PUBLIC_DNS/` in a browser:

   ```sh
   sudo docker compose ps
   sudo docker compose logs --tail=100
   curl http://localhost/api/health
   ```

For updates, pull the latest code, rebuild, apply any new migrations, then
recreate the containers. Back up RDS before migrations. For HTTPS, put an
Application Load Balancer or another TLS-terminating proxy in front of EC2.
See [docs/EC2-DOCKER.md](docs/EC2-DOCKER.md) for additional deployment and
database security details.

## Cloud Architecture

Brief explanation of AWS deployment.

## ICC Concepts Demonstrated

- Cloud deployment
- Managed database
- Object storage
- Authentication
- Security
- Scalability
- Monitoring
- Load balancing
- CI/CD

## Future Scope

- Real-time communication
- Mobile application
- AI-based adoption matching
- Advanced notifications
- Additional welfare services