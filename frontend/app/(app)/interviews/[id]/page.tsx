import type { Metadata } from "next";
import { InterviewDetail } from "@/components/reports/interview-detail";

export const metadata: Metadata = { title: "Interview report" };

export default async function InterviewDetailPage(props: PageProps<"/interviews/[id]">) {
  const { id } = await props.params;
  return <InterviewDetail id={id} />;
}
