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
- Deployment: AWS Elastic Beanstalk
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