import type { UserProfile, Policy, Claim, DashboardStats, AdminStats } from "../types";

export const MOCK_USER: UserProfile = {
  id: "worker-123",
  phone: "+91 98765 43210",
  name: "Ravi Kumar",
  city: "Bengaluru",
  role: "worker",
  language: "kn",
  upiId: "ravi.kumar@oksbi",
  weeksActive: 14,
  activePolicyId: "pol-456",
  consent: {
    gps: true,
    device: true,
    platform: true,
  },
};

export const MOCK_POLICY: Policy = {
  id: "pol-456",
  workerId: "worker-123",
  tier: "standard",
  status: "active",
  startDate: "2023-10-01",
  endDate: "2023-10-08",
  premiumAmount: 65,
  maxPayout: 1500,
  coverageFactor: 1.0,
  calculationBreakdown: {
    base: 40,
    risk: 35,
    loyalty: -10,
  },
  changeReason: "High risk zone adjustment & Gold Partner discount",
};

export const MOCK_CLAIMS: Claim[] = [
  {
    id: "CLM-1092",
    workerId: "worker-123",
    policyId: "pol-456",
    status: "approved",
    triggerType: "heavy_rain",
    triggerDate: "2023-10-15",
    amount: 850,
    cappedAmount: 850,
    calculationLog: "DAE (350) * 2.5h * Score (0.85)",
    fraudScore: 0.12,
    payoutTimeline: [
      { status: "Generated", description: "Disruption detected", at: "2023-10-15 14:30" },
      { status: "Validated", description: "GPS & Platform verified", at: "2023-10-15 14:35" },
      { status: "Paid", description: "UPI Transfer Success", at: "2023-10-15 14:40" },
    ],
  },
  {
    id: "CLM-1084",
    workerId: "worker-123",
    policyId: "pol-456",
    status: "partial",
    triggerType: "platform_outage",
    triggerDate: "2023-09-02",
    amount: 1033,
    cappedAmount: 620,
    calculationLog: "DAE (400) * 3h * Score (0.90)",
    fraudScore: 0.45,
    fraudReason: "Location data was intermittent during outage",
    payoutTimeline: [
      { status: "Generated", description: "Platform reported down", at: "2023-09-02 11:00" },
      { status: "Partial Paid", description: "60% released immediately", at: "2023-09-02 11:15" },
      { status: "Held", description: "Remaining 40% under review", at: "2023-09-02 11:15" },
    ],
    expectedReleaseAt: "2023-09-03 11:15",
  },
  {
    id: "CLM-1055",
    workerId: "worker-123",
    policyId: "pol-456",
    status: "held",
    triggerType: "aqi_crisis",
    triggerDate: "2023-07-18",
    amount: 700,
    cappedAmount: 0,
    calculationLog: "DAE (350) * 2h * Score (1.0)",
    fraudScore: 0.72,
    fraudReason: "Device fingerprinting shared with multiple accounts",
    payoutTimeline: [
      { status: "Generated", description: "AQI exceeded 400", at: "2023-07-18 09:00" },
      { status: "Held", description: "Fraud signals detected", at: "2023-07-18 09:10" },
    ],
  },
];

export const MOCK_DASHBOARD: DashboardStats = {
  todayEarnings: 450,
  totalEarnings: 12450,
  predictedPayout: 720,
  activeDisruptions: [
    {
      type: "rain",
      severity: "high",
      description: "Heavy rain alert in Koramangala (4PM - 7PM). You are covered.",
    },
  ],
  riskTrend: [
    { date: "Mon", score: 0.2 },
    { date: "Tue", score: 0.35 },
    { date: "Wed", score: 0.65 },
    { date: "Thu", score: 0.4 },
    { date: "Fri", score: 0.25 },
    { date: "Sat", score: 0.15 },
    { date: "Sun", score: 0.1 },
  ],
};

export const MOCK_ADMIN: AdminStats = {
  activePolicies: 1240,
  totalPremiums: 85400,
  totalPayouts: 12450,
  lossRatio: 14.5,
  lossRatioTrend: [
    { month: "Jan", ratio: 12 },
    { month: "Feb", ratio: 15 },
    { month: "Mar", ratio: 18 },
    { month: "Apr", ratio: 14 },
    { month: "May", ratio: 10 },
    { month: "Jun", ratio: 22 },
  ],
  ringAlerts: [
    {
      id: "RNG-99",
      workerIds: ["W-1", "W-2", "W-3", "W-4"],
      riskScore: 0.92,
      status: "open",
      createdAt: "2023-10-15 10:00",
    },
  ],
};
