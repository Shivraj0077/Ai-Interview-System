"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowRight, CheckCircle2, Clock, Flag, Lock, MessageSquareText, RotateCw, SkipForward } from "lucide-react";
import { api, ApiError, errorMessage } from "@/lib/api";
import type { Session } from "@/lib/types";
import { LevelBadge } from "../badges";
import { Logo } from "../logo";
import { Button, ButtonLink, Card, cn, ErrorState, InlineError, Skeleton, Spinner, Textarea } from "../ui";

const MAX_CHARS = 4000;

/* ---------- small pieces ---------- */

function useElapsed(startIso: string | null) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);
  if (!startIso) return "00:00";
  const s = Math.max(0, Math.floor((now - new Date(startIso).getTime()) / 1000));
  const mm = String(Math.floor(s / 60)).padStart(2, "0");
  const ss = String(s % 60).padStart(2, "0");
  return s >= 3600 ? `${Math.floor(s / 3600)}:${mm.slice(-2)}:${ss}` : `${mm}:${ss}`;
}

function draftKey(id: string, index: number) {
  return `answer-draft:${id}:${index}`;
}
function readDraft(key: string) {
  try {
    return sessionStorage.getItem(key) ?? "";
  } catch {
    return "";
  }
}
function writeDraft(key: string, value: string) {
  try {
    if (value) sessionStorage.setItem(key, value);
    else sessionStorage.removeItem(key);
  } catch {
    // storage unavailable (private mode); drafts just won't survive a refresh
  }
}

function RoomFrame({ session, children, footer }: { session?: Session | null; children: React.ReactNode; footer?: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex h-14 max-w-4xl items-center justify-between gap-4 px-4 sm:px-6">
          <Logo href="/" />
          {session && <span className="truncate text-sm text-muted">{session.role}</span>}
        </div>
      </header>
      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col px-4 py-8 sm:px-6">{children}</main>
      {footer}
    </div>
  );
}

function EvaluatingPanel({ phase }: { phase: "evaluating" | "next" | "starting" | "finishing" }) {
  const label = {
    starting: "Preparing your first question…",
    evaluating: "Evaluating your answer…",
    next: "Preparing the next question…",
    finishing: "Finishing interview…",
  }[phase];
  return (
    <div className="flex flex-col items-center py-16 text-center" role="status" aria-live="polite">
      <div className="h-1 w-56 overflow-hidden rounded-full bg-ink/10">
        <div className="h-full w-2/5 animate-[progress-indeterminate_1.2s_ease-in-out_infinite] rounded-full bg-brand" />
      </div>
      <p className="mt-5 text-sm font-medium text-ink">{label}</p>
      <p className="mt-1 text-xs text-muted">
        {phase === "evaluating" || phase === "next"
          ? "Scoring against this topic's grounded signals, then choosing what to ask next."
          : "Retrieving a concept from the knowledge base."}
      </p>
    </div>
  );
}

/* ---------- screens ---------- */

function Lobby({ session, onStart, starting, error }: { session: Session; onStart: () => void; starting: boolean; error: string | null }) {
  return (
    <Card className="mx-auto w-full max-w-2xl p-6 sm:p-8">
      <p className="text-sm font-medium text-brand">Technical interview</p>
      <h1 className="mt-1 text-2xl font-semibold tracking-tight text-ink">{session.role}</h1>
      <p className="mt-1 text-muted">Hi {session.candidate_name}, here&apos;s how this works.</p>

      <ul className="mt-6 space-y-4 text-sm">
        {[
          [MessageSquareText, `${session.num_questions} conceptual questions, answered in writing. Explain your reasoning as you would out loud.`],
          [ArrowRight, "Questions adapt: strong answers lead to harder questions, weaker ones to more fundamental ones."],
          [Lock, "You won't see scores during the interview. The full evaluation is available when you finish."],
          [Clock, "There's no hard time limit. Most people take about a minute per question."],
        ].map(([Icon, text], i) => {
          const I = Icon as typeof Clock;
          return (
            <li key={i} className="flex gap-3">
              <I className="mt-0.5 size-4 shrink-0 text-muted" aria-hidden />
              <span className="text-ink-2">{text as string}</span>
            </li>
          );
        })}
      </ul>

      {error && (
        <div className="mt-6">
          <InlineError>{error}</InlineError>
        </div>
      )}

      <Button size="lg" className="mt-8 w-full sm:w-auto" onClick={onStart} loading={starting}>
        {error ? "Try again" : "Start interview"}
      </Button>
    </Card>
  );
}

function Complete({ session }: { session: Session }) {
  return (
    <Card className="mx-auto w-full max-w-xl p-8 text-center">
      <CheckCircle2 className="mx-auto size-10 text-good" aria-hidden />
      <h1 className="mt-4 text-2xl font-semibold tracking-tight text-ink">Interview complete</h1>
      <p className="mt-2 text-muted">
        Thanks, {session.candidate_name}. You answered {session.answered} of {session.num_questions} questions.
      </p>
      <p className="mt-1 text-sm text-faint">
        In a real hiring process only the recruiter would see this. In the demo, you can open it yourself.
      </p>
      <ButtonLink href={`/interviews/${session.id}`} size="lg" className="mt-6">
        View evaluation report <ArrowRight className="size-4" aria-hidden />
      </ButtonLink>
    </Card>
  );
}

