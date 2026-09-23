import Link from "next/link";
import {
  ArrowRight,
  Check,
  FileSearch,
  Gauge,
  GitBranch,
  ListChecks,
  ScanSearch,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  X,
} from "lucide-react";
import { DemoButton } from "@/components/demo-button";
import { Logo } from "@/components/logo";
import { LevelBadge } from "@/components/badges";
import { ButtonLink } from "@/components/ui";

const REPO_URL = "https://github.com/Shivraj0077/Ai-Interview-System";

const FEATURES = [
  {
    icon: TrendingUp,
    title: "Adaptive difficulty",
    body: "Every answer moves the interview. Score 8+ and the next question steps up a level; 4 or below and it steps down.",
  },
  {
    icon: FileSearch,
    title: "Role, JD and resume context",
    body: "Focus areas filter the knowledge base, and the job description and resume steer which concepts are retrieved first.",
  },
  {
    icon: ShieldCheck,
    title: "Grounded evaluation",
    body: "Answers are scored only against curated signals for that concept. Citations the model invents are stripped out.",
  },
  {
    icon: ListChecks,
    title: "Structured reports",
    body: "Scores by dimension, topic coverage, difficulty path, and a question-by-question review of what was covered or missed.",
  },
];

const PIPELINE = [
  { icon: ScanSearch, title: "Retrieve", body: "pgvector semantic search picks an unused concept at the current level, within the focus areas." },
  { icon: Sparkles, title: "Ask", body: "An open-weight LLM on Groq writes one question grounded in that concept, probing gaps from the previous answer." },
  { icon: Gauge, title: "Evaluate", body: "The answer is scored against the concept's core signals, advanced signals and known misconceptions." },
  { icon: ShieldCheck, title: "Verify", body: "Any cited signal not in the source is removed, and the score is capped at what the evidence supports." },
  { icon: GitBranch, title: "Adapt", body: "Difficulty moves up or down based on the score, and the loop repeats." },
];

function ReportPreview() {
  const dims = [
    ["Technical knowledge", 82],
    ["Conceptual depth", 76],
    ["Communication", 84],
  ] as const;
  return (
    <div className="relative">
      <div className="absolute -inset-4 -z-10 rounded-3xl bg-gradient-to-br from-brand/10 via-transparent to-sky-200/30 blur-2xl" aria-hidden />
      <div className="rounded-2xl border border-line bg-surface p-5 shadow-xl shadow-ink/5">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-faint">Candidate evaluation</p>
            <p className="mt-1 font-semibold text-ink">Backend Engineer</p>
          </div>
          <div className="text-right">
            <p className="text-3xl font-semibold tabular-nums text-good">82</p>
            <p className="text-xs text-muted">Strong performance</p>
          </div>
        </div>

        <div className="mt-5 space-y-3">
          {dims.map(([label, value]) => (
            <div key={label}>
              <div className="mb-1 flex justify-between text-xs">
                <span className="text-ink-2">{label}</span>
                <span className="tabular-nums text-muted">{value}</span>
              </div>
              <div className="h-1.5 rounded-full bg-ink/5">
                <div className="h-full rounded-full bg-brand" style={{ width: `${value}%` }} />
              </div>
            </div>
          ))}
        </div>

        <div className="mt-5 flex items-center gap-1.5 text-xs text-muted">
          <span className="mr-1">Difficulty</span>
          {(["L1", "L2", "L3", "L3", "L2"] as const).map((l, i) => (
            <span key={i} className="flex items-center gap-1.5">
              {i > 0 && <ArrowRight className="size-3 text-faint" aria-hidden />}
              <LevelBadge level={l} />
            </span>
          ))}
        </div>

        <div className="mt-5 rounded-lg border border-line bg-canvas p-3">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium text-ink">Q3 · Exactly-once vs at-least-once</span>
            <span className="font-semibold tabular-nums text-warn">5/10</span>
          </div>
          <div className="mt-2 flex flex-wrap gap-1.5 text-xs">
            {["Message duplication", "ACK mechanisms"].map((s) => (
              <span key={s} className="inline-flex items-center gap-1 rounded bg-good-soft px-1.5 py-0.5 text-good">
                <Check className="size-3" aria-hidden />
                {s}
              </span>
            ))}
            {["Consumer side-effects"].map((s) => (
              <span key={s} className="inline-flex items-center gap-1 rounded bg-bad-soft px-1.5 py-0.5 text-bad">
                <X className="size-3" aria-hidden />
                {s}
              </span>
            ))}
          </div>
        </div>
        <p className="mt-3 text-center text-[11px] text-faint">Illustrative example</p>
      </div>
    </div>
  );
}

