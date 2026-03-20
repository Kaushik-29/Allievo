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
8. [Adversarial Defense & Anti-Spoofing Strategy](#8-adversarial-defense--anti-spoofing-strategy)
9. [Platform Choice — Web App](#9-platform-choice--web-app)
10. [Tech Stack](#10-tech-stack)
11. [Development Plan](#11-development-plan)

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

## 8. Adversarial Defense & Anti-Spoofing Strategy

Allievo's zero-touch payout model is only trustworthy if the system is robust against deliberate manipulation. Because payouts are automatic, a naive implementation would be vulnerable to location spoofing, synthetic claim rings, and opportunistic fraud. This section describes how Allievo defends against adversarial actors at three levels: individual differentiation, coordinated ring detection, and fair treatment of legitimate edge cases.

---

### 8.1 Differentiating a Genuine Stranded Worker from a GPS Spoofer

The core challenge is that a bad actor and a genuinely stranded worker will look identical on a single dimension — both register a GPS coordinate inside the disrupted zone. Allievo defeats this by requiring **multi-signal coherence**: a genuine worker's full behavioral fingerprint must be consistent with their location claim, not just their GPS coordinate.

#### Signal Layer 1 — Behavioral Trajectory Consistency

GPS spoofing tools inject static or scripted coordinates. They cannot replicate the natural, physics-consistent movement of a real delivery worker. Allievo analyzes GPS ping history for the 90 minutes preceding a disruption event and applies the following checks:

```
Trajectory Checks:
  ✓ Speed continuity:   No teleportation between pings (Δdistance / Δtime within physical limits)
  ✓ Micro-drift:        Real devices show ±3–8m natural GPS drift; perfect static coordinates are suspect
  ✓ Path plausibility:  Movement path matches known road geometry (validated against OSM road network)
  ✓ Arrival vector:     Worker was moving toward the zone, not suddenly "in" it at trigger time
```

A spoofed coordinate typically appears instantaneously in the zone with no prior trajectory, or shows movement that violates road geometry (e.g., cutting across a lake). These are hard physical flags.

#### Signal Layer 2 — Platform Activity Correlation

Every genuine delivery worker interacting with Zomato or Swiggy produces a stream of platform-side events: order pings received, orders accepted or declined, pickup confirmations, delivery completions. Allievo cross-references this event stream against the GPS claim:

```
Platform Correlation Checks:
  ✓ Order ping receipt:     Was the worker receiving order notifications from the zone's restaurant cluster?
  ✓ Last accepted order:    GPS of last pickup point must be within or adjacent to the claimed zone
  ✓ Order acceptance rate:  Workers mid-shift show natural accept/decline patterns; idle accounts don't
  ✓ App session continuity: Platform app must show an active session — not a background token only
```

A spoofed account that has not accepted a single order in the disrupted zone for the prior 2 hours will fail this check even if their GPS is correctly placed.

#### Signal Layer 3 — Device Fingerprint Integrity

Allievo collects a device fingerprint at onboarding and on each app open. The fingerprint includes:

```
Device Fingerprint Components:
  - Hardware ID (Android Device ID / IMEI hash)
  - SIM card carrier and cell tower registration (cross-checks physical location independently of GPS)
  - Accelerometer & gyroscope motion signature (real workers show constant vibration from road movement)
  - Network SSID history (a stationary worker at home will connect to a known home Wi-Fi, not tower pings from the zone)
  - Battery drain rate (active delivery workers show higher drain than idle devices)
```

The **cell tower cross-check** is particularly powerful: GPS can be spoofed, but a device's registered cell tower at the time of the disruption provides an independent, hardware-level location signal that cannot be faked by a GPS mock app. If the cell tower and GPS disagree by more than 500m, the claim is flagged.

#### Differentiation Decision Matrix

```
Signal                        | Genuine Worker        | GPS Spoofer
------------------------------|------------------------|------------------------
GPS trajectory pre-disruption | Natural road path      | Teleport / static jump
Cell tower location           | Matches GPS            | Mismatches GPS
Platform order activity       | Active last 60–90 min  | No recent activity
Micro-GPS drift               | Natural ±3–8m          | Suspiciously perfect
Accelerometer pattern         | Road vibration present | Flat / no motion
Device fingerprint            | Matches onboarding     | New or altered device
```

A genuine worker scores coherently across all signals. A spoofer will typically fail 2–3 of these checks simultaneously, which triggers the fraud pipeline regardless of their GPS accuracy.

---

### 8.2 Detecting Coordinated Fraud Rings

Individual fraud is manageable. Coordinated rings — where multiple fake accounts simultaneously claim a disruption — pose a systemic risk. Allievo uses a dedicated **Ring Detection Engine** that monitors cross-account patterns in real time during each disruption event.

#### Data Points Analyzed for Ring Detection

Beyond basic GPS, Allievo ingests the following cross-account signals during any active disruption event:

**1. Device Sharing Graph**
A legitimate delivery worker has one device. Fraud rings typically operate clusters of fake accounts from a small number of physical devices (phones with GPS mock apps). Allievo builds a device-sharing graph: if three policy accounts share the same hardware ID at any point in the prior 30 days, they are linked. During a disruption, a payout to one node in a linked cluster triggers a hold on all linked accounts pending review.

**2. UPI Destination Clustering**
Payouts ultimately land in UPI accounts. Allievo analyzes the graph of UPI destination accounts and checks for:
```
  - Multiple Allievo accounts mapping to the same UPI VPA
  - UPI accounts receiving payouts that are immediately forwarded to a common third account
  - New UPI registrations within 48 hours of a disruption event
```
A fraud ring typically funnels payouts to a single controller account. This graph structure is detectable even when individual accounts appear clean.

**3. Temporal Claim Clustering**
During genuine disruptions, claims arrive continuously over the disruption window as different workers' app sessions update. Coordinated fraud rings tend to trigger all their claims within a narrow time window — often within minutes of the disruption being confirmed — because the ring operator fires all accounts simultaneously.

```
Ring Detection Signal:
  Genuine disruption:   Claims arrive distributed over 30–90 minutes
  Fraud ring pattern:   ≥ 5 claims from different accounts within a 3-minute window,
                        all with GPS pings that appeared in the zone within the last 15 minutes
```

This "claim burst" pattern combined with fresh GPS registrations is a strong ring indicator.

**4. Social Graph & Referral Chain Analysis**
Allievo tracks how workers were onboarded. A fraud ring often recruits through a single referral chain (one person onboards 10+ accounts). If 8 accounts in the same referral subtree claim the same disruption event, the probability of coordinated fraud is very high. Allievo applies a multiplier to the fraud score for accounts with deep referral chain overlap.

**5. Historical Zone Presence vs. Zone Claim**
Allievo maintains a 30-day rolling log of each worker's active zones derived from platform activity (not self-reported). A worker who has never previously accepted an order in a zone — but claims to have been working there during a disruption — receives a significantly elevated fraud score regardless of their GPS position on the day.

```
Zone Presence Score = (Days active in claimed zone in last 30 days) / 30

Score < 0.1 (worked in zone < 3 days of last 30):  High suspicion flag
Score > 0.5 (worked in zone ≥ 15 days of last 30): Credibility boost
```

#### Ring Detection Summary

```
Ring Detection Signals:
  ✓ Device-sharing graph (shared hardware IDs across accounts)
  ✓ UPI destination clustering (payouts funneling to common accounts)
  ✓ Temporal claim bursting (coordinated simultaneous submissions)
  ✓ Referral chain overlap (accounts onboarded through same recruiter chain)
  ✓ Historical zone absence (claimed zone with no prior platform activity)
  ✓ Cross-account GPS proximity (10+ accounts reporting identical coordinates)
```

When 3 or more ring signals fire simultaneously, Allievo escalates from automated hold to a **Ring Alert**, which pauses all payouts in that cluster and notifies the human review team for same-day resolution.

---

### 8.3 Handling Flagged Claims Without Penalizing Honest Workers

This is the most critical UX challenge in Allievo's design. Heavy rain, poor network, and GPS signal degradation happen to honest workers simultaneously — exactly when they need coverage most. A system that flags too aggressively punishes the people it was built to protect.

Allievo's approach is built on three principles: **assume innocence first, pay what is unambiguous immediately, resolve disputes fast**.

#### The Tiered Payout Architecture

Rather than binary approve/hold, Allievo uses a three-tier response system:

```
Fraud Score  | Action                           | Worker Experience
-------------|----------------------------------|------------------------------------------
0.0 – 0.30   | Auto-approve                     | Payout within 10 minutes, no friction
0.31 – 0.55  | Soft flag — Partial Pay          | 60% payout immediately; remaining 40%
             |                                  | held for 24-hour passive review
0.56 – 0.70  | Hard flag — Full Hold            | No payout; worker notified with reason
             |                                  | category; 48-hour resolution window
0.71 – 1.0   | Fraud block — Manual Review      | Claim held; human review within 4 hours
             |                                  | during business hours
```

The **partial pay model** (Soft Flag band) is the most important design decision for fairness. A worker with a mildly elevated fraud score — perhaps because their GPS signal was unstable during the rain — still receives the majority of their payout immediately. The 40% hold is released automatically after 24 hours if no additional fraud signals emerge, without requiring any action from the worker.

#### The Network Drop Grace Period

GPS signal degradation in heavy rain is a well-documented phenomenon in urban India. Allievo's fraud model explicitly accounts for this:

```
Network Drop Accommodation:
  - If a worker's GPS pings become sparse or absent during the disruption window,
    the system does NOT treat absence of GPS data as evidence of fraud.
  - Instead, last-known-position is extended for up to 45 minutes with a
    "signal gap" flag — not a fraud flag.
  - The system cross-checks cell tower data during the gap. If tower data
    confirms the worker remained in the zone, the claim proceeds normally.
  - Only if both GPS AND cell tower data are absent simultaneously (very rare)
    does the system move to the Soft Flag tier.
```

This means a worker whose phone GPS dropped during a monsoon storm — exactly when they need the insurance — is protected by the cell tower fallback rather than penalized.

#### The Worker-Facing Explanation System

When a claim is flagged (any tier above auto-approve), the worker receives a transparent notification explaining the specific reason in plain language. Allievo never says "your claim is under review" without context. Instead:

```
Example Soft Flag notification (in Hindi/Telugu/English based on language preference):

  "Your payout for [disruption event] on [date] is being processed.
   ₹180 has been sent to your UPI now.
   The remaining ₹120 will be released within 24 hours.

   Reason for delay: Your location data was intermittent during the storm.
   No action needed from you — this resolves automatically."
```

For Hard Flag and above, the worker receives a simple one-question appeal option: "Were you working in [Zone Name] on [Date]?" with a Yes/No and an optional 100-character text note. This is intentionally minimal — not a document upload, not a form — because requiring complex documentation from a gig worker during or after a disruption is the primary failure mode of traditional insurance.

#### The Honest Worker Protection Guarantee

Allievo commits to the following SLAs for flagged legitimate claims:

```
Protection SLAs:
  - Soft flag (0.31–0.55): 100% of payout released within 24 hours if no new fraud signals
  - Hard flag (0.56–0.70): Human review within 48 hours; payout released same day if cleared
  - False positive rate target: < 3% of all claims flagged incorrectly
  - Repeat false positive: If a worker is incorrectly flagged twice in 90 days,
    their fraud score baseline is adjusted downward permanently
```

The **repeat false positive adjustment** is especially important for fairness. A worker who keeps getting flagged incorrectly — perhaps because they operate in a zone with poor network coverage — has their baseline recalibrated so the model learns their legitimate behavioral pattern rather than continuing to flag them.

#### Flagged Claim Flow Summary

```
┌──────────────────────────────────────────────────────────────┐
│                 DISRUPTION DETECTED IN ZONE                   │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
              Multi-Signal Fraud Score Computed
              (GPS + Cell Tower + Platform Activity
               + Device Fingerprint + Ring Signals)
                           │
            ┌──────────────┼──────────────┐
            │              │              │
         0–0.30         0.31–0.55      0.56–1.0
            │              │              │
            ▼              ▼              ▼
       Auto-Pay        Partial Pay    Full Hold
      (10 min)        60% now +      Worker notified
                      40% in 24hr    + Appeal option
                      (auto-release   + Human review
                       if no new       48hr SLA
                       signals)
                           │
                     Worker Notified
                   (plain language,
                    no jargon,
                    no forms)
```

---

### 8.4 Anti-Spoofing: Technical Implementation Notes

| Component                  | Technology / Approach                                    |
|----------------------------|----------------------------------------------------------|
| GPS trajectory analysis    | PostGIS spatial queries on ping history table            |
| Cell tower cross-check     | Android Network Location API (passive, no user action)   |
| Device fingerprinting      | FingerprintJS Pro (hashed, no PII stored)                |
| Accelerometer sampling     | Background service, 1 sample/min during active session   |
| Platform event stream      | Mock REST API (Phase 1); real OAuth integration (Phase 2)|
| Device-sharing graph       | Graph DB (Neo4j) or adjacency table in PostgreSQL        |
| UPI clustering analysis    | Batch job run post-disruption, flags before payout batch |
| Ring detection engine      | Python service (Celery worker), fires within 5 min of trigger |
| Partial payout release     | Scheduled Celery task with 24hr timer, auto-cancels on new signal |

---

## 9. Platform Choice — Web App

We have chosen to build Allievo as a **web application** (React frontend + FastAPI backend) for the following reasons:

1. **Accessibility:** Workers access it via a mobile browser — no app install required, reducing friction for onboarding
2. **Speed of development:** A responsive web app can be built and demoed faster in a 6-week hackathon than a native mobile app
3. **Admin panel:** The insurer/admin dashboard is naturally better suited to a browser interface
4. **Demo-ability:** Easier to share live links with judges and record demo videos
5. **Progressive upgrade path:** A PWA (Progressive Web App) wrapper can be added in Phase 3 to give a near-native mobile experience

The UI will be fully responsive and optimized for mobile screens (320px–480px), since most workers will access it on their smartphones.

---

## 10. Tech Stack

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
| Primary DB   | PostgreSQL + PostGIS| Relational + spatial queries for GPS analysis |
| Graph DB     | PostgreSQL adjacency table (Phase 1) / Neo4j (Phase 2) | Device-sharing and ring detection graphs |
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
| Cell Tower   | Android Network Location API | Independent location cross-check    |
| Device FP    | FingerprintJS Pro   | Hardware fingerprinting for spoofing defense  |

### Infrastructure
| Layer        | Technology          | Reason                                        |
|--------------|---------------------|-----------------------------------------------|
| Containerization | Docker + Docker Compose | Consistent dev/prod environment       |
| Hosting      | Render / Railway (free tier) | Easy deployment for demo purposes    |
| Version control | GitHub           | Single repo across all 3 phases               |

---

## 11. Development Plan

### Phase 1 (Mar 4–20): Ideation & Foundation ✅
- [x] Define persona, scenarios, and workflow
- [x] Design weekly premium model and parametric triggers
- [x] Plan AI/ML architecture
- [x] Design adversarial defense and anti-spoofing strategy
- [x] Finalize tech stack
- [x] Set up GitHub repository with project scaffolding
- [x] Initialize React frontend + FastAPI backend boilerplate
- [x] Set up PostgreSQL schema (workers, policies, claims, triggers, device_fingerprints, gps_pings)
- [x] Record 2-minute strategy video

### Phase 2 (Mar 21–Apr 4): Automation & Protection
- [ ] Worker registration and onboarding flow
- [ ] Policy creation with dynamic weekly premium calculation (ML model v1)
- [ ] Implement 5 parametric trigger monitors (weather, AQI, curfew, heat, outage)
- [ ] Basic fraud detection layer (rule-based + Isolation Forest)
- [ ] GPS trajectory analysis pipeline (PostGIS)
- [ ] Cell tower cross-check integration (Android Network Location API)
- [ ] Tiered payout system (auto-approve / partial-pay / hold)
- [ ] Worker-facing flagged claim notifications (plain language, multilingual)
- [ ] Zero-touch claim initiation pipeline
- [ ] Mock payout integration (Razorpay sandbox)
- [ ] Record 2-minute demo video

### Phase 3 (Apr 5–17): Scale & Optimise
- [ ] Advanced fraud detection: device-sharing graph, UPI clustering, ring detection engine
- [ ] Coordinated ring alert system with human review escalation
- [ ] Repeat false-positive baseline adjustment for legitimate workers
- [ ] Worker dashboard (earnings protected, active coverage, payout history, flag status)
- [ ] Admin/insurer dashboard (loss ratios, fraud ring alerts, predictive disruption analytics)
- [ ] PWA wrapper for mobile-native experience
- [ ] Full end-to-end demo with simulated disruption event + simulated fraud ring attempt
- [ ] Final pitch deck (PDF)
- [ ] Record 5-minute walkthrough demo video

---

## Team

| Role                    | Responsibilities                                    |
|-------------------------|-----------------------------------------------------|
| Frontend Developer      | React UI, worker dashboard, onboarding flow         |
| Backend Developer       | FastAPI, database, trigger monitoring pipelines      |
| ML Engineer             | Premium model, fraud detection, anti-spoofing models |
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