/* ---------- main ---------- */

type Busy = null | "starting" | "evaluating" | "next" | "finishing" | "skipping" | "retrying";

export function InterviewRoom({ id }: { id: string }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loadError, setLoadError] = useState<unknown>(null);
  const [busy, setBusy] = useState<Busy>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [draft, setDraft] = useState<{ index: number; text: string } | null>(null);
  const [confirmFinish, setConfirmFinish] = useState(false);
  const autoRetried = useRef(false);

  const q = session?.current_question ?? null;
  const elapsed = useElapsed(session?.started_at ?? null);

  const fetchSession = useCallback(() => api.session(id).then(setSession, setLoadError), [id]);
  const load = useCallback(() => {
    setLoadError(null);
    fetchSession();
  }, [fetchSession]);

  useEffect(() => {
    fetchSession();
  }, [fetchSession]);

  // The answer for the open question; falls back to an unsent draft saved before a refresh.
  const answer = q ? (draft?.index === q.index ? draft.text : readDraft(draftKey(id, q.index))) : "";

  const apply = useCallback(
    (next: Session) => {
      setSession(next);
      setActionError(next.question_error?.message ?? null);
    },
    [],
  );

  const prepareQuestion = useCallback(async () => {
    setBusy("retrying");
    setActionError(null);
    try {
      apply(await api.prepareQuestion(id));
    } catch (err) {
      setActionError(errorMessage(err));
    } finally {
      setBusy(null);
    }
  }, [apply, id]);

  // In progress but no open question (refresh after a failed generation): prepare one once automatically.
  useEffect(() => {
    if (session?.status === "in_progress" && !session.current_question && !busy && !autoRetried.current && !session.question_error) {
      autoRetried.current = true;
      prepareQuestion();
    }
  }, [session, busy, prepareQuestion]);

  async function start() {
    setBusy("starting");
    setActionError(null);
    try {
      apply(await api.start(id));
    } catch (err) {
      setActionError(errorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  async function submit() {
    if (!q || !answer.trim() || busy) return;
    setBusy("evaluating");
    setActionError(null);
    const phase = setTimeout(() => setBusy((b) => (b === "evaluating" ? "next" : b)), 2500);
    try {
      const next = await api.answer(id, q.index, answer);
      writeDraft(draftKey(id, q.index), "");
      apply(next);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      // Stale question (answered in another tab): reload the real state instead of showing an error.
      if (err instanceof ApiError && err.status === 409) load();
      else setActionError(errorMessage(err));
    } finally {
      clearTimeout(phase);
      setBusy(null);
    }
  }

  async function skip() {
    if (!q || busy) return;
    setBusy("skipping");
    setActionError(null);
    try {
      writeDraft(draftKey(id, q.index), "");
      apply(await api.skip(id, q.index));
    } catch (err) {
      setActionError(errorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  async function finish() {
    setBusy("finishing");
    setConfirmFinish(false);
    try {
      apply(await api.finish(id));
    } catch (err) {
      setActionError(errorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  /* ----- render ----- */

  if (loadError) {
    return (
      <RoomFrame>
        <Card>
          <ErrorState message={errorMessage(loadError)} onRetry={load} />
        </Card>
      </RoomFrame>
    );
  }

  if (!session) {
    return (
      <RoomFrame>
        <Card className="mx-auto w-full max-w-2xl space-y-4 p-8">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-7 w-64" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
        </Card>
      </RoomFrame>
    );
  }

  if (session.is_sample) {
    return (
      <RoomFrame session={session}>
        <Card className="mx-auto max-w-xl p-8 text-center">
          <p className="font-semibold text-ink">This is a read-only sample interview.</p>
          <p className="mt-1 text-sm text-muted">Start the demo to try the live interview engine.</p>
          <div className="mt-5 flex justify-center gap-3">
            <ButtonLink href={`/interviews/${session.id}`} variant="secondary">
              View sample report
            </ButtonLink>
            <ButtonLink href="/">Back to home</ButtonLink>
          </div>
        </Card>
      </RoomFrame>
    );
  }

  if (session.status === "completed") {
    return (
      <RoomFrame session={session}>
        <Complete session={session} />
      </RoomFrame>
    );
  }

  if (session.status === "created") {
    return (
      <RoomFrame session={session}>
        {busy === "starting" ? (
          <Card className="mx-auto w-full max-w-2xl">
            <EvaluatingPanel phase="starting" />
          </Card>
        ) : (
          <Lobby session={session} onStart={start} starting={false} error={actionError} />
        )}
      </RoomFrame>
    );
  }

  const progress = (session.answered / session.num_questions) * 100;
  const showWorking = busy === "evaluating" || busy === "next" || busy === "finishing";

  return (
    <RoomFrame
      session={session}
      footer={
        <footer className="border-t border-line bg-surface">
          <div className="mx-auto flex max-w-4xl flex-wrap items-center justify-between gap-2 px-4 py-3 text-xs text-muted sm:px-6">
            <span className="flex items-center gap-3">
              {q && !showWorking && (
                <>
                  <span>
                    Topic: <span className="font-medium text-ink-2">{q.domain}</span>
                  </span>
                  <span className="flex items-center gap-1.5">
                    Difficulty: <LevelBadge level={q.difficulty} long />
                  </span>
                </>
              )}
            </span>
            {session.engine && (
              <span>
                AI engine: {session.engine.provider} · {session.engine.model}
              </span>
            )}
          </div>
        </footer>
      }
    >
      {/* status bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between gap-4 text-sm">
          <span className="font-medium text-ink">
            Question {Math.min(session.answered + 1, session.num_questions)} <span className="text-muted">of {session.num_questions}</span>
          </span>
          <span className="flex items-center gap-4">
            <span className="flex items-center gap-1.5 tabular-nums text-muted" aria-label="Elapsed time">
              <Clock className="size-3.5" aria-hidden /> {elapsed}
            </span>
            <Button variant="ghost" size="sm" onClick={() => setConfirmFinish(true)} disabled={!!busy}>
              <Flag className="size-3.5" aria-hidden /> Finish
            </Button>
          </span>
        </div>
        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-ink/10" role="progressbar" aria-valuenow={session.answered} aria-valuemin={0} aria-valuemax={session.num_questions}>
          <div className="h-full rounded-full bg-brand transition-[width] duration-500" style={{ width: `${progress}%` }} />
        </div>
      </div>

      {confirmFinish && (
        <Card className="mb-6 flex flex-col gap-3 border-warn/30 bg-warn-soft p-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-ink-2">
            End the interview now? {session.answered} answered question{session.answered === 1 ? "" : "s"} will be evaluated; the rest are dropped.
          </p>
          <div className="flex shrink-0 gap-2">
            <Button variant="secondary" size="sm" onClick={() => setConfirmFinish(false)}>
              Keep going
            </Button>
            <Button size="sm" onClick={finish} disabled={session.answered === 0}>
              Finish interview
            </Button>
          </div>
        </Card>
      )}

      <Card className="flex-1">
        {showWorking ? (
          <EvaluatingPanel phase={busy as "evaluating" | "next" | "finishing"} />
        ) : !q ? (
          <div className="flex flex-col items-center px-6 py-16 text-center">
            {busy === "retrying" ? (
              <>
                <Spinner />
                <p className="mt-3 text-sm text-muted">Preparing the next question…</p>
              </>
            ) : (
              <>
                <p className="font-medium text-ink">Your answer was saved, but the next question couldn&apos;t be prepared.</p>
                <p className="mt-1 max-w-md text-sm text-muted">{actionError ?? "The AI service didn't respond."}</p>
                <Button variant="secondary" className="mt-5" onClick={prepareQuestion}>
                  <RotateCw className="size-4" aria-hidden /> Try again
                </Button>
              </>
            )}
          </div>
        ) : (
          <div className="p-5 sm:p-8">
            <div className="flex items-start gap-4">
              <div className="grid size-9 shrink-0 place-items-center rounded-full bg-ink text-xs font-semibold text-white" aria-hidden>
                AI
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium uppercase tracking-wide text-faint">Interviewer</p>
                <p className="mt-2 text-lg leading-relaxed text-ink sm:text-xl">{q.text}</p>
              </div>
            </div>

            <div className="mt-8">
              <label htmlFor="answer" className="sr-only">
                Your answer
              </label>
              <Textarea
                id="answer"
                autoFocus
                rows={8}
                maxLength={MAX_CHARS}
                value={answer}
                onChange={(e) => {
                  setDraft({ index: q.index, text: e.target.value });
                  writeDraft(draftKey(id, q.index), e.target.value);
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit();
                }}
                placeholder="Type your answer…"
                disabled={!!busy}
                className="text-[15px]"
              />
              <div className="mt-1.5 flex justify-between text-xs text-faint">
                <span className="hidden sm:inline">Ctrl + Enter to submit</span>
                <span className={cn("tabular-nums", answer.length > MAX_CHARS * 0.9 && "text-warn")}>
                  {answer.length}/{MAX_CHARS}
                </span>
              </div>
            </div>

            {actionError && (
              <div className="mt-4">
                <InlineError
                  action={
                    <button className="font-medium underline underline-offset-2" onClick={submit}>
                      Retry
                    </button>
                  }
                >
                  {actionError} Your answer is still here.
                </InlineError>
              </div>
            )}

            <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-between">
              <Button variant="ghost" onClick={skip} loading={busy === "skipping"} disabled={!!busy}>
                {busy !== "skipping" && <SkipForward className="size-4" aria-hidden />} Skip question
              </Button>
              <Button size="lg" onClick={submit} disabled={!answer.trim() || !!busy}>
                Submit answer
              </Button>
            </div>
          </div>
        )}
      </Card>

      {session.answered > 0 && !showWorking && (
        <p className="mt-4 text-center text-xs text-faint">
          {session.answered} answered · scores are revealed in the final report
        </p>
      )}
    </RoomFrame>
  );
}
