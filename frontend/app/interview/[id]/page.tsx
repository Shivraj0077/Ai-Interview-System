import type { Metadata } from "next";
import { InterviewRoom } from "@/components/interview/interview-room";

export const metadata: Metadata = { title: "Interview" };

export default async function InterviewPage(props: PageProps<"/interview/[id]">) {
  const { id } = await props.params;
  return <InterviewRoom id={id} />;
}
