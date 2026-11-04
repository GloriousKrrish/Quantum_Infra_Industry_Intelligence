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

  const n = Math.min(parcels.length, 8);
  const matrix: number[][] = [];

  for (let i = 0; i < n; i++) {
    const row: number[] = [];
    for (let j = 0; j < n; j++) {
      if (i === j) {
        const val = Math.round(
          -15 * parcels[i].utility_score + 0.1 * parcels[i].price_cr ** 2
        );
        row.push(val);
      } else if (j > i) {
        const val = Math.round(
          0.15 * parcels[i].price_cr * parcels[j].price_cr + (i + j) * 1.2
        );
        row.push(val);
      } else {
        row.push(0);
      }
    }
    matrix.push(row);
  }

  return (
    <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <Grid3X3 className="h-4 w-4 text-blue-600" />
          <h3 className="font-display text-sm font-bold text-slate-900">
            QUBO Interaction Coupling Matrix (Q<sub>ij</sub>)
          </h3>
        </div>
        <span className="font-mono text-xs text-slate-400">
          Upper Triangular · N={n}
        </span>
      </div>

      {/* Heatmap Grid */}
      <div className="overflow-x-auto pb-2">
        <div className="inline-block min-w-[340px]">
          {/* Header Row */}
          <div className="flex items-center gap-1.5 mb-1.5">
            <div className="w-10 text-[10px] font-mono text-slate-400 text-center" />
            {parcels.slice(0, n).map((p, idx) => (
              <div
                key={idx}
                className="w-9 text-center font-mono text-[10px] font-semibold text-slate-500 truncate"
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
                className="w-10 text-right pr-1 font-mono text-[10px] font-semibold text-slate-500 truncate"
                title={parcels[i].name}
              >
                q{i}
              </div>
              {row.map((val, j) => {
                if (j < i) {
                  return (
                    <div
                      key={j}
                      className="h-8 w-9 rounded-lg bg-slate-50/60 border border-slate-100"
                    />
                  );
                }

                const isDiagonal = i === j;
                const isHovered =
                  hoveredCell?.i === i && hoveredCell?.j === j;

                const bgClass = isDiagonal
                  ? "bg-blue-50 border-blue-200 text-blue-800 font-bold"
                  : val > 20
                  ? "bg-indigo-50 border-indigo-200 text-indigo-700 font-semibold"
                  : "bg-slate-50 border-slate-200 text-slate-700";

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
                      "flex h-8 w-9 cursor-pointer items-center justify-center rounded-lg border font-mono text-[11px] transition-all hover:scale-105",
                      bgClass,
                      isHovered && "ring-2 ring-blue-500 z-10 scale-105"
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

      {/* Info Tooltip */}
      <div className="mt-3 flex min-h-[40px] items-center rounded-xl border border-slate-100 bg-slate-50 p-2.5 text-xs">
        {hoveredCell ? (
          <div className="flex items-center gap-2 font-mono text-xs text-slate-700">
            <span className="text-blue-700 font-bold">
              Q[{hoveredCell.i},{hoveredCell.j}] = {hoveredCell.val}
            </span>
            <span className="text-slate-400">|</span>
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
