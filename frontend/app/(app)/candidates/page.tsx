"use client";

import Link from "next/link";
import { Users } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import type { InterviewSummary } from "@/lib/types";
import { relativeTime } from "@/lib/format";
import { SampleBadge, Score, StatusBadge } from "@/components/badges";
import { interviewHref, TableSkeleton } from "@/components/dashboard/interview-table";
import { Card, EmptyState, ErrorState, PageHeader } from "@/components/ui";

function initials(name: string) {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join("");
}

export default function CandidatesPage() {
  const { data, error, loading, reload } = useApi(api.listInterviews);

  const groups = new Map<string, InterviewSummary[]>();
  for (const i of data ?? []) {
    groups.set(i.candidate_name, [...(groups.get(i.candidate_name) ?? []), i]);
  }

  return (
    <>
      <PageHeader title="Candidates" description="Everyone who has been invited to an interview, grouped by name." />
      {loading ? (
        <Card>
          <TableSkeleton />
        </Card>
      ) : error ? (
        <Card>
          <ErrorState message={errorMessage(error)} onRetry={reload} />
        </Card>
      ) : groups.size === 0 ? (
        <Card>
          <EmptyState icon={<Users className="size-5" />} title="No candidates yet" />
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {[...groups.entries()].map(([name, interviews]) => (
            <Card key={name} className="p-5">
              <div className="flex items-center gap-3">
                <span className="grid size-10 place-items-center rounded-full bg-brand-soft text-sm font-semibold text-brand-strong">
                  {initials(name)}
                </span>
                <div className="min-w-0">
                  <p className="flex items-center gap-2 font-semibold text-ink">
                    {name} {interviews.some((i) => i.is_sample) && <SampleBadge />}
                  </p>
                  <p className="text-sm text-muted">
                    {interviews.length} interview{interviews.length > 1 ? "s" : ""}
                  </p>
                </div>
              </div>
              <ul className="mt-4 divide-y divide-line rounded-lg border border-line">
                {interviews.map((i) => (
                  <li key={i.id}>
                    <Link href={interviewHref(i)} className="flex items-center gap-3 px-3 py-2.5 text-sm hover:bg-canvas">
                      <span className="min-w-0 flex-1 truncate font-medium text-ink-2">{i.role}</span>
                      <StatusBadge status={i.status} />
                      <span className="w-8 text-right">
                        <Score value={i.overall} />
                      </span>
                      <span className="hidden w-16 text-right text-xs text-faint sm:block">{relativeTime(i.updated_at)}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            </Card>
          ))}
        </div>
      )}
    </>
  );
}
