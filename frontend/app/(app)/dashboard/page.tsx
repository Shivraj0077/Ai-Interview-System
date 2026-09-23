"use client";

import Link from "next/link";
import { ArrowRight, ListChecks, Plus } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import { DemoButton } from "@/components/demo-button";
import { InterviewTable, TableSkeleton } from "@/components/dashboard/interview-table";
import { ButtonLink, Card, CardHeader, EmptyState, ErrorState, PageHeader, Skeleton } from "@/components/ui";

function Stat({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <Card className="p-5">
      <p className="text-sm text-muted">{label}</p>
      <p className="mt-2 text-2xl font-semibold tabular-nums text-ink">{value}</p>
      {hint && <p className="mt-1 text-xs text-faint">{hint}</p>}
    </Card>
  );
}

export default function DashboardPage() {
  const { data, error, loading, reload } = useApi(api.listInterviews);
  const interviews = data ?? [];
  const completed = interviews.filter((i) => i.status === "completed");
  const scored = completed.filter((i) => i.overall !== null);
  const avg = scored.length ? Math.round(scored.reduce((s, i) => s + (i.overall ?? 0), 0) / scored.length) : null;
  const live = interviews.filter((i) => !i.is_sample);

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Technical interviews you've created, plus sample interviews to explore the reports."
        action={
          <ButtonLink href="/interviews/new">
            <Plus className="size-4" aria-hidden /> Create interview
          </ButtonLink>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <Card key={i} className="space-y-3 p-5">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-7 w-12" />
            </Card>
          ))
        ) : (
          <>
            <Stat label="Interviews" value={interviews.length} hint={`${live.length} created by you`} />
            <Stat label="Completed" value={completed.length} />
            <Stat label="In progress" value={interviews.filter((i) => i.status === "in_progress").length} />
            <Stat label="Average score" value={avg ?? "—"} hint="Across completed interviews" />
          </>
        )}
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_300px]">
        <Card>
          <CardHeader
            title="Recent interviews"
            action={
              <Link href="/interviews" className="flex items-center gap-1 text-sm font-medium text-brand hover:text-brand-strong">
                View all <ArrowRight className="size-3.5" aria-hidden />
              </Link>
            }
          />
          {loading ? (
            <TableSkeleton />
          ) : error ? (
            <ErrorState message={errorMessage(error)} onRetry={reload} />
          ) : interviews.length === 0 ? (
            <EmptyState
              icon={<ListChecks className="size-5" />}
              title="No interviews yet"
              description="Create an interview or run the demo to see results here."
            />
          ) : (
            <InterviewTable interviews={interviews.slice(0, 6)} />
          )}
        </Card>

        <div className="space-y-4">
          <Card className="p-5">
            <p className="text-sm font-semibold text-ink">Try it as a candidate</p>
            <p className="mt-1 text-sm text-muted">
              A 5-question Backend Engineer interview on the live engine. You&apos;ll get the full report at the end.
            </p>
            <DemoButton className="mt-4 w-full" label="Start demo interview" />
          </Card>
          <Card className="p-5">
            <p className="text-sm font-semibold text-ink">About sample data</p>
            <p className="mt-1 text-sm text-muted">
              Interviews marked <span className="font-medium text-warn">Sample</span> are pre-generated with fictional
              candidates so the dashboard isn&apos;t empty. They use real knowledge-base concepts and the same scoring
              pipeline, and are read-only.
            </p>
          </Card>
        </div>
      </div>
    </>
  );
}
