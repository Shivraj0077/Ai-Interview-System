"use client";

import { useRef, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Check, FileText, Info, Upload, Wand2, X } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import type { FocusArea, Level } from "@/lib/types";
import {
  Button,
  Card,
  CardHeader,
  cn,
  ErrorState,
  Field,
  InlineError,
  Input,
  PageHeader,
  Select,
  Skeleton,
  Textarea,
} from "@/components/ui";

const DIFFICULTY_OPTIONS = [
  { value: "adaptive:L1", label: "Adaptive, starting at L1 (recommended)" },
  { value: "adaptive:L2", label: "Adaptive, starting at L2" },
  { value: "fixed:L1", label: "Fixed at L1 · Foundational" },
  { value: "fixed:L2", label: "Fixed at L2 · Intermediate" },
  { value: "fixed:L3", label: "Fixed at L3 · Advanced" },
];

const EXAMPLE = {
  candidate_name: "Jordan Lee",
  role: "Backend Engineer Intern",
  focus_areas: ["backend", "database", "distributed_systems"],
  job_description:
    "Backend Engineer Intern for our payments team. You'll build REST APIs in Python, design PostgreSQL schemas and indexes, and help make our event-driven services reliable with retries, idempotency and message queues.",
};

function FocusAreaPicker({
  areas,
  selected,
  onToggle,
}: {
  areas: FocusArea[];
  selected: string[];
  onToggle: (id: string) => void;
}) {
  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {areas.map((a) => {
        const on = selected.includes(a.id);
        const total = a.concepts.L1 + a.concepts.L2 + a.concepts.L3;
        return (
          <button
            type="button"
            key={a.id}
            onClick={() => onToggle(a.id)}
            aria-pressed={on}
            className={cn(
              "flex items-center gap-3 rounded-lg border px-3 py-2.5 text-left transition-colors",
              on ? "border-brand bg-brand-soft/60 ring-1 ring-brand" : "border-line-strong bg-surface hover:bg-canvas",
            )}
          >
            <span
              className={cn(
                "grid size-4 shrink-0 place-items-center rounded border",
                on ? "border-brand bg-brand text-white" : "border-line-strong",
              )}
            >
              {on && <Check className="size-3" strokeWidth={3} aria-hidden />}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-sm font-medium text-ink">{a.label}</span>
              <span className="block text-xs text-muted">
                {total} concepts · {(["L1", "L2", "L3"] as Level[]).filter((l) => a.concepts[l] > 0).join(" / ")}
              </span>
            </span>
          </button>
        );
      })}
    </div>
  );
}

