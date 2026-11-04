import { useState } from "react";
import { Grid3X3, Info } from "lucide-react";
import { cn } from "../../lib/utils";

interface QUBOHeatmapProps {
  parcels: { id: number; name: string; price_cr: number; utility_score: number }[];
}

export default function QUBOHeatmap({ parcels }: QUBOHeatmapProps) {
  const [hoveredCell, setHoveredCell] = useState<{
    i: number;
    j: number;
    val: number;
    p1: string;
    p2: string;
  } | null>(null);

  // Generate synthetic QUBO matrix based on prices and utilities
  // Q_ii = -10 * U_i + lambda * Price_i^2 - 2 * lambda * Budget * Price_i
  // Q_ij = 2 * lambda * Price_i * Price_j + risk_ij
  const n = Math.min(parcels.length, 8);
  const matrix: number[][] = [];

  for (let i = 0; i < n; i++) {
    const row: number[] = [];
    for (let j = 0; j < n; j++) {
      if (i === j) {
        // Diagonal: Individual utility vs budget penalty
        const val = Math.round(
          -15 * parcels[i].utility_score + 0.1 * parcels[i].price_cr ** 2
        );
        row.push(val);
      } else if (j > i) {
        // Off-diagonal: Cross budget interaction
        const val = Math.round(
          0.15 * parcels[i].price_cr * parcels[j].price_cr + (i + j) * 1.2
        );
        row.push(val);
      } else {
        // Symmetric lower half
        row.push(0);
      }
    }
    matrix.push(row);
  }

  return (
    <div className="flex flex-col rounded-xl border border-slate-800 bg-slate-950/80 p-5 backdrop-blur-md">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <Grid3X3 className="h-4 w-4 text-cyan-400" />
          <h3 className="font-display text-sm font-semibold text-white">
            QUBO Interaction Coupling Matrix (Q<sub>ij</sub>)
          </h3>
        </div>
        <span className="font-mono text-[10px] text-slate-400">
          Upper Triangular · N={n}
        </span>
      </div>

      {/* Heatmap Grid */}
      <div className="overflow-x-auto pb-2">
        <div className="inline-block min-w-[340px]">
          {/* Header Row */}
          <div className="flex items-center gap-1.5 mb-1.5">
            <div className="w-10 text-[10px] font-mono text-slate-500 text-center" />
            {parcels.slice(0, n).map((p, idx) => (
              <div
                key={idx}
                className="w-9 text-center font-mono text-[10px] text-slate-400 truncate"
                title={p.name}
              >
                q{idx}
              </div>
            ))}
          </div>

          {/* Matrix Rows */}
          {matrix.map((row, i) => (
            <div key={i} className="flex items-center gap-1.5 mb-1.5">
              <div
                className="w-10 text-right pr-1 font-mono text-[10px] text-slate-400 truncate"
                title={parcels[i].name}
              >
                q{i}
              </div>
              {row.map((val, j) => {
                if (j < i) {
                  return (
                    <div
                      key={j}
                      className="h-8 w-9 rounded bg-slate-950/30 border border-slate-900/60"
                    />
                  );
                }

                const isDiagonal = i === j;
                const isHovered =
                  hoveredCell?.i === i && hoveredCell?.j === j;

                // Color scale
                const bgClass = isDiagonal
                  ? "bg-cyan-950/70 border-cyan-500/40 text-cyan-300"
                  : val > 20
                  ? "bg-purple-950/60 border-purple-500/30 text-purple-300"
                  : "bg-slate-900 border-slate-800 text-slate-300";

                return (
                  <div
                    key={j}
                    onMouseEnter={() =>
                      setHoveredCell({
                        i,
                        j,
                        val,
                        p1: parcels[i].name,
                        p2: parcels[j].name,
                      })
                    }
                    onMouseLeave={() => setHoveredCell(null)}
                    className={cn(
                      "flex h-8 w-9 cursor-pointer items-center justify-center rounded border font-mono text-[10px] transition-all hover:scale-110",
                      bgClass,
                      isHovered && "ring-2 ring-cyan-400 z-10 scale-110"
                    )}
                  >
                    {val}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Hover Info Tooltip Banner */}
      <div className="mt-3 flex min-h-[42px] items-center rounded-lg border border-slate-800 bg-slate-900/80 p-2.5 text-xs">
        {hoveredCell ? (
          <div className="flex items-center gap-2 font-mono text-[11px] text-slate-200">
            <span className="text-cyan-400 font-bold">
              Q[{hoveredCell.i},{hoveredCell.j}] = {hoveredCell.val}
            </span>
            <span className="text-slate-500">|</span>
            {hoveredCell.i === hoveredCell.j ? (
              <span>Self-energy: {hoveredCell.p1} (Utility vs Cost)</span>
            ) : (
              <span>
                Coupling: {hoveredCell.p1} &harr; {hoveredCell.p2} (Budget/Risk)
              </span>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-2 text-slate-500 text-xs">
            <Info className="h-3.5 w-3.5" />
            <span>Hover over any matrix element to inspect mathematical couplings</span>
          </div>
        )}
      </div>
    </div>
  );
}
