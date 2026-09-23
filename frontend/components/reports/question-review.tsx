"use client";

import { useState } from "react";
import { AlertOctagon, Check, ChevronDown, ShieldCheck, Sparkles, X } from "lucide-react";
import type { Turn } from "@/lib/types";
import { Badge, cn } from "../ui";
import { LevelBadge, Score } from "../badges";

const VERDICT = {
  strong: { label: "Strong", tone: "good" as const },
  average: { label: "Adequate", tone: "warn" as const },
  weak: { label: "Needs improvement", tone: "bad" as const },
};

function SignalList({ title, items, icon, className }: { title: string; items: string[]; icon: React.ReactNode; className: string }) {
  if (items.length === 0) return null;
  return (
    <div>
      <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-faint">{title}</p>
      <ul className="space-y-1">
        {items.map((s) => (
          <li key={s} className="flex items-start gap-2 text-sm text-ink-2">
            <span className={cn("mt-0.5 grid size-4 shrink-0 place-items-center rounded-full", className)}>{icon}</span>
            {s}
          </li>
        ))}
      </ul>
    </div>
  );
}

function TurnDetail({ turn }: { turn: Turn }) {
  const ev = turn.evaluation;
  return (
    <div className="space-y-5 border-t border-line bg-canvas/60 px-5 py-5">
      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-faint">Question</p>
          <p className="text-sm leading-relaxed text-ink">{turn.question}</p>
        </div>
        <div>
          <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-faint">Candidate answer</p>
          {turn.skipped ? (
            <p className="text-sm italic text-muted">Skipped</p>
          ) : (
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink-2">{turn.answer}</p>
          )}
        </div>
      </div>

      {ev && (
        <>
          <div className="grid gap-5 md:grid-cols-2">
            <SignalList
              title="Covered"
              items={ev.core_coverage}
              icon={<Check className="size-3" strokeWidth={3} />}
              className="bg-good-soft text-good"
            />
            <SignalList
              title="Missed"
              items={ev.missed_core_signals}
              icon={<X className="size-3" strokeWidth={3} />}
              className="bg-bad-soft text-bad"
            />
            <SignalList
              title="Advanced (bonus)"
              items={ev.advanced_coverage}
              icon={<Sparkles className="size-2.5" />}
              className="bg-violet-50 text-violet-700"
            />
            <SignalList
              title="Misconceptions detected"
              items={ev.misconceptions_detected}
              icon={<AlertOctagon className="size-2.5" />}
              className="bg-warn-soft text-warn"
            />
          </div>

          <div className="flex flex-wrap gap-x-5 gap-y-1.5 border-t border-line pt-4 text-xs text-muted">
            <span>Communication {ev.communication_score}/10</span>
            <span className="flex items-center gap-1">
              <ShieldCheck className="size-3.5 text-brand" aria-hidden />
              {ev.ungrounded_removed.length === 0
                ? "All cited signals verified against the knowledge base"
                : `${ev.ungrounded_removed.length} unverifiable claim${ev.ungrounded_removed.length > 1 ? "s" : ""} removed by grounding check`}
            </span>
            {ev.score_capped_from !== null && (
              <span>Score lowered from {ev.score_capped_from} to match verified evidence</span>
            )}
            {turn.retrieval_note && <span>{turn.retrieval_note}</span>}
          </div>
        </>
      )}
    </div>
  );
}

export function QuestionReview({ turns }: { turns: Turn[] }) {
  const [open, setOpen] = useState<Set<number>>(new Set());
  const answered = turns.filter((t) => t.answered);
  const toggle = (i: number) =>
    setOpen((s) => {
      const n = new Set(s);
      if (n.has(i)) n.delete(i);
      else n.add(i);
      return n;
    });
  const allOpen = open.size === answered.length;

  return (
    <div>
      <div className="flex justify-end border-b border-line px-5 py-2">
        <button
          className="text-xs font-medium text-brand hover:text-brand-strong"
          onClick={() => setOpen(allOpen ? new Set() : new Set(answered.map((t) => t.index)))}
        >
          {allOpen ? "Collapse all" : "Expand all"}
        </button>
      </div>
      <ul className="divide-y divide-line">
        {answered.map((t) => {
          const isOpen = open.has(t.index);
          const verdict = t.evaluation ? VERDICT[t.evaluation.verdict] : null;
          return (
            <li key={t.index}>
              <button
                className="flex w-full items-center gap-3 px-5 py-3.5 text-left hover:bg-canvas"
                onClick={() => toggle(t.index)}
                aria-expanded={isOpen}
              >
                <span className="w-7 font-mono text-xs text-faint">Q{t.number}</span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-medium text-ink">{t.topic}</span>
                  <span className="block truncate text-xs text-muted">{t.domain}</span>
                </span>
                <LevelBadge level={t.difficulty} />
                <span className="hidden w-36 justify-end sm:flex">
                  {verdict ? <Badge tone={verdict.tone}>{verdict.label}</Badge> : <Badge>Skipped</Badge>}
                </span>
                <span className="w-12 text-right text-sm">
                  <Score value={t.evaluation?.score ?? (t.skipped ? 0 : null)} outOf={10} />
                </span>
                <ChevronDown className={cn("size-4 text-faint transition-transform", isOpen && "rotate-180")} aria-hidden />
              </button>
              {isOpen && <TurnDetail turn={t} />}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
