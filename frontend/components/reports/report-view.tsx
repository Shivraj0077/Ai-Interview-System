import { AlertOctagon, ArrowRight, CheckCircle2, CircleAlert, Info, ShieldCheck } from "lucide-react";
import type { InterviewDetail, Report } from "@/lib/types";
import { duration, formatDate, scoreTone } from "@/lib/format";
import { Card, CardHeader, cn } from "../ui";
import { LevelBadge } from "../badges";
import { DifficultyChart } from "./difficulty-chart";
import { QuestionReview } from "./question-review";

const BAR = { good: "bg-good", warn: "bg-[#dc6803]", bad: "bg-bad", none: "bg-faint" };
const TEXT = { good: "text-good", warn: "text-warn", bad: "text-bad", none: "text-faint" };

const DIMENSIONS: { key: keyof Report["dimensions"]; label: string; help: string }[] = [
  { key: "technical_knowledge", label: "Technical knowledge", help: "Average question score (skipped questions count as 0)." },
  { key: "conceptual_depth", label: "Conceptual depth", help: "Share of each topic's core signals covered, plus advanced signals." },
  { key: "communication", label: "Communication", help: "Evaluator's clarity rating for each answer." },
];

function Bar({ value }: { value: number | null }) {
  const tone = scoreTone(value);
  return (
    <div className="h-2 overflow-hidden rounded-full bg-ink/[0.06]">
      <div className={cn("h-full rounded-full", BAR[tone])} style={{ width: `${value ?? 0}%` }} />
    </div>
  );
}

