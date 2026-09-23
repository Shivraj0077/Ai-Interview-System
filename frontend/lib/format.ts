export function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const minutes = Math.round(diff / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

export function duration(startIso: string | null, endIso: string | null): string | null {
  if (!startIso || !endIso) return null;
  const minutes = Math.max(1, Math.round((new Date(endIso).getTime() - new Date(startIso).getTime()) / 60_000));
  return `${minutes} min`;
}

export function scoreTone(score: number | null | undefined, outOf = 100): "good" | "warn" | "bad" | "none" {
  if (score === null || score === undefined) return "none";
  const pct = (score / outOf) * 100;
  if (pct >= 75) return "good";
  if (pct >= 55) return "warn";
  return "bad";
}

export const LEVEL_LABEL: Record<string, string> = {
  L1: "Foundational",
  L2: "Intermediate",
  L3: "Advanced",
};
