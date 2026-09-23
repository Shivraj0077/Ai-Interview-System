import type { Level, Turn } from "@/lib/types";
import { scoreTone } from "@/lib/format";

const ROW: Record<Level, number> = { L3: 0, L2: 1, L1: 2 };
const DOT = { good: "#067647", warn: "#dc6803", bad: "#d92d20", none: "#98a2b3" };

/** Step chart of the level each question was asked at, coloured by the score it received. */
export function DifficultyChart({ turns }: { turns: Turn[] }) {
  const answered = turns.filter((t) => t.answered);
  if (answered.length === 0) return <p className="text-sm text-muted">No answered questions yet.</p>;

  const colW = 88;
  const rowH = 36;
  const padL = 32;
  const padT = 14;
  const width = padL + colW * answered.length;
  const height = padT * 2 + rowH * 2;
  const x = (i: number) => padL + colW * i + colW / 2;
  const y = (l: Level) => padT + ROW[l] * rowH;
  const points = answered.map((t, i) => `${x(i)},${y(t.difficulty)}`).join(" ");

  return (
    <div className="overflow-x-auto">
      <svg
        viewBox={`0 0 ${width} ${height + 22}`}
        width={width}
        height={height + 22}
        className="shrink-0"
        role="img"
        aria-label={`Difficulty progression: ${answered.map((t) => t.difficulty).join(", ")}`}
      >
        {(["L3", "L2", "L1"] as Level[]).map((l) => (
          <g key={l}>
            <line x1={padL} x2={width} y1={y(l)} y2={y(l)} stroke="#e4e7ec" strokeDasharray="3 4" />
            <text x={0} y={y(l) + 4} fontSize="11" fill="#667085" fontFamily="var(--font-geist-mono)">
              {l}
            </text>
          </g>
        ))}
        <polyline points={points} fill="none" stroke="#0f766e" strokeWidth="2" strokeLinejoin="round" opacity="0.5" />
        {answered.map((t, i) => {
          const score = t.evaluation?.score ?? null;
          return (
            <g key={t.index}>
              <circle cx={x(i)} cy={y(t.difficulty)} r="7" fill="white" stroke={DOT[t.skipped ? "none" : scoreTone(score, 10)]} strokeWidth="3" />
              <text x={x(i)} y={height + 14} textAnchor="middle" fontSize="11" fill="#667085">
                Q{t.number}
                {score !== null ? ` · ${score}` : t.skipped ? " · skip" : ""}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