export function ReportView({ interview }: { interview: InterviewDetail }) {
  const report = interview.report!;
  const tone = scoreTone(report.overall);
  const took = duration(interview.started_at, interview.finished_at);

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
        <Card className="flex flex-col justify-between p-6">
          <div>
            <p className="text-sm text-muted">Overall score</p>
            <p className={cn("mt-2 text-5xl font-semibold tabular-nums", TEXT[tone])}>
              {report.overall ?? "—"}
              <span className="text-xl font-normal text-faint"> / 100</span>
            </p>
            <p className={cn("mt-2 text-sm font-medium", TEXT[tone])}>{report.band}</p>
          </div>
          <dl className="mt-6 grid grid-cols-2 gap-3 border-t border-line pt-4 text-sm">
            <div>
              <dt className="text-xs text-muted">Answered</dt>
              <dd className="font-medium tabular-nums text-ink">
                {report.questions_answered}/{report.questions_planned}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-muted">Peak level</dt>
              <dd>{report.peak_difficulty ? <LevelBadge level={report.peak_difficulty} long /> : "—"}</dd>
            </div>
            {took && (
              <div>
                <dt className="text-xs text-muted">Duration</dt>
                <dd className="font-medium text-ink">{took}</dd>
              </div>
            )}
            {interview.finished_at && (
              <div>
                <dt className="text-xs text-muted">Completed</dt>
                <dd className="font-medium text-ink">{formatDate(interview.finished_at)}</dd>
              </div>
            )}
          </dl>
        </Card>

        <Card className="p-6">
          <p className="text-sm font-semibold text-ink">Scores by dimension</p>
          <div className="mt-5 space-y-5">
            {DIMENSIONS.map((d) => (
              <div key={d.key}>
                <div className="mb-1.5 flex items-baseline justify-between gap-4">
                  <span className="text-sm font-medium text-ink-2">{d.label}</span>
                  <span className={cn("text-sm font-semibold tabular-nums", TEXT[scoreTone(report.dimensions[d.key])])}>
                    {report.dimensions[d.key] ?? "—"}
                  </span>
                </div>
                <Bar value={report.dimensions[d.key]} />
                <p className="mt-1 text-xs text-faint">{d.help}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Adaptive path */}
      <Card>
        <CardHeader
          title="Difficulty progression"
          description={
            interview.config.difficulty_mode === "adaptive"
              ? "Level of each question. Score 8+ moves up a level, 4 or below moves down."
              : `Fixed at ${interview.config.start_difficulty} for this interview.`
          }
          action={
            <div className="hidden items-center gap-1.5 sm:flex">
              {report.difficulty_progression.map((l, i) => (
                <span key={i} className="flex items-center gap-1.5">
                  {i > 0 && <ArrowRight className="size-3 text-faint" aria-hidden />}
                  <LevelBadge level={l} />
                </span>
              ))}
            </div>
          }
        />
        <div className="px-5 py-4">
          <DifficultyChart turns={interview.turns} />
        </div>
      </Card>

      {/* Strengths / improvements */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader title="Strengths" />
          <ul className="space-y-3 p-5">
            {report.strengths.length === 0 && <li className="text-sm text-muted">No answers scored 7 or above.</li>}
            {report.strengths.map((s, i) => (
              <li key={i} className="flex gap-3">
                <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-good" aria-hidden />
                <div>
                  <p className="text-sm font-medium text-ink">{s.title}</p>
                  <p className="text-sm text-muted">{s.detail}</p>
                </div>
              </li>
            ))}
          </ul>
        </Card>
        <Card>
          <CardHeader title="Areas to improve" />
          <ul className="space-y-3 p-5">
            {report.improvements.length === 0 && <li className="text-sm text-muted">No significant gaps found.</li>}
            {report.improvements.map((s, i) => (
              <li key={i} className="flex gap-3">
                <CircleAlert className="mt-0.5 size-4 shrink-0 text-warn" aria-hidden />
                <div>
                  <p className="text-sm font-medium text-ink">{s.title}</p>
                  <p className="text-sm text-muted">{s.detail}</p>
                </div>
              </li>
            ))}
            {report.misconceptions.length > 0 && (
              <li className="rounded-lg border border-warn/20 bg-warn-soft p-3">
                <p className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-warn">
                  <AlertOctagon className="size-3.5" aria-hidden /> Misconceptions detected
                </p>
                <ul className="mt-1.5 list-disc space-y-0.5 pl-5 text-sm text-ink-2">
                  {report.misconceptions.map((m) => (
                    <li key={m}>{m}</li>
                  ))}
                </ul>
              </li>
            )}
          </ul>
        </Card>
      </div>

      {/* Coverage */}
      <Card>
        <CardHeader title="Technical coverage" description="Average score for questions in each area." />
        <ul className="space-y-4 p-5">
          {report.coverage.map((c) => (
            <li key={c.domain} className="grid grid-cols-[minmax(0,160px)_1fr_48px] items-center gap-4 sm:grid-cols-[220px_1fr_60px]">
              <span className="truncate text-sm text-ink-2">
                {c.label}
                <span className="ml-1.5 text-xs text-faint">
                  {c.questions} Q
                </span>
              </span>
              <Bar value={c.score} />
              <span className={cn("text-right text-sm font-semibold tabular-nums", TEXT[scoreTone(c.score)])}>{c.score}%</span>
            </li>
          ))}
        </ul>
      </Card>

      {/* Questions */}
      <Card>
        <CardHeader title="Question review" description="Expand a question to see exactly which signals the answer covered or missed." />
        <QuestionReview turns={interview.turns} />
      </Card>

      {/* Methodology */}
      <Card className="p-5">
        <div className="flex items-start gap-3">
          <ShieldCheck className="mt-0.5 size-5 shrink-0 text-brand" aria-hidden />
          <div className="text-sm">
            <p className="font-semibold text-ink">How this report was produced</p>
            <p className="mt-1 max-w-3xl leading-relaxed text-muted">
              Each answer was scored by {interview.engine?.provider ?? "the LLM"} · {interview.engine?.model ?? ""} against the
              core signals, advanced signals and known misconceptions of the concept it was asked about, retrieved from a
              curated knowledge base. A verification step removed{" "}
              <span className="font-medium text-ink-2">{report.grounding.ungrounded_claims_removed}</span> cited signal
              {report.grounding.ungrounded_claims_removed === 1 ? "" : "s"} that didn&apos;t exist in the source
              {report.grounding.scores_capped > 0 && (
                <>
                  {" "}
                  and lowered <span className="font-medium text-ink-2">{report.grounding.scores_capped}</span> score
                  {report.grounding.scores_capped === 1 ? "" : "s"} that the verified evidence didn&apos;t support
                </>
              )}
              . This summary is computed directly from those evaluations; no additional model call writes it.
            </p>
            {report.grounding.catalog_fallbacks > 0 && (
              <p className="mt-2 flex items-center gap-1.5 text-xs text-muted">
                <Info className="size-3.5" aria-hidden />
                {report.grounding.catalog_fallbacks} question
                {report.grounding.catalog_fallbacks === 1 ? " was" : "s were"} selected without semantic search because
                vector retrieval was unavailable.
              </p>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}
