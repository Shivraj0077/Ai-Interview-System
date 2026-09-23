import type { InterviewStatus, Level } from "@/lib/types";
import { LEVEL_LABEL, scoreTone } from "@/lib/format";
import { Badge, cn } from "./ui";

export function StatusBadge({ status }: { status: InterviewStatus }) {
  if (status === "completed") return <Badge tone="good">Completed</Badge>;
  if (status === "in_progress")
    return (
      <Badge tone="brand">
        <span className="size-1.5 rounded-full bg-brand" aria-hidden /> In progress
      </Badge>
    );
  return <Badge>Not started</Badge>;
}

export function SampleBadge() {
  return (
    <Badge tone="warn" title="Pre-generated sample data, not a real candidate">
      Sample
    </Badge>
  );
}

const LEVEL_STYLE: Record<Level, string> = {
  L1: "bg-sky-50 text-sky-700 ring-sky-600/20",
  L2: "bg-violet-50 text-violet-700 ring-violet-600/20",
  L3: "bg-amber-50 text-amber-800 ring-amber-600/20",
};

export function LevelBadge({ level, long }: { level: Level; long?: boolean }) {
  return (
    <span
      className={cn("inline-flex items-center rounded-md px-1.5 py-0.5 font-mono text-xs font-medium ring-1 ring-inset", LEVEL_STYLE[level])}
      title={LEVEL_LABEL[level]}
    >
      {level}
      {long && <span className="ml-1 font-sans">· {LEVEL_LABEL[level]}</span>}
    </span>
  );
}

const TONE_TEXT = { good: "text-good", warn: "text-warn", bad: "text-bad", none: "text-faint" };

export function Score({ value, outOf = 100, className }: { value: number | null; outOf?: number; className?: string }) {
  return (
    <span className={cn("font-semibold tabular-nums", TONE_TEXT[scoreTone(value, outOf)], className)}>
      {value ?? "—"}
      {value !== null && outOf !== 100 && <span className="font-normal text-faint">/{outOf}</span>}
    </span>
  );
}
