# 🐾 Pettit Gateau | High-Performance E-commerce Backend

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-4.2+-092E20.svg?logo=django&logoColor=white)
![Django REST Framework](https://img.shields.io/badge/DRF-API-red.svg?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Robust-336791.svg?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED.svg?logo=docker&logoColor=white)

**An enterprise-grade niche perfumery e-commerce platform, engineered to demonstrate advanced software architecture patterns, asynchronous payment integrations, and strict data integrity.**

While this project features a fully functional and responsive Vanilla JS frontend, its core purpose is to showcase robust **Back-end Engineering**. It tackles real-world e-commerce challenges such as cart mathematics, external API resilience, and transactional security.

---

## 📸 System Walkthrough

*(Note: Replace the placeholder links below with actual GIFs or screenshots of your project)*

| Storefront & Cart | Checkout & Payment Flow | Customized administration panel and inventory |
| :---: | :---: | :---: |
| <img src="docs/applying_coupon_and_zip_code.gif" width="250" alt="Applying Coupon and Zip Code"/> | <img src="docs/finalizing_order.gif" width="250" alt="Mercado Pago Integration"/> | <img src="docs/administration_panels_and_changing_and_adding_tracking_codes.gif" width="250" alt="Administration Panels"/> |
| *Async Cart updates (Fetch API), real-time freight simulation, and coupon validation.* | *Anti-fraud validations and direct Mercado Pago Webhook integration.* | *Custom UI bypassing standard Django Admin for Logistics and Marketing management.* |

---

## 🧠 Core Architecture & Engineering Decisions

Unlike basic CRUD applications, **Pettit Gateau** is built to handle edge cases and maintain business logic integrity:

### 🛡️ Transactional Integrity & Webhooks
* **Asynchronous Inventory Management:** Inventory deductions are triggered *only* via secure webhooks upon Mercado Pago's payment approval. This prevents phantom out-of-stock scenarios caused by abandoned checkouts (e.g., unpaid PIX or Boletos).
* **Float Math Protection:** Discounted orders are dynamically grouped into a single transactional payload before being sent to the payment gateway to completely eliminate API crashes caused by floating-point rounding errors or negative item values.

### 🚚 Resilient Logistics & Anti-Fraud
* **Intelligent Freight Mock & ViaCEP Validation:** Replaced the notoriously unstable public postal API with a resilient local mock service that calculates shipping based on geographic rules (originating from Laguna/SC). Integrated the **ViaCEP API** to instantly validate zip codes and block dummy inputs (e.g., `00000000`).
* **Address Spoofing Prevention:** The checkout view actively cross-references the zip code calculated in the cart against the final selected delivery address, hard-blocking the transaction if discrepancies are found.

### 🏗️ Advanced Data Modeling
* **Abstract Data Governance:** All entities inherit from a universal `BaseModel` providing automated UUIDs (preventing enumeration attacks), audit timestamps (`created_at`/`updated_at`), and `is_active` flags for safe soft-deletions.
* **Decoupled SKU Architecture:** Logical separation between Product (Identity) and SKU (Logistics/Pricing), allowing independent inventory tracking across different volumes with historical price snapshotting on `OrderItems`.

---

## 🗺️ Entity-Relationship Diagram (ERD)

The database schema is heavily normalized, built on PostgreSQL, and designed for scalability.

```mermaid
erDiagram
    CUSTOMER {
        UUID id PK
        string email UK
        string first_name
        string last_name
        string tax_id UK
    }
    ADDRESS {
        UUID id PK
        boolean is_default
        string zip_code
        string city
    }
    PRODUCT {
        UUID id PK
        string name
        string slug UK
    }
    SKU {
        UUID id PK
        string sku_code UK
        int volume_ml
        decimal price
        int stock_quantity
    }
    COUPON {
        UUID id PK
        string code UK
        decimal discount_percentage
        decimal discount_fixed
    }
    ORDER {
        UUID id PK
        string status
        decimal total_price
        string tracking_code
    }
    ORDERITEM {
        UUID id PK
        decimal price
        int quantity
    }
    CART {
        UUID id PK
        string session_key
    }
    CARTITEM {
        UUID id PK
        int quantity
    }

    %% Relationships
    CUSTOMER ||--o{ ADDRESS : "has"
    CUSTOMER ||--o{ ORDER : "places"
    PRODUCT ||--o{ SKU : "contains"
    SKU ||--o{ CARTITEM : "added to"
    SKU ||--o{ ORDERITEM : "purchased as"
    CART ||--o{ CARTITEM : "holds"
    ORDER ||--o{ ORDERITEM : "includes"
    ORDER }|--|| ADDRESS : "delivered to"
    ORDER }|--o| COUPON : "applies"
```

## ⚙️ Prerequisites
To run this project locally, ensure you have the following installed:

* Docker and Docker Compose
* Python 3.11+
* Git
* Ngrok (For testing local webhooks)

## 🚀 Installation & Setup
**1. Clone the repository:**
```bash
git clone [https://github.com/BrendonCordova/pettit-gateau.git](https://github.com/BrendonCordova/pettit-gateau.git)
cd pettit-gateau
```

**2. Configure Environment Variables:**
Create a `.env` file in the root directory based on `.env.example`:
```env
SECRET_KEY=your_django_secret_key
DEBUG=True
POSTGRES_PASSWORD=your_database_password
MP_ACCESS_TOKEN=your_mercado_pago_token
WEBHOOK_BASE_URL=[https://your-ngrok-url.ngrok-free.app](https://your-ngrok-url.ngrok-free.app)
EMAIL_HOST_USER=your_smtp_email
EMAIL_HOST_PASSWORD=your_app_password
```

**3. Boot the Database (Docker):**
```bash
docker-compose up -d db
```

**4. Set up the Virtual Environment & Dependencies:**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**5. Apply Migrations & Create Superuser:**
```bash
python manage.py migrate
python manage.py createsuperuser
```

**6. Start the Local Server:**
```bash
python manage.py runserver
```

> **Note on Webhooks:** To fully test the Mercado Pago checkout flow locally, start an Ngrok tunnel (`ngrok http 8000`), copy the HTTPS URL, update the `WEBHOOK_BASE_URL` in your `.env` file, and restart the Django server.

## 🧪 Testing
The application includes comprehensive test suites focusing on core logic, user permissions, API endpoints, and webhook mocking.
```bash
python manage.py test
```

## 🔄 Git Workflow
This project utilizes the **GitHub Flow** methodology:
* `main` branch acts as the production-ready source of truth.
* Features and bug fixes are developed on ephemeral branches (`feat/*`, `fix/*`, `docs/*`).
* Strict enforcement of atomic commits and Pull Requests for continuous integration.

---
*Architected and developed by **Brendon Gomes de Cordova** as a demonstration of production-ready Backend Engineering.*