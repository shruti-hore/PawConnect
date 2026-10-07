
---

# 8. `SECURITY.md`

```md
# PawConnect - Security Design

## 1. Security Objective

PawConnect must protect:

- User accounts
- Personal information
- Authentication credentials
- Animal information
- Uploaded images
- Database records
- Administrative operations

---

# 2. Authentication

Authentication verifies who the user is.

Amazon Cognito is used for authentication.

Example:

```text
User
 ↓
Login
 ↓
Cognito
 ↓
Identity Verification
 ↓
Authentication Token