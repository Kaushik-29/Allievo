// Core Types for Allievo Frontend

export type UserRole = "worker" | "admin";

export type Tier = "basic" | "standard" | "premium";

export interface UserProfile {
  id: string;
  phone: string;
  name: string;
  city: string;
  role: UserRole;
  language: "en" | "hi" | "kn" | "ta" | "te";
  upiId?: string;
  weeksActive: number;
  activePolicyId?: string;
  consent: {
    gps: boolean;
    device: boolean;
    platform: boolean;
  };
}

export interface Policy {
  id: string;
  workerId: string;
  tier: Tier;
  status: "active" | "expired" | "pending";
  startDate: string;
  endDate: string;
  premiumAmount: number;
  maxPayout: number;
  coverageFactor: number;
  calculationBreakdown: {
    base: number;
    risk: number; // dynamically added
    loyalty: number; // loyalty discount
  };
  changeReason?: string; // "High risk zone", "Loyalty discount applied", etc.
}

export interface Claim {
  id: string;
  workerId: string;
  policyId: string;
  status: "pending" | "approved" | "partial" | "held" | "blocked" | "rejected";
  triggerType: "heavy_rain" | "heatwave" | "aqi_crisis" | "curfew" | "platform_outage";
  triggerDate: string;
  amount: number;
  cappedAmount: number;
  calculationLog: string;
  fraudScore: number;
  fraudReason?: string;
  payoutTimeline: {
    status: string;
    description: string;
    at: string;
  }[];
  expectedReleaseAt?: string; // For partial payouts
}

export interface DashboardStats {
  todayEarnings: number;
  totalEarnings: number;
  predictedPayout: number; // Next potential payout based on historical patterns
  activeDisruptions: {
    type: string;
    severity: "low" | "medium" | "high";
    description: string;
  }[];
  riskTrend: {
    date: string;
    score: number;
  }[];
}

export interface AdminStats {
  activePolicies: number;
  totalPremiums: number;
  totalPayouts: number;
  lossRatio: number;
  lossRatioTrend: {
    month: string;
    ratio: number;
  }[];
  ringAlerts: {
    id: string;
    workerIds: string[];
    riskScore: number;
    status: "open" | "resolved";
    createdAt: string;
  }[];
}
