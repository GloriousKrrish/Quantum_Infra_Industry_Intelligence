import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import AppLayout from "./components/layout/AppLayout";
import Dashboard from "./pages/Dashboard";
import LandStudio from "./pages/LandStudio";
import QuantumLab from "./pages/QuantumLab";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="land" element={<LandStudio />} />
            <Route path="quantum" element={<QuantumLab />} />
            <Route path="qaoa" element={<QuantumLab />} />
            <Route path="benchmarks" element={<QuantumLab />} />
            <Route path="builder" element={<LandStudio />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
