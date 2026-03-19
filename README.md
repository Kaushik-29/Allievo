# Allievo — AI-Powered Parametric Income Insurance for Food Delivery Partners

> **Guidewire DEVTrails 2026 | Phase 1 Submission**
> Persona: Food Delivery Partners (Zomato / Swiggy)

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Our Solution](#2-our-solution)
3. [Persona & User Scenarios](#3-persona--user-scenarios)
4. [Application Workflow](#4-application-workflow)
5. [Weekly Premium Model](#5-weekly-premium-model)
6. [Parametric Triggers](#6-parametric-triggers)
7. [AI/ML Integration Plan](#7-aiml-integration-plan)
8. [Platform Choice — Web App](#8-platform-choice--web-app)
9. [Tech Stack](#9-tech-stack)
10. [Development Plan](#10-development-plan)

---

## 1. Problem Statement

India's food delivery partners — working for Zomato and Swiggy — earn between ₹15,000 and ₹25,000 per month, almost entirely through daily deliveries. Their income is directly tied to hours on the road. When external disruptions hit, they cannot work — and they earn nothing.

**Key disruptions affecting food delivery workers:**
- Heavy rainfall and flooding (halts outdoor work, roads become impassable)
- Extreme heat advisories (platforms suspend deliveries above certain temperatures)
- Dense pollution / AQI emergencies (government restrictions on outdoor activity)
- Curfews, bandhs, or sudden zone closures (inability to access pickup/drop areas)
- Platform-side outages during peak hours (app downtime blocking order acceptance)

Currently, gig workers have zero income protection against these events. They bear 100% of the financial loss. Allievo changes that.

---

## 2. Our Solution

**Allievo** is an AI-enabled parametric income insurance platform built exclusively for food delivery partners on Zomato and Swiggy.

**How it works — in one sentence:** When a verified external disruption crosses a defined threshold in a worker's delivery zone, Allievo automatically triggers a claim and deposits income replacement directly into the worker's UPI account — no forms, no wait, no friction.

**Key principles:**
- **Parametric:** Payouts are triggered by objective, verifiable external data (weather, AQI, curfew notices) — not by the worker filing a claim
- **Weekly pricing:** Premiums are structured and charged on a weekly basis to match the gig worker's earnings cycle
- **Income-only coverage:** We cover lost wages during disruption windows only. No vehicle, health, accident, or life coverage of any kind
- **Zero-touch claims:** Workers should never have to "claim" — the system detects, validates, and pays automatically

---

## 3. Persona & User Scenarios

### Primary Persona: Ravi, Food Delivery Partner

- **Age:** 26
- **Platform:** Zomato (also does Swiggy surge hours)
- **City:** Hyderabad, Kondapur zone
- **Earnings:** ~₹700–900/day on normal days, ₹1,200+ on weekends/festivals
- **Working hours:** 10am–2pm and 6pm–11pm (peak slots)
- **Device:** Android smartphone (mid-range)
- **Financial profile:** No credit card, UPI-enabled (PhonePe/GPay), lives paycheck to paycheck
- **Pain point:** Lost 4 days of income last monsoon season due to zone flooding. No insurance, no savings buffer.

---

### Scenario 1: Monsoon Flood Trigger

Ravi is active in Kondapur zone on a Tuesday evening. The IMD weather API reports rainfall exceeding 65mm/hour in Hyderabad. Zomato suspends deliveries in the affected zones. Allievo detects the trigger, validates Ravi's active policy and his historical zone activity, and initiates a payout covering his estimated 4-hour income loss (₹280) directly to his UPI. He receives it within 10 minutes — before the rain even stops.

### Scenario 2: AQI Emergency

Delhi in November. AQI crosses 400 (Severe) for 2 consecutive days. The government issues a Grade-4 GRAP restriction limiting outdoor work. Allievo detects the AQI threshold breach via the CPCB API, verifies it against the worker's registered zone, and auto-initiates a daily income replacement payout for all active policyholders in the affected Delhi zones.

### Scenario 3: Local Bandh / Curfew

A sudden Section 144 curfew is imposed in a city zone. Allievo's social disruption monitor (fed by government notification APIs and verified news sources) detects the event. It cross-validates with order drop data from the platform API mock. Workers in the affected zone with active policies receive automatic payout notifications within 30 minutes of the disruption being confirmed.

### Scenario 4: Fraud Attempt

A worker registers a claim for a zone they were not active in during the disruption. Allievo's fraud detection engine cross-checks GPS activity logs, order history timestamps, and zone assignment history. The claim is flagged and held for review. The legitimate workers in the same zone are paid without interruption.

---

## 4. Application Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                     WORKER ONBOARDING                        │
│  Register → Link Delivery Platform → Risk Profile → Policy  │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   WEEKLY POLICY MANAGEMENT                   │
│  AI calculates weekly premium → Worker opts in → Payment     │
│  deducted via UPI or wallet → Policy active for 7 days       │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                  REAL-TIME TRIGGER MONITORING                 │
│  Weather API · AQI API · Govt Alerts · Platform API (mock)   │
│  Continuous polling every 15 minutes across all active zones │
└────────────────────────────┬────────────────────────────────┘
                             │
                        Threshold
                        breached?
                        /       \
                      YES        NO
                      │          │
                      ▼          └──────── Continue monitoring
┌─────────────────────────────────────────────────────────────┐
│                  FRAUD DETECTION & VALIDATION                 │
│  Zone match · GPS activity · Order history · Dupe check      │
└────────────────────────────┬────────────────────────────────┘
                             │
                        Validates?
                        /       \
                      YES        NO
                      │          │
                      ▼          └──────── Flag for review
┌─────────────────────────────────────────────────────────────┐
│                    AUTOMATIC PAYOUT                          │
│  Income loss calculated → UPI transfer initiated → Worker    │
│  notified via SMS + app push notification                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Weekly Premium Model

### Philosophy

Food delivery workers operate on a week-to-week earnings cycle, typically receiving platform payouts every Monday or Tuesday. Our premium is designed to feel like a small, predictable deduction — not a lump annual payment.

Allievo uses a **two-layer hybrid pricing model**:
- **Layer 1 — Static Base Formula:** A simple, stable foundation computed at onboarding using historical zone data
- **Layer 2 — Dynamic Risk Score:** A live AI-computed score that adjusts the premium weekly based on real-world conditions

Both layers work together. The static layer ensures the premium is never shockingly different week to week. The dynamic layer ensures it accurately reflects current risk.

---

### Layer 1: Static Base Premium (Computed at Onboarding)

Calculated once when the worker signs up, and refreshed every 4 weeks.

```
Static Base Premium = Base Rate × Zone Risk Multiplier × Coverage Tier × Loyalty Adjustment

Where:
  Base Rate              = ₹40
  Zone Risk Multiplier   = 0.8 – 1.6 (historical disruption frequency of zone, updated monthly)
  Coverage Tier          = 0.8× (Basic) | 1.0× (Standard) | 1.4× (Premium)
  Loyalty Adjustment     = 1.0 → 0.95 (after 4 weeks) → 0.90 (after 12 weeks)
```

**Example zone multipliers:**
| Zone                     | Multiplier | Reason                          |
|--------------------------|------------|---------------------------------|
| Kondapur, Hyderabad      | 1.1        | Moderate flood history          |
| Koramangala, Bangalore   | 1.3        | High waterlogging frequency     |
| Lajpat Nagar, Delhi      | 1.4        | High AQI + flood risk           |
| Viman Nagar, Pune        | 0.9        | Low historical disruption       |

This gives the worker a **predictable base premium** they can plan around — say ₹45/week at Standard tier in Kondapur.

---

### Layer 2: Dynamic Risk Score (Computed Every Week via AI)

Every Sunday night, the system recomputes a **Risk Score (0–1)** for each zone using live and recent data. This score adjusts the static base premium for the coming week.

```
Risk Score =
  0.30 × Historical Risk   (disruption days in last 365 days / 365)
  0.25 × Weather Risk      (rain probability × severity factor)
  0.15 × Pollution Risk    (AQI / 500)
  0.15 × Traffic Risk      (1 − avg speed / ideal speed)
  0.15 × Live Event Risk   (0–1 based on confirmed curfews / bandhs)
```

---

### Final Weekly Premium Formula (Combined)

```
Weekly Premium = Static Base Premium × (1 + Risk Score × 0.75) × Loyalty Adjustment

Cap: Maximum weekly premium = ₹90 (Premium tier, highest risk zone)
Floor: Minimum weekly premium = ₹25 (Basic tier, lowest risk zone, full loyalty)
```

The **0.75 multiplier** caps the dynamic risk amplification so premiums never spike unaffordably even during high-risk weeks.

**Example — same worker, two different weeks:**

| Week        | Static Base | Risk Score | Dynamic Factor | Final Premium |
|-------------|-------------|------------|----------------|---------------|
| Dry January | ₹45         | 0.18       | × 1.135        | ₹51           |
| Monsoon July| ₹45         | 0.74       | × 1.555        | ₹70           |

The worker sees a higher premium in July — but it was communicated the Sunday before, giving them a full week to decide whether to renew or downgrade their tier.

---

### Coverage Tiers

| Tier     | Weekly Premium Range | Max Weekly Payout | Coverage Hours/Day |
|----------|---------------------|-------------------|--------------------|
| Basic    | ₹25 – ₹55           | ₹400              | Up to 4 hours      |
| Standard | ₹32 – ₹72           | ₹700              | Up to 6 hours      |
| Premium  | ₹45 – ₹90           | ₹1,000            | Up to 8 hours      |

### Waiting Period & Eligibility Rules

To prevent adverse selection (workers signing up only when a storm is already forecast):

```
Rule 1 — Waiting Period:
  A policy must be active and paid for >= 2 consecutive weeks
  before the worker is eligible to receive any payout.

Rule 2 — Forecast Lockout:
  Any disruption that was publicly warned or officially forecast
  BEFORE the worker's policy activation date is excluded from
  coverage for that policy term.

Rule 3 — Zone Lock:
  Claims are only valid for the worker's registered active zones.
  Zone changes take effect from the following week's policy cycle.
```

### Payout Calculation During a Disruption

```
Payout = Daily Average Earnings x (Disruption Hours / Total Working Hours) x Coverage Factor

Example:
  Daily avg earnings    = Rs.800
  Disruption duration   = 3 hours
  Typical working hours = 8 hours
  Coverage factor       = 1.0 (Standard tier)

  Payout = Rs.800 x (3/8) x 1.0 = Rs.300
```

Payouts are capped at the tier's weekly maximum. The weekly cap resets every Monday.

---

## 6. Parametric Triggers

All triggers are objective, third-party verifiable, and require no manual claim initiation.

### Trigger 1: Heavy Rainfall / Flooding

| Parameter         | Detail                                                  |
|-------------------|---------------------------------------------------------|
| Data Source       | IMD Open API / OpenWeatherMap                           |
| Trigger Condition | Rainfall ≥ 65mm/hour OR active flood alert for zone     |
| Validation        | Cross-check with platform order cancellation spike      |
| Payout Duration   | Per hour of platform suspension in the affected zone    |
| Mock Available    | Yes — OpenWeatherMap free tier                          |

### Trigger 2: Extreme Heat Advisory

| Parameter         | Detail                                                  |
|-------------------|---------------------------------------------------------|
| Data Source       | IMD API / OpenWeatherMap                                |
| Trigger Condition | Temperature ≥ 44°C AND active heat advisory issued      |
| Validation        | Check if platform has issued heat suspension notice     |
| Payout Duration   | Per 2-hour block during advisory window                 |
| Mock Available    | Yes                                                     |

### Trigger 3: Severe AQI / Pollution Emergency

| Parameter         | Detail                                                  |
|-------------------|---------------------------------------------------------|
| Data Source       | CPCB API (free) / AQI.in                                |
| Trigger Condition | AQI > 400 (Severe) sustained for ≥ 4 hours in zone     |
| Validation        | GRAP restriction level confirmed via govt notification  |
| Payout Duration   | Full day payout per qualifying day                      |
| Mock Available    | Yes — CPCB API has free public data                     |

### Trigger 4: Curfew / Bandh / Zone Closure

| Parameter         | Detail                                                  |
|-------------------|---------------------------------------------------------|
| Data Source       | Government notification feed / verified news API        |
| Trigger Condition | Section 144 / state bandh confirmed in worker's zone    |
| Validation        | Order data drop > 80% in zone within 1 hour of event    |
| Payout Duration   | Full duration of restriction as reported officially     |
| Mock Available    | Yes — simulated event injection for demo                |

### Trigger 5: Platform App Outage (Peak Hours)

| Parameter         | Detail                                                  |
|-------------------|---------------------------------------------------------|
| Data Source       | Downdetector API / platform status mock                 |
| Trigger Condition | Platform outage lasting ≥ 45 minutes during peak hours  |
| Validation        | Confirmed by at least 2 independent monitoring sources  |
| Payout Duration   | Per hour of confirmed outage during 12pm–2pm / 7pm–10pm |
| Mock Available    | Yes — mock platform status endpoint                     |

---

## 7. AI/ML Integration Plan

### 7.1 Dynamic Premium Calculation (ML Model)

**Goal:** Personalize weekly premiums per worker based on hyper-local risk, not just a flat rate.

**Approach:**
- **Model type:** Gradient Boosted Trees (XGBoost / LightGBM) — interpretable, fast to train, works well on tabular data
- **Input features:**
  - Worker's registered zone(s) and historical activity zones
  - Zone-level historical disruption frequency (last 3 years)
  - Seasonal risk factor (monsoon months weighted higher)
  - Worker's claim history (frequency, amount)
  - Platform activity consistency (days active per week)
  - City-level risk index
- **Output:** Recommended weekly premium and coverage tier
- **Training data:** Simulated / synthetic dataset for Phase 1; will integrate real IMD/CPCB historical data in Phase 2
- **Retraining:** Weekly batch retraining using new disruption event data

### 7.2 Fraud Detection (Anomaly Detection)

**Goal:** Catch fraudulent or invalid claims before payout is triggered.

**Approach:**
- **Model type:** Isolation Forest + rule-based validation layer
- **Signals used:**
  - GPS coordinates at time of disruption vs. registered zone
  - Order acceptance/rejection history during the disruption window
  - Claim frequency relative to disruption frequency in the zone
  - Comparison of claimed disruption hours vs. platform downtime logs
  - Pattern detection: multiple claims from same device/IP, abnormal claim clustering
- **Output:** Fraud score (0–1). Claims above 0.7 are held for manual review; below 0.3 auto-approve

### 7.3 Disruption Severity Scoring

**Goal:** Estimate income loss more accurately based on disruption severity, not just binary on/off.

**Approach:**
- Rule-based model for Phase 1 (severity tiers: Low / Moderate / High / Severe)
- Phase 2: Regression model to predict % income loss given disruption parameters
- Example: A 70mm/hr rainfall at 7pm (peak dinner hour) in Koramangala scores higher than the same rainfall at 3am

### 7.4 Risk Zone Profiling

**Goal:** Continuously update zone risk scores as new disruption data arrives.

**Approach:**
- Sliding window aggregation of disruption events per zone
- Zone scores refreshed weekly
- New zones scored using nearest-neighbor interpolation from known zone scores

---

## 8. Platform Choice — Web App

We have chosen to build Allievo as a **web application** (React frontend + FastAPI backend) for the following reasons:

1. **Accessibility:** Workers access it via a mobile browser — no app install required, reducing friction for onboarding
2. **Speed of development:** A responsive web app can be built and demoed faster in a 6-week hackathon than a native mobile app
3. **Admin panel:** The insurer/admin dashboard is naturally better suited to a browser interface
4. **Demo-ability:** Easier to share live links with judges and record demo videos
5. **Progressive upgrade path:** A PWA (Progressive Web App) wrapper can be added in Phase 3 to give a near-native mobile experience

The UI will be fully responsive and optimized for mobile screens (320px–480px), since most workers will access it on their smartphones.

---

## 9. Tech Stack

### Frontend
| Layer        | Technology          | Reason                                        |
|--------------|---------------------|-----------------------------------------------|
| Framework    | React 18            | Component-based, fast, large ecosystem        |
| Styling      | Tailwind CSS        | Rapid UI development, responsive out of box   |
| State        | Zustand             | Lightweight, simpler than Redux               |
| API calls    | Axios + React Query | Caching, loading states, error handling       |
| Charts       | Recharts            | Simple, React-native charting for dashboard   |

### Backend
| Layer        | Technology          | Reason                                        |
|--------------|---------------------|-----------------------------------------------|
| Framework    | FastAPI (Python)    | Fast, async, auto-generates API docs          |
| Auth         | JWT + OAuth2        | Secure, stateless authentication              |
| Task queue   | Celery + Redis      | Background jobs for trigger monitoring        |
| Scheduler    | APScheduler         | Periodic polling of weather/AQI APIs          |

### AI/ML
| Layer        | Technology          | Reason                                        |
|--------------|---------------------|-----------------------------------------------|
| Models       | scikit-learn / XGBoost | Standard, well-documented ML libraries    |
| Data         | Pandas / NumPy      | Data processing and feature engineering       |
| Serving      | FastAPI endpoints   | Models served inline with the backend         |

### Database
| Layer        | Technology          | Reason                                        |
|--------------|---------------------|-----------------------------------------------|
| Primary DB   | PostgreSQL          | Relational, reliable, good for financial data |
| Cache        | Redis               | Session storage, API response caching         |
| ORM          | SQLAlchemy          | Clean DB access layer                         |

### External Integrations (APIs)
| Service      | API / Source        | Usage                                         |
|--------------|---------------------|-----------------------------------------------|
| Weather      | OpenWeatherMap (free tier) | Rain, temp, heat advisory triggers     |
| AQI          | CPCB API (free)     | Pollution emergency triggers                  |
| Payment      | Razorpay test mode  | Simulated UPI payout processing               |
| Platform     | Mock REST API       | Simulated Zomato/Swiggy order data            |
| Alerts       | Mock govt feed      | Curfew/bandh event simulation                 |

### Infrastructure
| Layer        | Technology          | Reason                                        |
|--------------|---------------------|-----------------------------------------------|
| Containerization | Docker + Docker Compose | Consistent dev/prod environment       |
| Hosting      | Render / Railway (free tier) | Easy deployment for demo purposes    |
| Version control | GitHub           | Single repo across all 3 phases               |

---

## 10. Development Plan

### Phase 1 (Mar 4–20): Ideation & Foundation ✅
- [x] Define persona, scenarios, and workflow
- [x] Design weekly premium model and parametric triggers
- [x] Plan AI/ML architecture
- [x] Finalize tech stack
- [ ] Set up GitHub repository with project scaffolding
- [ ] Initialize React frontend + FastAPI backend boilerplate
- [ ] Set up PostgreSQL schema (workers, policies, claims, triggers)
- [ ] Record 2-minute strategy video

### Phase 2 (Mar 21–Apr 4): Automation & Protection
- [ ] Worker registration and onboarding flow
- [ ] Policy creation with dynamic weekly premium calculation (ML model v1)
- [ ] Implement 5 parametric trigger monitors (weather, AQI, curfew, heat, outage)
- [ ] Basic fraud detection layer (rule-based + Isolation Forest)
- [ ] Zero-touch claim initiation pipeline
- [ ] Mock payout integration (Razorpay sandbox)
- [ ] Record 2-minute demo video

### Phase 3 (Apr 5–17): Scale & Optimise
- [ ] Advanced fraud detection (GPS spoofing, historical pattern analysis)
- [ ] Worker dashboard (earnings protected, active coverage, payout history)
- [ ] Admin/insurer dashboard (loss ratios, predictive disruption analytics)
- [ ] PWA wrapper for mobile-native experience
- [ ] Full end-to-end demo with simulated disruption event
- [ ] Final pitch deck (PDF)
- [ ] Record 5-minute walkthrough demo video

---

## Team

| Role                    | Responsibilities                                    |
|-------------------------|-----------------------------------------------------|
| Frontend Developer      | React UI, worker dashboard, onboarding flow         |
| Backend Developer       | FastAPI, database, trigger monitoring pipelines      |
| ML Engineer             | Premium model, fraud detection, risk scoring         |
| Full-Stack / DevOps     | Integration, deployment, demo setup                  |

---

## Exclusions (Hard Rules)

This platform explicitly does **NOT** cover:
- Health or medical expenses
- Life insurance
- Road accident or personal injury
- Vehicle repair or maintenance costs

Coverage is **income loss only**, triggered by verifiable external disruptions.

---

*Allievo — Because every delivery partner deserves a safety net.*
