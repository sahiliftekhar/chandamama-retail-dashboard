# 🛍️ ChandaMama Retail Intelligence Dashboard

<div align="center">

![Django](https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-Reverse%20Proxy-009639?style=for-the-badge&logo=nginx&logoColor=white)

**A production-ready retail ERP & analytics dashboard built for a real clothing business.**

[Features](#-features) • [Tech Stack](#-tech-stack) • [Screenshots](#-screenshots) • [Setup](#-setup) • [API](#-api-endpoints)

</div>

---

## 📌 Overview

ChandaMama is a full-featured retail management system built on top of Django Admin. It powers real-time sales analytics, inventory tracking, multi-product cart billing, and business intelligence for a clothing retail store.

---

## ✨ Features

### 📊 Analytics Dashboard
- **AJAX-powered filtering** — period, section, date range, search — all without page reload
- **4 Period KPI Cards** — Revenue, Profit, Units Sold, Margin with trend badges (↑ +12% vs last week)
- **5 Live KPI Cards** — Today's revenue/profit, year revenue, low stock, dead stock
- **Smart Insights Panel** — Auto-generated business alerts with glowing color-coded cards
- **6 Interactive Charts** — Monthly sales, category distribution, 7-day trend, growth rate, profit margin, aging analysis

### 🛒 Sales Management
- **Single sale form** with product remarks/variant (e.g. `GAMCHA - Bhagwa`)
- **Multi-product cart** — add multiple items in one transaction
- **Payment modes** — Cash, PhonePe, Due (Pay Later)
- **Due sales** — customer name + phone required, tracked separately
- **Product remarks** — optional variant identification shown as `PRODUCT - Remarks`

### 📦 Inventory Intelligence
- **Low stock alerts** with visual progress bars and critical thresholds
- **Dead stock detection** — items with no sale in 90+ days
- **Product aging analysis** — 0-30, 31-60, 61-90, 90+ days buckets
- **At-risk capital** calculation per dead stock item

### 🎨 Premium UI
- Always-dark premium theme with deep navy backgrounds
- Inter + JetBrains Mono fonts
- Colored glow borders per card type (cyan/green/purple/gold/red)
- Count-up number animations on filter change
- Tabbed tables — Top Selling / Low Stock / Dead Stock
- Pulsing dot animations in Smart Insights
- Responsive design (mobile/tablet/desktop)

### 📤 Export & Reporting
- **Excel export** with auto-formatted sheets, colored headers, borders
- Section-wise and date-range filtered exports

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.2.12, Python 3.11 |
| Database | PostgreSQL 15 |
| Frontend | Vanilla JS, Chart.js 4.4, Inter + JetBrains Mono |
| Infrastructure | Docker, Docker Compose, Nginx |
| Auth | Django Admin (custom site) |
| Excel | openpyxl |

---

## 📸 Screenshots

> Add your screenshots here after taking them from the live app

| Dashboard Dark Mode | Smart Insights | Sales Cart |
|---|---|---|
| *(screenshot)* | *(screenshot)* | *(screenshot)* |

---

## 🚀 Setup

### Prerequisites
- Docker & Docker Compose
- Git

### Quick Start

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/MY_EOD.git
cd MY_EOD

# Start all services
docker compose up -d

# Create superuser
docker exec -it django_backend python manage.py createsuperuser

# Visit
http://localhost/admin/
```

### Environment Variables

Create `backend/.env`:
```env
DEBUG=False
SECRET_KEY=your-secret-key
DB_NAME=retail_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=postgres_db
DB_PORT=5432
```

---

## 📡 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/dashboard/` | KPI data with period comparison |
| `GET /api/health/` | System health check |
| `GET /admin/api/product-sizes/` | Sizes for a product |
| `GET /admin/export-excel/` | Download Excel report |
| `POST /admin/store/sale/add-cart/save/` | Save multi-product cart |

### Dashboard API Response
```json
{
  "revenue": 5365.0,
  "profit": 1307.0,
  "units": 33,
  "margin_pct": 24.4,
  "rev_pct": 12.5,
  "profit_pct": 8.3,
  "units_pct": -3.0
}
```

---

## 📁 Project Structure

```
MY_EOD/
├── backend/
│   ├── store/
│   │   ├── models.py        # Sale, Product, Stock, Pricing, Section, Category
│   │   ├── admin.py         # Custom admin site, dashboard, cart, exports
│   │   ├── views.py         # Dashboard API, health check
│   │   ├── urls.py          # API routes
│   │   └── migrations/      # 20 migrations
│   ├── templates/
│   │   └── admin/
│   │       ├── dashboard.html        # Main analytics dashboard
│   │       └── store/sale/
│   │           ├── cart.html         # Multi-product cart
│   │           └── change_list.html  # Sales list with buttons
│   └── config/
│       ├── settings.py
│       └── urls.py
├── docker-compose.yml
└── nginx/
    └── nginx.conf
```

---

## 🧠 Key Technical Decisions

- **Django Admin as base** — leverages built-in auth, permissions, audit logs while adding custom views
- **AJAX without frameworks** — pure `fetch()` + vanilla JS for zero frontend dependencies
- **Split script blocks** — Django template vars in one `<script>`, pure JS in another to avoid template literal conflicts
- **Previous period comparison** — API calculates `rev_pct`, `profit_pct`, `units_pct` by comparing current vs previous equivalent period
- **Product remarks** — optional variant identification stored on `Sale` model, displayed as `PRODUCT - Remarks`

---

## 👨‍💻 Author

Built with ❤️ for a real retail business.

---

## 📄 License

MIT License — feel free to use, modify and distribute.
