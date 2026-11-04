import {
  MapPin,
  Cpu,
  BarChart3,
  IndianRupee,
  TrendingUp,
  TrendingDown,
  Bot,
  Brain,
  Grid3X3,
  Atom,
  Server,
  GitMerge,
  Sparkles,
  CheckCircle2,
  Loader2,
  Circle,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { cn } from "../lib/utils";
import { MOCK_PARCELS, MOCK_BITSTRING_PROBS, MOCK_WORKFLOW_STEPS } from "../lib/mockData";

// ─── Icon map for workflow steps ──────────────────────────────────────────────

const STEP_ICONS: Record<string, React.ElementType> = {
  Bot,
  MapPin,
  Brain,
  Grid3X3,
  Atom,
  Cpu,
  Server,
  GitMerge,
  Sparkles,
};

// ─── KPI Metric Card ─────────────────────────────────────────────────────────

interface MetricCardProps {
  label: string;
  value: string;
  icon: React.ElementType;
  accentColor: string;
  borderColor: string;
  trend?: { value: string; positive: boolean };
}

function MetricCard({ label, value, icon: Icon, accentColor, borderColor, trend }: MetricCardProps) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl border border-slate-700/50 bg-slate-900/80 p-5 transition-all duration-300 hover:border-slate-600/50 hover:shadow-lg",
        borderColor
      )}
    >
      {/* Subtle glow background */}
      <div className={cn("absolute -right-4 -top-4 h-24 w-24 rounded-full opacity-[0.07] blur-2xl", accentColor)} />

      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-slate-500">{label}</p>
          <p className="mt-2 text-2xl font-bold text-slate-100">{value}</p>
          {trend && (
            <div className="mt-1.5 flex items-center gap-1">
              {trend.positive ? (
                <TrendingUp className="h-3 w-3 text-emerald-400" />
              ) : (
                <TrendingDown className="h-3 w-3 text-rose-400" />
              )}
              <span
                className={cn(
                  "text-xs font-medium",
                  trend.positive ? "text-emerald-400" : "text-rose-400"
                )}
              >
                {trend.value}
              </span>
            </div>
          )}
        </div>
        <div className={cn("flex h-10 w-10 items-center justify-center rounded-lg", accentColor.replace("bg-", "bg-") + "/10")}>
          <Icon className={cn("h-5 w-5", accentColor.replace("bg-", "text-"))} />
        </div>
      </div>
    </div>
  );
}

// ─── Status Badge ─────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    Available: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    "Under Review": "bg-amber-500/10 text-amber-400 border-amber-500/20",
    Shortlisted: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
  };
  return (
    <span className={cn("inline-flex rounded-full border px-2.5 py-0.5 text-[11px] font-medium", styles[status] || "")}>
      {status}
    </span>
  );
}

// ─── Workflow Step Status Icon ────────────────────────────────────────────────

function StepStatusIcon({ status }: { status: string }) {
  switch (status) {
    case "completed":
      return <CheckCircle2 className="h-4 w-4 text-emerald-400" />;
    case "active":
      return <Loader2 className="h-4 w-4 animate-spin text-cyan-400" />;
    default:
      return <Circle className="h-4 w-4 text-slate-600" />;
  }
}

// ─── Custom Tooltip for QAOA Chart ───────────────────────────────────────────

function QAOATooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const data = payload[0].payload;
  return (
    <div className="rounded-lg border border-slate-700/50 bg-slate-900 px-3 py-2 shadow-xl">
      <p className="font-mono text-xs text-cyan-400">{data.bitstring}</p>
      <p className="text-sm text-slate-300">
        Probability: <span className="font-semibold text-slate-100">{(data.probability * 100).toFixed(1)}%</span>
      </p>
      {data.isOptimal && (
        <p className="text-[10px] font-semibold uppercase tracking-wider text-amber-400">★ Optimal</p>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// DASHBOARD PAGE
// ═══════════════════════════════════════════════════════════════════════════════

export default function Dashboard() {
  return (
    <div className="space-y-6">
      {/* ── Row 1: KPI Metric Cards ───────────────────────────── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Total Parcels Analyzed"
          value="8"
          icon={MapPin}
          accentColor="bg-emerald-400"
          borderColor="border-l-2 border-l-emerald-400"
          trend={{ value: "+2 this week", positive: true }}
        />
        <MetricCard
          label="Active Quantum Jobs"
          value="3"
          icon={Cpu}
          accentColor="bg-cyan-400"
          borderColor="border-l-2 border-l-cyan-400"
          trend={{ value: "2 queued", positive: true }}
        />
        <MetricCard
          label="Benchmark Score"
          value="0.87α"
          icon={BarChart3}
          accentColor="bg-amber-400"
          borderColor="border-l-2 border-l-amber-400"
          trend={{ value: "+0.05 vs baseline", positive: true }}
        />
        <MetricCard
          label="Budget Utilization"
          value="₹12.4 / 15.0 Cr"
          icon={IndianRupee}
          accentColor="bg-violet-400"
          borderColor="border-l-2 border-l-violet-400"
          trend={{ value: "82.7% utilized", positive: true }}
        />
      </div>

      {/* ── Row 2: Parcels Table + QAOA Chart ─────────────────── */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        {/* LEFT: Pune Development Parcels Table */}
        <div className="rounded-xl border border-slate-700/50 bg-slate-900/80 p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-200">Pune Development Parcels</h2>
            <span className="rounded-full bg-slate-800 px-2.5 py-0.5 text-[11px] font-medium text-slate-400">
              {MOCK_PARCELS.length} parcels
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-700/50">
                  <th className="pb-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500">Name</th>
                  <th className="pb-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500">Area</th>
                  <th className="pb-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500">Price</th>
                  <th className="pb-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500">Infra</th>
                  <th className="pb-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500">Return</th>
                  <th className="pb-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {MOCK_PARCELS.map((parcel) => (
                  <tr key={parcel.id} className="group transition-colors hover:bg-slate-800/30">
                    <td className="py-3 pr-3">
                      <div>
                        <p className="font-medium text-slate-200 group-hover:text-cyan-400 transition-colors">{parcel.name}</p>
                        <p className="text-[11px] text-slate-500">{parcel.location}</p>
                      </div>
                    </td>
                    <td className="py-3 font-mono text-xs text-slate-300">{parcel.area_acres}ac</td>
                    <td className="py-3 font-mono text-xs text-slate-300">₹{parcel.price_cr}Cr</td>
                    <td className="py-3">
                      {/* Mini infra score bar */}
                      <div className="flex items-center gap-1.5">
                        <div className="h-1.5 w-16 overflow-hidden rounded-full bg-slate-800">
                          <div
                            className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-emerald-400"
                            style={{ width: `${parcel.utility_score * 100}%` }}
                          />
                        </div>
                        <span className="font-mono text-[11px] text-slate-400">
                          {(parcel.utility_score * 100).toFixed(0)}
                        </span>
                      </div>
                    </td>
                    <td className="py-3">
                      <span className={cn("font-mono text-xs", parcel.return_pct >= 17 ? "text-emerald-400" : "text-slate-400")}>
                        {parcel.return_pct}%
                      </span>
                    </td>
                    <td className="py-3">
                      <StatusBadge status={parcel.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* RIGHT: QAOA Optimization Results */}
        <div className="rounded-xl border border-slate-700/50 bg-slate-900/80 p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-200">QAOA Optimization Results</h2>
            <div className="flex items-center gap-1.5 rounded-full bg-cyan-500/10 px-2.5 py-0.5">
              <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-cyan-400" />
              <span className="text-[11px] font-medium text-cyan-400">p=2 layers</span>
            </div>
          </div>

          {/* Optimal result callout */}
          <div className="mb-4 rounded-lg border border-cyan-500/20 bg-cyan-500/5 px-4 py-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[11px] font-medium uppercase tracking-wider text-cyan-500">Optimal Bitstring</p>
                <p className="mt-0.5 font-mono text-lg font-bold tracking-widest text-cyan-400">1 1 0 1 0 0 1 0</p>
              </div>
              <div className="text-right">
                <p className="text-[11px] font-medium uppercase tracking-wider text-slate-500">Probability</p>
                <p className="mt-0.5 text-lg font-bold text-slate-100">34.2%</p>
              </div>
            </div>
          </div>

          {/* Bitstring probability bar chart */}
          <div className="h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={MOCK_BITSTRING_PROBS} margin={{ top: 5, right: 5, bottom: 5, left: -10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis
                  dataKey="bitstring"
                  tick={{ fontSize: 9, fill: "#64748b", fontFamily: "monospace" }}
                  angle={-45}
                  textAnchor="end"
                  height={50}
                  axisLine={{ stroke: "#334155" }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: "#64748b" }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
                />
                <Tooltip content={<QAOATooltip />} />
                <Bar dataKey="probability" radius={[4, 4, 0, 0]} maxBarSize={32}>
                  {MOCK_BITSTRING_PROBS.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.isOptimal ? "#22d3ee" : "#334155"}
                      fillOpacity={entry.isOptimal ? 1 : 0.7}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* ── Row 3: 9-Step Computational Workflow ──────────────── */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-900/80 p-5">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-200">9-Step Computational Workflow</h2>
            <p className="mt-0.5 text-xs text-slate-500">Pune ₹15 Cr Investment Pipeline</p>
          </div>
          <div className="flex items-center gap-4 text-[11px]">
            <span className="flex items-center gap-1.5 text-emerald-400">
              <CheckCircle2 className="h-3 w-3" /> Completed
            </span>
            <span className="flex items-center gap-1.5 text-cyan-400">
              <Loader2 className="h-3 w-3" /> Active
            </span>
            <span className="flex items-center gap-1.5 text-slate-500">
              <Circle className="h-3 w-3" /> Pending
            </span>
          </div>
        </div>

        {/* Horizontal stepper */}
        <div className="overflow-x-auto">
          <div className="flex min-w-[900px] items-start gap-2">
            {MOCK_WORKFLOW_STEPS.map((step, idx) => {
              const Icon = STEP_ICONS[step.icon] || Circle;
              const isCompleted = step.status === "completed";
              const isActive = step.status === "active";

              return (
                <div key={step.step} className="flex flex-1 items-start">
                  {/* Step card */}
                  <div
                    className={cn(
                      "flex w-full flex-col items-center rounded-lg border p-3 transition-all",
                      isActive
                        ? "border-cyan-500/30 bg-cyan-500/5 shadow-[0_0_20px_rgba(6,182,212,0.1)]"
                        : isCompleted
                          ? "border-emerald-500/20 bg-emerald-500/5"
                          : "border-slate-700/30 bg-slate-800/30"
                    )}
                  >
                    <div
                      className={cn(
                        "mb-2 flex h-8 w-8 items-center justify-center rounded-lg",
                        isActive
                          ? "bg-cyan-500/20"
                          : isCompleted
                            ? "bg-emerald-500/20"
                            : "bg-slate-700/30"
                      )}
                    >
                      <Icon
                        className={cn(
                          "h-4 w-4",
                          isActive
                            ? "text-cyan-400"
                            : isCompleted
                              ? "text-emerald-400"
                              : "text-slate-600"
                        )}
                      />
                    </div>
                    <StepStatusIcon status={step.status} />
                    <p
                      className={cn(
                        "mt-1.5 text-center text-[11px] font-semibold",
                        isActive ? "text-cyan-400" : isCompleted ? "text-emerald-400" : "text-slate-500"
                      )}
                    >
                      {step.name}
                    </p>
                    <p className="mt-0.5 text-center text-[9px] leading-tight text-slate-600">
                      {step.description}
                    </p>
                  </div>

                  {/* Connector line */}
                  {idx < MOCK_WORKFLOW_STEPS.length - 1 && (
                    <div className="mt-7 flex w-4 shrink-0 items-center">
                      <div
                        className={cn(
                          "h-[2px] w-full",
                          isCompleted ? "bg-emerald-500/40" : "bg-slate-700/40"
                        )}
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