export default function NewInterviewPage() {
  const router = useRouter();
  const meta = useApi(api.meta);
  const fileInput = useRef<HTMLInputElement>(null);

  const [candidateName, setCandidateName] = useState("");
  const [role, setRole] = useState("");
  const [difficulty, setDifficulty] = useState(DIFFICULTY_OPTIONS[0].value);
  const [numQuestions, setNumQuestions] = useState(6);
  const [focus, setFocus] = useState<string[]>([]);
  const [jd, setJd] = useState("");
  const [resumeText, setResumeText] = useState("");
  const [resumeFile, setResumeFile] = useState<string | null>(null);

  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const [mode, startLevel] = difficulty.split(":") as ["adaptive" | "fixed", Level];
  const selectedAreas = meta.data?.focus_areas.filter((a) => focus.includes(a.id)) ?? [];
  const missingL3 = mode === "adaptive" && selectedAreas.length > 0 && selectedAreas.every((a) => a.concepts.L3 === 0);
  const fixedMissing =
    mode === "fixed" && selectedAreas.length > 0 && selectedAreas.every((a) => a.concepts[startLevel] === 0);

  function toggle(id: string) {
    setFocus((f) => (f.includes(id) ? f.filter((x) => x !== id) : [...f, id]));
  }

  function fillExample() {
    setCandidateName(EXAMPLE.candidate_name);
    setRole(EXAMPLE.role);
    setFocus(EXAMPLE.focus_areas);
    setJd(EXAMPLE.job_description);
  }

  async function onUpload(file: File | undefined) {
    if (!file) return;
    setUploadError(null);
    setUploading(true);
    try {
      const res = await api.parseResume(file);
      setResumeText(res.text);
      setResumeFile(res.filename);
    } catch (err) {
      setUploadError(errorMessage(err));
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitError(null);
    setSubmitting(true);
    try {
      const interview = await api.createInterview({
        candidate_name: candidateName,
        role,
        difficulty_mode: mode,
        start_difficulty: startLevel,
        num_questions: numQuestions,
        focus_areas: focus,
        job_description: jd,
        resume_text: resumeText,
        resume_filename: resumeText ? resumeFile ?? "Pasted text" : null,
      });
      router.push(`/interviews/${interview.id}`);
    } catch (err) {
      setSubmitError(errorMessage(err));
      setSubmitting(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Create interview"
        description="Configure what to assess. The candidate gets a link to a live, adaptive interview."
        action={
          <Button type="button" variant="secondary" size="sm" onClick={fillExample}>
            <Wand2 className="size-4" aria-hidden /> Fill with example
          </Button>
        }
      />

      <form onSubmit={onSubmit} className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <div className="space-y-6">
          <Card>
            <CardHeader title="Role" />
            <div className="grid gap-5 p-5 sm:grid-cols-2">
              <Field label="Role" htmlFor="role">
                <Input id="role" required maxLength={80} value={role} onChange={(e) => setRole(e.target.value)} placeholder="Backend Engineer Intern" />
              </Field>
              <Field label="Candidate name" htmlFor="candidate">
                <Input id="candidate" required maxLength={80} value={candidateName} onChange={(e) => setCandidateName(e.target.value)} placeholder="Jordan Lee" />
              </Field>
              <Field label="Interview type" hint="Conceptual questions answered in writing.">
                <Input value="Technical interview" disabled readOnly />
              </Field>
              <Field label="Number of questions" htmlFor="count" hint={`About ${numQuestions} minutes for the candidate.`}>
                <Select id="count" value={numQuestions} onChange={(e) => setNumQuestions(Number(e.target.value))}>
                  {[3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                    <option key={n} value={n}>
                      {n} questions
                    </option>
                  ))}
                </Select>
              </Field>
              <div className="sm:col-span-2">
                <Field
                  label="Difficulty"
                  htmlFor="difficulty"
                  hint={
                    mode === "adaptive"
                      ? "Steps up a level after a score of 8+, down after 4 or below."
                      : "Every question stays at this level."
                  }
                >
                  <Select id="difficulty" value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
                    {DIFFICULTY_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </Select>
                </Field>
              </div>
            </div>
          </Card>

          <Card>
            <CardHeader
              title="Focus areas"
              description="Questions are drawn only from these knowledge-base domains. Leave empty to use all of them."
            />
            <div className="p-5">
              {meta.loading ? (
                <div className="grid gap-2 sm:grid-cols-2">
                  {Array.from({ length: 8 }).map((_, i) => (
                    <Skeleton key={i} className="h-[58px]" />
                  ))}
                </div>
              ) : meta.error ? (
                <ErrorState message={errorMessage(meta.error)} onRetry={meta.reload} />
              ) : (
                <>
                  <FocusAreaPicker areas={meta.data!.focus_areas} selected={focus} onToggle={toggle} />
                  {(missingL3 || fixedMissing) && (
                    <p className="mt-3 flex items-start gap-2 text-xs text-muted">
                      <Info className="mt-0.5 size-3.5 shrink-0" aria-hidden />
                      {fixedMissing
                        ? `None of the selected areas have ${startLevel} concepts, so questions will come from other areas at ${startLevel}.`
                        : "None of the selected areas have L3 concepts. If the candidate reaches L3, questions will widen to other areas (L3 is Distributed Systems and Observability)."}
                    </p>
                  )}
                </>
              )}
            </div>
          </Card>

          <Card>
            <CardHeader title="Context" description="Used to steer which concepts are retrieved for the first question, and to frame questions around the role." />
            <div className="space-y-5 p-5">
              <Field label="Job description" htmlFor="jd" optional>
                <Textarea
                  id="jd"
                  rows={6}
                  maxLength={6000}
                  value={jd}
                  onChange={(e) => setJd(e.target.value)}
                  placeholder="Paste the job description…"
                />
              </Field>

              <Field
                label="Candidate resume"
                optional
                hint="PDF text is extracted on the server (no OCR). You can edit or paste the text directly."
              >
                <div className="flex flex-wrap items-center gap-3">
                  <input
                    ref={fileInput}
                    type="file"
                    accept="application/pdf,.pdf"
                    className="sr-only"
                    id="resume"
                    onChange={(e) => onUpload(e.target.files?.[0])}
                  />
                  <Button type="button" variant="secondary" size="sm" loading={uploading} onClick={() => fileInput.current?.click()}>
                    {!uploading && <Upload className="size-4" aria-hidden />}
                    {uploading ? "Reading PDF…" : "Upload PDF"}
                  </Button>
                  {resumeFile && (
                    <span className="inline-flex items-center gap-1.5 rounded-md bg-canvas px-2 py-1 text-sm text-ink-2 ring-1 ring-line">
                      <FileText className="size-3.5" aria-hidden />
                      {resumeFile}
                      <button
                        type="button"
                        aria-label="Remove resume"
                        className="text-faint hover:text-ink"
                        onClick={() => {
                          setResumeFile(null);
                          setResumeText("");
                        }}
                      >
                        <X className="size-3.5" />
                      </button>
                    </span>
                  )}
                </div>
                {uploadError && <p className="text-sm text-bad">{uploadError}</p>}
                <Textarea
                  rows={resumeText ? 5 : 3}
                  maxLength={8000}
                  value={resumeText}
                  onChange={(e) => setResumeText(e.target.value)}
                  placeholder="…or paste resume text"
                  aria-label="Resume text"
                />
              </Field>
            </div>
          </Card>
        </div>

        <div className="lg:sticky lg:top-8 lg:self-start">
          <Card className="p-5">
            <p className="text-sm font-semibold text-ink">Summary</p>
            <dl className="mt-4 space-y-3 text-sm">
              {[
                ["Role", role || "—"],
                ["Candidate", candidateName || "—"],
                ["Questions", numQuestions],
                ["Difficulty", mode === "adaptive" ? `Adaptive from ${startLevel}` : `Fixed ${startLevel}`],
                ["Focus", focus.length ? `${focus.length} area${focus.length > 1 ? "s" : ""}` : "All areas"],
                ["Context", [jd && "JD", resumeText && "Resume"].filter(Boolean).join(" + ") || "None"],
              ].map(([k, v]) => (
                <div key={k as string} className="flex justify-between gap-4">
                  <dt className="text-muted">{k}</dt>
                  <dd className="truncate text-right font-medium text-ink-2">{v}</dd>
                </div>
              ))}
            </dl>
            {submitError && (
              <div className="mt-4">
                <InlineError>{submitError}</InlineError>
              </div>
            )}
            <Button type="submit" className="mt-5 w-full" loading={submitting} disabled={!role.trim() || !candidateName.trim()}>
              Create interview
            </Button>
            <p className="mt-3 text-center text-xs text-faint">Nothing is sent to the candidate automatically.</p>
          </Card>
        </div>
      </form>
    </>
  );
}
