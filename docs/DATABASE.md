
---

# 4. `DATABASE.md`

```md
# PawConnect - Database Design

## 1. Database Technology

PawConnect uses PostgreSQL as its relational database.

For cloud deployment, PostgreSQL will be hosted using Amazon RDS.

---

# 2. Main Entities

The primary entities are:

- Users
- Roles
- NGOs
- Animals
- Rescue Cases
- Adoption Applications
- Donations
- Volunteer Applications
- Reports
- Notifications

Only entities required by the implemented features need to be created in the final database.

---

# 3. Users

### Table: users

| Field | Type | Description |
|---|---|---|
| user_id | PK | Unique user ID |
| name | VARCHAR | User name |
| email | VARCHAR | User email |
| phone | VARCHAR | Contact number |
| role_id | FK | User role |
| location | VARCHAR | User location |
| auth_id | VARCHAR | Authentication provider ID |
| created_at | TIMESTAMP | Account creation time |

---

# 4. Roles

### Table: roles

| Field | Type | Description |
|---|---|---|
| role_id | PK | Unique role ID |
| role_name | VARCHAR | Role name |

Possible roles:

- User
- NGO
- Rescuer
- Volunteer
- Donor
- Admin

---

# 5. NGOs

### Table: ngos

| Field | Type | Description |
|---|---|---|
| ngo_id | PK | NGO ID |
| user_id | FK | Associated user |
| name | VARCHAR | NGO name |
| description | TEXT | NGO description |
| location | VARCHAR | NGO location |
| contact | VARCHAR | Contact information |
| verification_status | VARCHAR | Verification state |

---

# 6. Animals

### Table: animals

| Field | Type | Description |
|---|---|---|
| animal_id | PK | Animal ID |
| ngo_id | FK | Associated NGO |
| name | VARCHAR | Animal name |
| species | VARCHAR | Animal type |
| breed | VARCHAR | Breed |
| age | INTEGER | Age |
| gender | VARCHAR | Gender |
| description | TEXT | Description |
| location | VARCHAR | Current location |
| status | VARCHAR | Adoption/rescue status |
| image_url | TEXT | S3 image reference |
| created_at | TIMESTAMP | Creation time |

---

# 7. Rescue Cases

### Table: rescue_cases

| Field | Type | Description |
|---|---|---|
| case_id | PK | Rescue case ID |
| reported_by | FK | Reporting user |
| assigned_ngo | FK | Assigned NGO |
| animal_type | VARCHAR | Animal type |
| condition | TEXT | Animal condition |
| location | VARCHAR | Rescue location |
| description | TEXT | Case description |
| urgency | VARCHAR | Urgency level |
| image_url | TEXT | S3 image reference |
| status | VARCHAR | Case status |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update |

---

# 8. Adoption Applications

### Table: adoption_applications

| Field | Type | Description |
|---|---|---|
| application_id | PK | Application ID |
| animal_id | FK | Animal |
| user_id | FK | Applicant |
| ngo_id | FK | Responsible NGO |
| application_date | TIMESTAMP | Application date |
| status | VARCHAR | Application status |
| message | TEXT | Applicant message |

---

# 9. Donations

### Table: donations

| Field | Type | Description |
|---|---|---|
| donation_id | PK | Donation ID |
| donor_id | FK | Donor |
| case_id | FK | Related case |
| amount | DECIMAL | Donation amount |
| payment_status | VARCHAR | Payment state |
| donated_at | TIMESTAMP | Donation time |

---

# 10. Volunteer Applications

### Table: volunteer_applications

| Field | Type | Description |
|---|---|---|
| volunteer_id | PK | Application ID |
| user_id | FK | Volunteer |
| ngo_id | FK | NGO |
| status | VARCHAR | Application status |
| applied_at | TIMESTAMP | Application date |

---

# 11. Relationships

```text
Roles
  |
  +---- Users
           |
           +---- NGOs
           |
           +---- Rescue Cases
           |
           +---- Adoption Applications
           |
           +---- Donations
           |
           +---- Volunteer Applications

NGOs
  |
  +---- Animals
  |
  +---- Rescue Cases
  |
  +---- Adoption Applications

Animals
  |
  +---- Adoption Applications