export default function Landing() {
  return (
    <div className="bg-surface">
      <header className="border-b border-line">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Logo />
          <nav className="flex items-center gap-1 sm:gap-2">
            <Link href="/dashboard" className="hidden rounded-lg px-3 py-2 text-sm font-medium text-ink-2 hover:bg-ink/5 sm:block">
              Dashboard
            </Link>
            <a href={REPO_URL} className="hidden rounded-lg px-3 py-2 text-sm font-medium text-ink-2 hover:bg-ink/5 sm:block">
              Source
            </a>
            <ButtonLink href="/interviews/new" variant="secondary" size="sm">
              Create interview
            </ButtonLink>
          </nav>
        </div>
      </header>

      <section className="mx-auto grid max-w-6xl items-center gap-12 px-4 py-16 sm:px-6 lg:grid-cols-[1.1fr_1fr] lg:py-24">
        <div>
          <p className="inline-flex items-center gap-2 rounded-full border border-line bg-canvas px-3 py-1 text-xs font-medium text-ink-2">
            <span className="size-1.5 rounded-full bg-brand" aria-hidden />
            Adaptive · RAG-grounded · Structured reports
          </p>
          <h1 className="mt-5 text-4xl font-semibold leading-[1.1] tracking-tight text-ink sm:text-5xl">
            Run structured technical interviews with an adaptive AI interviewer.
          </h1>
          <p className="mt-5 max-w-xl text-lg leading-relaxed text-muted">
            Configure a role and focus areas, let the candidate answer in a real interview flow, and get an evaluation
            report where every score traces back to a specific, verified signal.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <DemoButton size="lg" label="Try demo interview" />
            <ButtonLink href="/interviews/new" variant="secondary" size="lg">
              Create interview <ArrowRight className="size-4" aria-hidden />
            </ButtonLink>
          </div>
          <p className="mt-4 text-sm text-faint">
            No sign-up. The demo runs the live AI engine: 5 questions, about 5 minutes.
          </p>
        </div>
        <ReportPreview />
      </section>

      <section className="border-y border-line bg-canvas">
        <dl className="mx-auto grid max-w-6xl grid-cols-2 gap-6 px-4 py-8 sm:px-6 md:grid-cols-4">
          {[
            ["127", "curated concepts"],
            ["12", "technical domains"],
            ["3", "difficulty levels"],
            ["2", "model calls per question"],
          ].map(([value, label]) => (
            <div key={label}>
              <dt className="sr-only">{label}</dt>
              <dd className="text-2xl font-semibold tabular-nums text-ink">{value}</dd>
              <dd className="text-sm text-muted">{label}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
        <h2 className="text-2xl font-semibold tracking-tight text-ink">What the recruiter gets</h2>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map(({ icon: Icon, title, body }) => (
            <div key={title} className="rounded-xl border border-line p-5">
              <Icon className="size-5 text-brand" aria-hidden />
              <h3 className="mt-4 font-semibold text-ink">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-t border-line bg-canvas">
        <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
          <h2 className="text-2xl font-semibold tracking-tight text-ink">How each question works</h2>
          <p className="mt-2 max-w-2xl text-muted">
            One retrieval, one generation and one evaluation per question. The report is computed from stored
            evaluations, with no extra model calls.
          </p>
          <ol className="mt-10 grid gap-4 md:grid-cols-5">
            {PIPELINE.map(({ icon: Icon, title, body }, i) => (
              <li key={title} className="relative rounded-xl border border-line bg-surface p-5">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs text-faint">0{i + 1}</span>
                  <Icon className="size-4 text-brand" aria-hidden />
                </div>
                <h3 className="mt-3 font-semibold text-ink">{title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-muted">{body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-20 text-center sm:px-6">
        <h2 className="text-2xl font-semibold tracking-tight text-ink">See it adapt to your answers</h2>
        <p className="mx-auto mt-2 max-w-lg text-muted">
          Answer well and watch the questions get harder. Then open the report the recruiter would see.
        </p>
        <div className="mt-6 flex justify-center gap-3">
          <DemoButton size="lg" />
          <ButtonLink href="/dashboard" variant="secondary" size="lg">
            View sample reports
          </ButtonLink>
        </div>
      </section>

      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-6 text-sm text-muted sm:flex-row sm:justify-between sm:px-6">
          <p>
            An end-to-end AI technical interviewing system, built as a full-stack engineering project. Not a commercial
            product.
          </p>
          <p>Groq · gpt-oss-120b · Gemini embeddings · Supabase pgvector</p>
        </div>
      </footer>
    </div>
  );
}
