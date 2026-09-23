"use client";

import Link from "next/link";
import { ArrowLeft, Copy, ExternalLink, FileText } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import type { InterviewDetail as Detail } from "@/lib/types";
import { formatDate } from "@/lib/format";
import { LevelBadge, SampleBadge, StatusBadge } from "../badges";
import { Button, ButtonLink, Card, CardHeader, ErrorState, Skeleton } from "../ui";
import { useToast } from "../ui/toast";
import { DifficultyChart } from "./difficulty-chart";
import { QuestionReview } from "./question-review";
import { ReportView } from "./report-view";

function ConfigCard({ interview }: { interview: Detail }) {
  const c = interview.config;
  return (
    <Card>
      <CardHeader title="Configuration" />
      <dl className="grid gap-4 p-5 text-sm sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <dt className="text-xs text-muted">Questions</dt>
          <dd className="mt-0.5 font-medium text-ink">{c.num_questions}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted">Difficulty</dt>
          <dd className="mt-0.5 flex items-center gap-1.5 font-medium text-ink">
            {c.difficulty_mode === "adaptive" ? "Adaptive from" : "Fixed"} <LevelBadge level={c.start_difficulty} />
          </dd>
        </div>
        <div className="sm:col-span-2">
          <dt className="text-xs text-muted">Focus areas</dt>
          <dd className="mt-0.5 font-medium text-ink">{c.focus_areas.map((f) => f.label).join(", ") || "All areas"}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted">Job description</dt>
          <dd className="mt-0.5 font-medium text-ink">{c.has_job_description ? "Provided" : "None"}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted">Resume</dt>
          <dd className="mt-0.5 flex items-center gap-1.5 font-medium text-ink">
            {c.resume_filename ? (
              <>
                <FileText className="size-3.5 text-muted" aria-hidden />
                {c.resume_filename}
              </>
            ) : (
              "None"
            )}
          </dd>
        </div>
      </dl>
    </Card>
  );
}

function InviteCard({ interview }: { interview: Detail }) {
  const toast = useToast();
  const path = `/interview/${interview.id}`;

  async function copy() {
    try {
      await navigator.clipboard.writeText(`${window.location.origin}${path}`);
      toast("Interview link copied");
    } catch {
      toast("Couldn't copy. Select the link and copy it manually.", "error");
    }
  }

  return (
    <Card className="p-6">
      <p className="font-semibold text-ink">Ready for the candidate</p>
      <p className="mt-1 text-sm text-muted">
        Share this link with {interview.candidate_name}. For the demo, you can open it and take the interview yourself.
      </p>
      <div className="mt-4 flex flex-col gap-2 sm:flex-row">
        <code className="flex-1 truncate rounded-lg border border-line bg-canvas px-3 py-2.5 font-mono text-sm text-ink-2">
          {typeof window !== "undefined" ? window.location.origin : ""}
          {path}
        </code>
        <Button variant="secondary" onClick={copy}>
          <Copy className="size-4" aria-hidden /> Copy
        </Button>
        <ButtonLink href={path}>
          Open interview <ExternalLink className="size-4" aria-hidden />
        </ButtonLink>
      </div>
    </Card>
  );
}

function DetailSkeleton() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-8 w-72" />
      </div>
      <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
        <Skeleton className="h-56 rounded-xl" />
        <Skeleton className="h-56 rounded-xl" />
      </div>
      <Skeleton className="h-40 rounded-xl" />
    </div>
  );
}

export function InterviewDetail({ id }: { id: string }) {
  const { data: interview, error, loading, reload } = useApi(() => api.getInterview(id), id);

  if (loading) return <DetailSkeleton />;
  if (error || !interview)
    return (
      <Card>
        <ErrorState message={errorMessage(error)} onRetry={reload} />
      </Card>
    );

  const answered = interview.turns.filter((t) => t.answered).length;

  return (
    <>
      <Link href="/interviews" className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted hover:text-ink">
        <ArrowLeft className="size-4" aria-hidden /> Interviews
      </Link>

      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={interview.status} />
            {interview.is_sample && <SampleBadge />}
          </div>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight text-ink">{interview.candidate_name}</h1>
          <p className="mt-0.5 text-muted">
            {interview.role} · Created {formatDate(interview.created_at)}
          </p>
        </div>
        {interview.engine && (
          <p className="text-xs text-faint">
            {interview.engine.provider} · {interview.engine.model}
            {interview.engine.vector_store && ` · ${interview.engine.vector_store}`}
          </p>
        )}
      </div>

      {interview.is_sample && (
        <p className="mb-6 rounded-lg border border-warn/20 bg-warn-soft px-4 py-3 text-sm text-ink-2">
          This is sample data with a fictional candidate, generated with real knowledge-base concepts and the same scoring
          pipeline as live interviews.
        </p>
      )}

      {interview.status === "completed" && interview.report ? (
        <ReportView interview={interview} />
      ) : (
        <div className="space-y-6">
          {interview.status === "created" && <InviteCard interview={interview} />}
          {interview.status === "in_progress" && (
            <Card className="flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="font-semibold text-ink">Interview in progress</p>
                <p className="mt-1 text-sm text-muted">
                  {answered} of {interview.config.num_questions} questions answered. The full report is generated when the interview
                  finishes.
                </p>
              </div>
              {!interview.is_sample && (
                <ButtonLink href={`/interview/${interview.id}`} variant="secondary">
                  Resume as candidate <ExternalLink className="size-4" aria-hidden />
                </ButtonLink>
              )}
            </Card>
          )}
          <ConfigCard interview={interview} />
          {answered > 0 && (
            <>
              <Card>
                <CardHeader title="Difficulty so far" />
                <div className="px-5 py-4">
                  <DifficultyChart turns={interview.turns} />
                </div>
              </Card>
              <Card>
                <CardHeader title="Answered questions" description="Evaluations are visible to you, not the candidate." />
                <QuestionReview turns={interview.turns} />
              </Card>
            </>
          )}
        </div>
      )}
    </>
  );
}
