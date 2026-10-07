# PawConnect - Requirements

## 1. Purpose

This document defines the functional and non-functional requirements of PawConnect.

The requirements provide a connection between the project idea and its implementation, testing, and deployment.

---

# 2. Functional Requirements

## FR-01: User Registration

The system shall allow users to create an account.

Required information may include:

- Name
- Email
- Phone
- Location
- Role

---

## FR-02: User Authentication

The system shall authenticate users before allowing access to protected features.

Authentication will be handled using Amazon Cognito.

---

## FR-03: Role-Based Access

The system shall provide different permissions based on the user's role.

Roles include:

- User / Adopter
- NGO
- Rescuer
- Volunteer
- Donor
- Administrator

---

## FR-04: Animal Listings

Authorized users shall be able to create animal listings.

Animal information may include:

- Name
- Species
- Breed
- Age
- Gender
- Description
- Location
- Status
- Image

---

## FR-05: Browse Animals

Users shall be able to:

- View animal listings
- Search animals
- Filter animals
- Open individual animal details

---

## FR-06: Report Animal in Need

Users shall be able to report an animal requiring help.

A report may contain:

- Animal type
- Image
- Location
- Condition
- Description
- Urgency
- Contact information

---

## FR-07: Rescue Case Management

Authorized NGO/rescuer users shall be able to:

- View rescue cases
- Review cases
- Respond to cases
- Update case status

Possible statuses:

- Reported
- Under Review
- NGO Assigned
- Rescued
- Under Treatment/Foster
- Adoption Available
- Adopted/Resolved

---

## FR-08: Adoption Application

Users shall be able to submit adoption applications for available animals.

---

## FR-09: Adoption Management

Authorized NGO users shall be able to review adoption applications and update their status.

---

## FR-10: NGO Profiles

The system shall allow NGO information to be stored and displayed.

---

## FR-11: Volunteer Applications

Users shall be able to register as volunteers.

NGOs may manage volunteer opportunities and applications.

---

## FR-12: Image Upload

Authorized users shall be able to upload animal images.

Images shall be stored in Amazon S3.

The database shall store the corresponding image reference or URL.

---

## FR-13: Administration

Administrators shall be able to manage:

- Users
- NGOs
- Animals
- Rescue cases
- Applications
- Reports

---

# 3. Non-Functional Requirements

## NFR-01: Security

The system shall:

- Use HTTPS
- Protect authentication information
- Use role-based authorization
- Validate user input
- Validate uploaded files
- Protect credentials
- Restrict database access

---

## NFR-02: Scalability

The application should support horizontal scaling by running multiple backend instances.

---

## NFR-03: Availability

The cloud architecture should reduce downtime through:

- Load balancing
- Health checks
- Multiple application instances

---

## NFR-04: Performance

The system should provide acceptable response times under normal and increased loads.

Performance testing will measure:

- Response time
- Requests per second
- CPU utilization
- Memory utilization
- Error rate

---

## NFR-05: Maintainability

The project shall use:

- Modular backend code
- Structured API endpoints
- Separate frontend and backend responsibilities
- Documentation
- Version control

---

## NFR-06: Reliability

The system should handle invalid requests and unexpected failures without exposing sensitive information.

---

## NFR-07: Usability

The interface should allow users to easily:

- Browse animals
- Report animals
- Apply for adoption
- Navigate between relevant sections

---

## NFR-08: Deployment

The application shall be deployable to AWS using a repeatable deployment process.

---

# 4. Requirement Traceability

| Requirement | Main Implementation | Testing |
|---|---|---|
| FR-01 | Authentication | Authentication tests |
| FR-02 | Cognito | Login tests |
| FR-03 | RBAC | Authorization tests |
| FR-04 | Animal API + DB | Animal API tests |
| FR-05 | Frontend + Animal API | UI/API tests |
| FR-06 | Rescue API + DB | Rescue tests |
| FR-07 | Rescue management | Workflow tests |
| FR-08 | Adoption API | Adoption tests |
| FR-09 | NGO dashboard | Authorization/workflow tests |
| FR-10 | NGO module | API tests |
| FR-11 | Volunteer module | API tests |
| FR-12 | S3 | File upload tests |
| FR-13 | Admin module | RBAC tests |
| NFR-01 | Security controls | Security tests |
| NFR-02 | ALB + scaling | Performance tests |
| NFR-03 | Cloud infrastructure | Availability tests |
| NFR-04 | CloudWatch + testing | Performance tests |
| NFR-05 | Modular architecture | Code review |
| NFR-08 | CI/CD | Deployment tests |