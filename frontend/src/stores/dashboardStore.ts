import { create } from "zustand";
import type { DashboardStats } from "../types";

interface DashboardState {
  stats: DashboardStats | null;
  setStats: (stats: DashboardStats) => void;
  updateRiskTrend: (trend: DashboardStats["riskTrend"]) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  stats: null,
  setStats: (stats) => set({ stats }),
  updateRiskTrend: (riskTrend) =>
    set((state) => ({
      stats: state.stats ? { ...state.stats, riskTrend } : null,
    })),
}));
