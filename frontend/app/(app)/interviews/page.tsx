"use client";

import { useState } from "react";
import { ListChecks, Plus } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import type { InterviewStatus } from "@/lib/types";
import { InterviewTable, TableSkeleton } from "@/components/dashboard/interview-table";
import { ButtonLink, Card, cn, EmptyState, ErrorState, PageHeader } from "@/components/ui";

const FILTERS: { id: "all" | InterviewStatus; label: string }[] = [
  { id: "all", label: "All" },
  { id: "in_progress", label: "In progress" },
  { id: "completed", label: "Completed" },
  { id: "created", label: "Not started" },
];

export default function InterviewsPage() {
  const { data, error, loading, reload } = useApi(api.listInterviews);
  const [filter, setFilter] = useState<(typeof FILTERS)[number]["id"]>("all");
  const rows = (data ?? []).filter((i) => filter === "all" || i.status === filter);

  return (
    <>
      <PageHeader
        title="Interviews"
        action={
          <ButtonLink href="/interviews/new">
            <Plus className="size-4" aria-hidden /> Create interview
          </ButtonLink>
        }
      />
      <Card>
        <div className="flex gap-1 overflow-x-auto border-b border-line px-3 py-2" role="tablist">
          {FILTERS.map((f) => (
            <button
              key={f.id}
              role="tab"
              aria-selected={filter === f.id}
              onClick={() => setFilter(f.id)}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium",
                filter === f.id ? "bg-ink/[0.06] text-ink" : "text-muted hover:text-ink",
              )}
            >
              {f.label}
              {data && (
                <span className="ml-1.5 tabular-nums text-faint">
                  {f.id === "all" ? data.length : data.filter((i) => i.status === f.id).length}
                </span>
              )}
            </button>
          ))}
        </div>
        {loading ? (
          <TableSkeleton rows={5} />
        ) : error ? (
          <ErrorState message={errorMessage(error)} onRetry={reload} />
        ) : rows.length === 0 ? (
          <EmptyState icon={<ListChecks className="size-5" />} title="Nothing here" description="No interviews match this filter." />
        ) : (
          <InterviewTable interviews={rows} />
        )}
      </Card>
    </>
  );
}
