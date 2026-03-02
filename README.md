# Bitespeed Backend Task – Identity Reconciliation

## 🚀 Overview

This project implements the `/identify` endpoint required in the Bitespeed Backend Task.

The service consolidates customer identities based on shared email or phone numbers.  
It maintains a primary-secondary contact relationship as described in the task specification.

---

## 🛠 Tech Stack

- FastAPI
- MySQL
- SQLAlchemy ORM
- Uvicorn

---

## 🧠 Logic Summary

- If no matching contact exists → Create primary contact
- If one field matches but new info is present → Create secondary contact
- If multiple primary contacts are linked → Oldest becomes primary
- All others become secondary

---

## 📦 How to Run Locally

### 1️⃣ Install Dependencies

### 2️⃣ Configure Database

Create MySQL database:


Update `database.py` with your MySQL credentials.

### 3️⃣ Start Server


---

## 🔎 API Endpoint

### POST `/identify`

Example request:

```json
{
  "email": "test@example.com",
  "phoneNumber": "123456"
}

{
  "contact": {
    "primaryContactId": 1,
    "emails": ["test@example.com"],
    "phoneNumbers": ["123456"],
    "secondaryContactIds": []
  }
}