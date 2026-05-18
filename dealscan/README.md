# 🏠 DealScan — Real Estate Investment Dashboard

Find undervalued properties with automatic scoring using 100% free data sources.

## Stack
- **Backend**: FastAPI (Python) → http://localhost:8000
- **Frontend**: Next.js + Tailwind CSS → http://localhost:2000
- **Data**: Zillow scraper, Redfin internal API, HUD FMR API, US Census API

## Setup

### 1. Backend
```bash
cd backend
pip install -r requirements.txt

# Add your HUD token to .env
echo "HUD_TOKEN=your_token_here" > .env

uvicorn main:app --reload
# Runs on http://localhost:8000
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:2000
```

## How Scoring Works
Each property gets a **Value Score (0–100)**:
- **45%** — Value Gap: how far below avg price/sqft the listing is
- **35%** — Rent Yield: annual HUD rent estimate / purchase price
- **20%** — Growth Score: Census median home value + population signals

Higher score = better investment opportunity.

## Features
- Search any US city + state
- Filter by max price, min rent yield, min value score
- Sort by value score, price, or rent yield
- Stats bar: avg price, yield, and score across results
- One-click Email Agent button (pre-filled with property details)
- One-click Call Agent button (when phone is available)
- Direct link to Zillow/Redfin listing

## Ports
- Frontend: **2000**
- Backend: **8000**
