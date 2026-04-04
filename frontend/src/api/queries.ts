import { useQuery } from "@tanstack/react-query";
import { MOCK_POLICY, MOCK_DASHBOARD, MOCK_ADMIN } from "./mocks";
import apiClient from "./client";
import { useAuthStore } from "../stores/authStore";

export const useProfile = (workerId: string | null) => {
  return useQuery({
    queryKey: ["profile", workerId],
    queryFn: async () => {
      if (!workerId) return null;
      const res = await apiClient.get(`/api/v1/workers/${workerId}/profile`);
      return res.data;
    },
    enabled: !!workerId,
  });
};

export const useCurrentPolicy = () => {
  const { userId } = useAuthStore();
  return useQuery({
    queryKey: ["policy", userId],
    queryFn: async () => {
      if (!userId) return MOCK_POLICY;
      try {
        const res = await apiClient.get(`/api/v1/policies/${userId}/current`);
        return res.data;
      } catch {
        return MOCK_POLICY;
      }
    },
  });
};

export const useClaims = () => {
  const { userId } = useAuthStore();
  return useQuery({
    queryKey: ["claims", userId],
    queryFn: async () => {
      if (!userId) return [];
      try {
        const res = await apiClient.get(`/api/v1/claims/${userId}/claims`);
        return res.data;
      } catch {
        return [];
      }
    },
    enabled: !!userId,
    refetchInterval: 30000, // Poll every 30s for live payout updates
  });
};

export const usePayouts = () => {
  const { userId } = useAuthStore();
  return useQuery({
    queryKey: ["payouts", userId],
    queryFn: async () => {
      if (!userId) return [];
      try {
        const res = await apiClient.get(`/api/v1/claims/${userId}/payout-status`);
        return res.data;
      } catch {
        return [];
      }
    },
    enabled: !!userId,
    refetchInterval: 15000,
  });
};

export const useDashboard = () => {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => {
      await new Promise((r) => setTimeout(r, 500));
      return MOCK_DASHBOARD;
    },
  });
};

export const useAdminStats = () => {
  return useQuery({
    queryKey: ["admin-stats"],
    queryFn: async () => {
      try {
        const res = await apiClient.get("/api/v1/admin/dashboard");
        return res.data;
      } catch {
        return MOCK_ADMIN;
      }
    },
    refetchInterval: 30000,
  });
};

export const useRiskStatus = (city: string) => {
  return useQuery({
    queryKey: ["risk-status", city],
    queryFn: async () => {
      const res = await apiClient.get(`/api/v1/status/risk/${city}`);
      return res.data;
    },
    refetchInterval: 60000 * 5,
  });
};
