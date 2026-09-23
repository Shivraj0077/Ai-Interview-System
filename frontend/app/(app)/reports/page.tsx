"use client";

import Link from "next/link";
import { FileBarChart2 } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import { formatDate } from "@/lib/format";
import { SampleBadge, Score } from "@/components/badges";
import { DemoButton } from "@/components/demo-button";
import { TableSkeleton } from "@/components/dashboard/interview-table";
import { Card, EmptyState, ErrorState, PageHeader } from "@/components/ui";

export default function ReportsPage() {
  const { data, error, loading, reload } = useApi(api.listInterviews);
  const reports = (data ?? []).filter((i) => i.status === "completed");

  return (
    <>
      <PageHeader title="Reports" description="Evaluation reports for completed interviews." />
      {loading ? (
        <Card>
          <TableSkeleton />
        </Card>
      ) : error ? (
        <Card>
          <ErrorState message={errorMessage(error)} onRetry={reload} />
        </Card>
      ) : reports.length === 0 ? (
        <Card>
          <EmptyState
            icon={<FileBarChart2 className="size-5" />}
            title="No reports yet"
            description="Reports appear here once an interview is finished."
            action={<DemoButton size="sm" />}
          />
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {reports.map((r) => (
            <Link key={r.id} href={`/interviews/${r.id}`} className="group">
              <Card className="h-full p-5 transition-shadow group-hover:shadow-md">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate font-semibold text-ink">{r.role}</p>
                    <p className="mt-0.5 flex items-center gap-2 text-sm text-muted">
                      {r.candidate_name} {r.is_sample && <SampleBadge />}
                    </p>
                  </div>
                  <Score value={r.overall} className="text-2xl" />
                </div>
                <p className="mt-4 text-xs text-faint">
                  {r.num_questions} questions · {formatDate(r.updated_at)}
                </p>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
