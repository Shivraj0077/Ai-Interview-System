"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { PlayCircle } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import { Button } from "./ui";
import { useToast } from "./ui/toast";

/** Creates a preconfigured demo interview and opens the interview room. */
export function DemoButton({
  label = "Try demo interview",
  variant = "primary",
  size = "md",
  className,
}: {
  label?: string;
  variant?: "primary" | "secondary";
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  const router = useRouter();
  const toast = useToast();
  const [loading, setLoading] = useState(false);

  async function start() {
    setLoading(true);
    try {
      const interview = await api.createDemo();
      router.push(`/interview/${interview.id}`);
    } catch (err) {
      toast(errorMessage(err), "error");
      setLoading(false);
    }
  }

  return (
    <Button variant={variant} size={size} className={className} onClick={start} loading={loading}>
      {!loading && <PlayCircle className="size-4" aria-hidden />}
      {label}
    </Button>
  );
}
