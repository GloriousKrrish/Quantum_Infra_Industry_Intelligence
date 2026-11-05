import { useQuery, useMutation } from "@tanstack/react-query";
import { runQuantumOptimization, runBenchmark, runPuneWorkflow } from "../lib/api";
import type { QuantumResult, BenchmarkResult } from "../lib/api";
import { MOCK_QUANTUM_RESULT, MOCK_BENCHMARK } from "../lib/mockData";

/**
 * Hook to run QAOA quantum optimization for a given budget.
 */
export function useQuantumOptimization() {
  return useMutation({
    mutationFn: (budget: number) => runQuantumOptimization({ budget_crore: budget }),
  });
}

/**
 * Hook to run classical vs quantum benchmark.
 */
export function useBenchmark() {
  return useMutation({
    mutationFn: (budget: number) => runBenchmark(budget),
  });
}

/**
 * Hook to run the full 9-step Pune workflow.
 */
export function useWorkflow() {
  return useMutation({
    mutationFn: (budget: number) => runPuneWorkflow({ budget_crore: budget }),
  });
}

/**
 * Convenience hook that returns mock quantum result for static display.
 */
export function useQuantumResult() {
  return useQuery<QuantumResult>({
    queryKey: ["quantum-result"],
    queryFn: async () => MOCK_QUANTUM_RESULT,
    staleTime: Infinity,
  });
}

/**
 * Convenience hook that returns mock benchmark result for static display.
 */
export function useBenchmarkResult() {
  return useQuery<BenchmarkResult>({
    queryKey: ["benchmark-result"],
    queryFn: async () => MOCK_BENCHMARK,
    staleTime: Infinity,
  });
}
