# Technical Specification Document



## ۱. API Endpoints - مدیریت کاربران

### POST /api/auth/register/

```python
#Request

{
 "email": "user@example.com",
 "phone": "09123456789",
 "password": "secure_password",
 "user_type": "owner"
}

# Response (201 Created)

{
 "id": 1,
 "email": "user@example.com",
 "phone": "09123456789",
 "user_type": "owner",
 "is_verified": false,
 "auth_token": "xyz123"
}```
```

### POST /api/auth/login/

```python
# Request
{
    "email": "user@example.com",
    "password": "secure_password"
}

# Response (200 OK)
{
    "id": 1,
    "email": "user@example.com",
    "user_type": "owner",
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "def456...",
    "complexes": [1, 2, 3]
}
```

## ۲. API Endpoints - مدیریت مجتمع

### POST /api/complexes/

```python
# Request
{
    "name": "برج مروارید",
    "address": "تهران، منطقه ۱",
    "type": "residential",
    "total_buildings": 2,
    "total_units": 100,
    "board_members": [1, 2, 3]
}

# Response (201 Created)
{
    "id": 1,
    "name": "برج مروارید",
    "code": "BRJ-001",
    "created_at": "2024-01-20T10:30:00Z"
}
```

## ۳. Database Schema

### Table: users

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(15) UNIQUE,
    password VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    user_type VARCHAR(20) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Table: complexes

```sql
CREATE TABLE complexes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    address TEXT NOT NULL,
    type VARCHAR(20) NOT NULL,
    total_buildings INTEGER DEFAULT 1,
    total_units INTEGER NOT NULL,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Table: units

```sql
CREATE TABLE units (
    id SERIAL PRIMARY KEY,
    complex_id INTEGER REFERENCES complexes(id) ON DELETE CASCADE,
    building_number VARCHAR(10) NOT NULL,
    unit_number VARCHAR(20) NOT NULL,
    floor INTEGER NOT NULL,
    area DECIMAL(10,2),
    owner_id INTEGER REFERENCES users(id),
    current_resident_id INTEGER REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
