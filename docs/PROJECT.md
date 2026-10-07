# PawConnect - Project Definition

## 1. Project Overview

PawConnect is a secure, cloud-deployed animal welfare and pet adoption platform that connects people who need help with animals to NGOs, rescuers, volunteers, donors, and adopters.

The platform provides a centralized system where users can:

- Discover animals available for adoption
- Report animals in need
- View animal and rescue cases
- Apply for adoption
- Find NGOs and rescuers
- Register as volunteers
- Support animal welfare activities
- Manage animal welfare cases through role-based access

The project demonstrates the use of cloud computing concepts such as cloud deployment, managed databases, object storage, authentication, load balancing, monitoring, scalability, security, and CI/CD.

---

## 2. Problem Statement

Animal welfare information is often distributed across social media, messaging platforms, individual NGO websites, and informal communication channels.

This can make it difficult to:

- Find animals available for adoption
- Report animals that need immediate help
- Connect people with NGOs or rescuers
- Track rescue cases
- Manage adoption requests
- Coordinate volunteers
- Maintain organized animal records

PawConnect aims to provide a centralized platform for these activities.

---

## 3. Proposed Solution

PawConnect provides a web-based platform where different stakeholders can interact according to their roles.

The basic flow is:

User identifies an animal or needs help
        ↓
User submits or searches information
        ↓
Cloud backend processes the request
        ↓
Database stores structured information
        ↓
NGO / Rescuer / Admin manages the case
        ↓
Case or adoption status is updated

---

## 4. Objectives

The main objectives are:

1. Create a centralized animal welfare platform.
2. Provide secure user authentication.
3. Implement role-based access control.
4. Allow users to report animals in need.
5. Provide animal adoption listings.
6. Allow users to submit adoption applications.
7. Provide NGO and rescuer information.
8. Store animal images using cloud object storage.
9. Deploy the application using cloud infrastructure.
10. Demonstrate cloud scalability and load balancing.
11. Monitor application performance and resource utilization.
12. Implement CI/CD using GitHub Actions.

---

## 5. Target Users

### General User / Adopter

Can:

- Register and log in
- Browse animals
- Search and filter animals
- View animal details
- Submit adoption applications
- Report animals in need
- View rescue cases

### NGO

Can:

- Manage NGO profile
- Add animals
- Update animal information
- Review rescue cases
- Manage adoption applications
- Update case statuses

### Rescuer

Can:

- View reported rescue cases
- Respond to cases
- Update rescue progress
- Coordinate with NGOs

### Volunteer

Can:

- Register as a volunteer
- View volunteer opportunities
- Apply for opportunities
- View assigned tasks

### Donor

Can:

- View welfare cases
- Support eligible cases
- View donation records

### Administrator

Can:

- Manage users
- Manage NGOs
- Manage animals
- Review reports
- Manage platform data
- Monitor system activity

---

## 6. Core Features

### 6.1 Authentication

Users can securely authenticate before accessing protected features.

### 6.2 Pet Adoption

Users can:

- Browse animals
- View animal details
- Search and filter listings
- Apply for adoption

### 6.3 Report an Animal in Need

Users can submit:

- Animal image
- Animal type
- Location
- Condition
- Description
- Urgency
- Contact information

The case can then be reviewed and managed by authorized NGO/rescuer users.

### 6.4 NGO Profiles

NGOs can maintain profiles containing:

- Organization name
- Description
- Location
- Contact details
- Verification status

### 6.5 Volunteer Management

Users can register as volunteers and NGOs can manage volunteer opportunities.

### 6.6 Admin Dashboard

Administrators can manage platform-level data and users.

---

## 7. Cloud Computing Scope

The project demonstrates:

- Public cloud deployment
- PaaS
- Managed database services
- Object storage
- Cloud authentication
- Load balancing
- Horizontal scaling
- Monitoring
- Resource utilization
- Security
- CI/CD

The project is not intended to be a true scientific High Performance Computing system. HPC-related course concepts are demonstrated through cloud performance, scaling, load balancing, and resource utilization.

---

## 8. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python Flask |
| API | REST API |
| Database | PostgreSQL |
| Cloud Database | Amazon RDS |
| Image Storage | Amazon S3 |
| Authentication | Amazon Cognito |
| Deployment | AWS Elastic Beanstalk |
| Load Balancing | AWS Application Load Balancer |
| Monitoring | Amazon CloudWatch |
| Version Control | Git + GitHub |
| CI/CD | GitHub Actions |

---

## 9. Project Scope

### Included

- User authentication
- Role-based access
- Animal listings
- Rescue reporting
- Adoption applications
- NGO profiles
- Cloud database
- Cloud image storage
- Cloud deployment
- Monitoring
- Load balancing
- CI/CD

### Optional

- Lost and found
- Volunteer opportunities
- Donations
- Notifications
- Events
- Google SSO

### Future Scope

- AI-based animal-adopter matching
- Automated NGO matching
- Mobile application
- Real-time chat
- Push notifications
- GPS-based rescue coordination
- Computer vision for animal identification
- Advanced analytics

---

## 10. Success Criteria

The project will be considered successful when:

- Users can authenticate securely.
- Users can browse animals.
- Users can submit rescue reports.
- NGOs can manage relevant cases.
- Adoption applications can be submitted and managed.
- Application data is stored in PostgreSQL.
- Images are stored in S3.
- The application is deployed on AWS.
- Security controls are implemented.
- Application performance can be monitored.
- CI/CD deployment works through GitHub Actions.
- The application can demonstrate horizontal scaling and load balancing.