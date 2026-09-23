"use client";

import Link from "next/link";
import { ChevronRight } from "lucide-react";
import type { InterviewSummary } from "@/lib/types";
import { relativeTime } from "@/lib/format";
import { SampleBadge, Score, StatusBadge } from "../badges";
import { Skeleton } from "../ui";

export function interviewHref(i: InterviewSummary) {
  // Unstarted interviews open the candidate room; everything else opens the recruiter view.
  return i.status === "created" ? `/interview/${i.id}` : `/interviews/${i.id}`;
}

export function InterviewTable({ interviews }: { interviews: InterviewSummary[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-line text-left text-xs font-medium uppercase tracking-wide text-faint">
            <th className="px-5 py-2.5 font-medium">Role</th>
            <th className="px-3 py-2.5 font-medium">Candidate</th>
            <th className="px-3 py-2.5 font-medium">Status</th>
            <th className="hidden px-3 py-2.5 font-medium md:table-cell">Questions</th>
            <th className="px-3 py-2.5 text-right font-medium">Score</th>
            <th className="hidden px-3 py-2.5 font-medium sm:table-cell">Updated</th>
            <th className="w-8" />
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {interviews.map((i) => (
            <tr key={i.id} className="group relative hover:bg-canvas">
              <td className="px-5 py-3">
                <Link href={interviewHref(i)} className="font-medium text-ink after:absolute after:inset-0">
                  {i.role}
                </Link>
              </td>
              <td className="px-3 py-3 text-ink-2">
                <span className="flex items-center gap-2">
                  {i.candidate_name}
                  {i.is_sample && <SampleBadge />}
                </span>
              </td>
              <td className="px-3 py-3">
                <StatusBadge status={i.status} />
              </td>
              <td className="hidden px-3 py-3 tabular-nums text-muted md:table-cell">{i.num_questions}</td>
              <td className="px-3 py-3 text-right">
                <Score value={i.overall} />
              </td>
              <td className="hidden px-3 py-3 text-muted sm:table-cell">{relativeTime(i.updated_at)}</td>
              <td className="pr-4 text-faint group-hover:text-ink-2">
                <ChevronRight className="size-4" aria-hidden />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function TableSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="divide-y divide-line">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-6 px-5 py-4">
          <Skeleton className="h-4 w-40" />
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-5 w-20" />
          <Skeleton className="ml-auto h-4 w-8" />
        </div>
      ))}
    </div>
  );
}
