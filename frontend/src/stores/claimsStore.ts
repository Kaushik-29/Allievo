import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Claim } from "../types";

interface ClaimsState {
  claims: Claim[];
  activeClaimId: string | null;
  addClaim: (claim: Claim) => void;
  setActiveClaim: (id: string | null) => void;
  updateClaimStatus: (id: string, status: Claim["status"]) => void;
}

export const useClaimsStore = create<ClaimsState>()(
  persist(
    (set) => ({
      claims: [],
      activeClaimId: null,
      addClaim: (claim) =>
        set((state) => ({
          claims: [claim, ...state.claims],
        })),
      setActiveClaim: (id) => set({ activeClaimId: id }),
      updateClaimStatus: (id, status) =>
        set((state) => ({
          claims: state.claims.map((c) => (c.id === id ? { ...c, status } : c)),
        })),
    }),
    {
      name: "allievo-claims",
    }
  )
);
