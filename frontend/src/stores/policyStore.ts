import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Policy, Tier } from "../types";

interface PolicyState {
  activePolicy: Policy | null;
  policyHistory: Policy[];
  setPolicy: (policy: Policy) => void;
  updateTier: (tier: Tier) => void; // Tier switching
}

export const usePolicyStore = create<PolicyState>()(
  persist(
    (set) => ({
      activePolicy: null,
      policyHistory: [],
      setPolicy: (policy) => set({ activePolicy: policy }),
      updateTier: (tier) =>
        set((state) => {
          if (!state.activePolicy) return state;
          return {
            activePolicy: { ...state.activePolicy, tier },
          };
        }),
    }),
    {
      name: "allievo-policy",
    }
  )
);
