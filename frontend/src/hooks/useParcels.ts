import { useQuery } from "@tanstack/react-query";
import { fetchParcels, fetchParcelsWithinBudget } from "../lib/api";
import type { Parcel } from "../lib/api";
import { MOCK_PARCELS } from "../lib/mockData";

/**
 * Hook to fetch all parcels.
 * Falls back to mock data when API is unavailable.
 */
export function useParcels() {
  return useQuery<Parcel[]>({
    queryKey: ["parcels"],
    queryFn: fetchParcels,
    placeholderData: MOCK_PARCELS,
    retry: 1,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to fetch parcels within a given budget.
 */
export function useParcelsWithinBudget(budget: number) {
  return useQuery<Parcel[]>({
    queryKey: ["parcels", "budget", budget],
    queryFn: () => fetchParcelsWithinBudget(budget),
    placeholderData: MOCK_PARCELS.filter((p) => p.price_cr <= budget),
    retry: 1,
    staleTime: 5 * 60 * 1000,
  });
}
