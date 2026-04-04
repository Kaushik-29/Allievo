/**
 * planStore — global reactive cache for the worker's current enrollment.
 * Updated immediately after a plan payment succeeds in Plans.tsx.
 * Subscribed to by WorkerDashboard and PolicyManagement for instant sync.
 */
import { create } from "zustand";

interface PlanState {
  /** Name of currently enrolled plan, e.g. "basic" | "dynamic" | "premium" | null */
  currentPlan: string | null;
  /** ISO timestamp of last enrollment — used as a refresh trigger */
  enrolledAt: string | null;
  /** Set after payment succeeds */
  setCurrentPlan: (plan: string) => void;
  /** Call to force a re-fetch in subscribers (bumps enrolledAt) */
  refreshPlan: () => void;
  /** Clear on logout */
  clearPlan: () => void;
}

export const usePlanStore = create<PlanState>((set) => ({
  currentPlan: null,
  enrolledAt: null,
  setCurrentPlan: (plan) =>
    set({ currentPlan: plan, enrolledAt: new Date().toISOString() }),
  refreshPlan: () =>
    set({ enrolledAt: new Date().toISOString() }),
  clearPlan: () =>
    set({ currentPlan: null, enrolledAt: null }),
}));
