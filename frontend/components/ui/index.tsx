import Link from "next/link";
import type { ComponentProps, ReactNode } from "react";
import { AlertTriangle, Loader2, RotateCw } from "lucide-react";

export function cn(...classes: (string | false | null | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

/* ---------- Button ---------- */

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

const VARIANTS: Record<Variant, string> = {
  primary: "bg-brand text-white hover:bg-brand-strong shadow-sm disabled:bg-brand/50",
  secondary: "bg-surface text-ink-2 border border-line-strong hover:bg-canvas shadow-sm disabled:text-faint",
  ghost: "text-ink-2 hover:bg-ink/5 disabled:text-faint",
  danger: "bg-surface text-bad border border-line-strong hover:bg-bad-soft disabled:text-faint",
};
const SIZES: Record<Size, string> = {
  sm: "h-8 px-3 text-sm gap-1.5",
  md: "h-10 px-4 text-sm gap-2",
  lg: "h-12 px-5 text-base gap-2",
};

function buttonClass(variant: Variant, size: Size, className?: string) {
  return cn(
    "inline-flex items-center justify-center rounded-lg font-medium transition-colors whitespace-nowrap disabled:cursor-not-allowed",
    VARIANTS[variant],
    SIZES[size],
    className,
  );
}

export function Button({
  variant = "primary",
  size = "md",
  loading,
  className,
  children,
  disabled,
  ...props
}: ComponentProps<"button"> & { variant?: Variant; size?: Size; loading?: boolean }) {
  return (
    <button className={buttonClass(variant, size, className)} disabled={disabled || loading} {...props}>
      {loading && <Loader2 className="size-4 animate-spin" aria-hidden />}
      {children}
    </button>
  );
}

export function ButtonLink({
  variant = "primary",
  size = "md",
  className,
  ...props
}: ComponentProps<typeof Link> & { variant?: Variant; size?: Size }) {
  return <Link className={buttonClass(variant, size, className)} {...props} />;
}

/* ---------- Surfaces ---------- */

export function Card({ className, ...props }: ComponentProps<"div">) {
  return <div className={cn("rounded-xl border border-line bg-surface shadow-[0_1px_2px_rgba(16,24,40,0.04)]", className)} {...props} />;
}

export function CardHeader({ title, description, action }: { title: ReactNode; description?: ReactNode; action?: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-line px-5 py-4">
      <div>
        <h2 className="text-sm font-semibold text-ink">{title}</h2>
        {description && <p className="mt-0.5 text-sm text-muted">{description}</p>}
      </div>
      {action}
    </div>
  );
}

export function PageHeader({ title, description, action }: { title: ReactNode; description?: ReactNode; action?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-ink">{title}</h1>
        {description && <p className="mt-1 text-sm text-muted">{description}</p>}
      </div>
      {action}
    </div>
  );
}

/* ---------- Badges ---------- */

type Tone = "neutral" | "brand" | "good" | "warn" | "bad";
const TONES: Record<Tone, string> = {
  neutral: "bg-ink/5 text-ink-2 ring-ink/10",
  brand: "bg-brand-soft text-brand-strong ring-brand/20",
  good: "bg-good-soft text-good ring-good/20",
  warn: "bg-warn-soft text-warn ring-warn/20",
  bad: "bg-bad-soft text-bad ring-bad/20",
};

export function Badge({ tone = "neutral", className, ...props }: ComponentProps<"span"> & { tone?: Tone }) {
  return (
    <span
      className={cn("inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset", TONES[tone], className)}
      {...props}
    />
  );
}

/* ---------- Loading / empty / error ---------- */

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cn("size-5 animate-spin text-muted", className)} aria-label="Loading" />;
}

export function Skeleton({ className }: { className?: string }) {
  return (
    <div className={cn("relative overflow-hidden rounded-md bg-ink/[0.06]", className)}>
      <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.4s_infinite] bg-gradient-to-r from-transparent via-white/60 to-transparent" />
    </div>
  );
}

export function EmptyState({ icon, title, description, action }: { icon?: ReactNode; title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center px-6 py-14 text-center">
      {icon && <div className="mb-3 rounded-full bg-ink/5 p-3 text-muted">{icon}</div>}
      <p className="text-sm font-semibold text-ink">{title}</p>
      {description && <p className="mt-1 max-w-sm text-sm text-muted">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function ErrorState({ message, onRetry, retrying }: { message: string; onRetry?: () => void; retrying?: boolean }) {
  return (
    <div role="alert" className="flex flex-col items-center px-6 py-12 text-center">
      <div className="mb-3 rounded-full bg-bad-soft p-3 text-bad">
        <AlertTriangle className="size-5" aria-hidden />
      </div>
      <p className="text-sm font-semibold text-ink">Couldn&apos;t load this</p>
      <p className="mt-1 max-w-md text-sm text-muted">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" className="mt-4" onClick={onRetry} loading={retrying}>
          <RotateCw className="size-3.5" aria-hidden /> Try again
        </Button>
      )}
    </div>
  );
}

export function InlineError({ children, action }: { children: ReactNode; action?: ReactNode }) {
  return (
    <div role="alert" className="flex items-start gap-3 rounded-lg border border-bad/20 bg-bad-soft px-4 py-3 text-sm text-bad">
      <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden />
      <div className="flex-1">{children}</div>
      {action}
    </div>
  );
}

/* ---------- Form fields ---------- */

export function Field({
  label,
  hint,
  htmlFor,
  optional,
  children,
}: {
  label: string;
  hint?: ReactNode;
  htmlFor?: string;
  optional?: boolean;
  children: ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={htmlFor} className="flex items-baseline gap-2 text-sm font-medium text-ink-2">
        {label}
        {optional && <span className="text-xs font-normal text-faint">Optional</span>}
      </label>
      {children}
      {hint && <p className="text-xs text-muted">{hint}</p>}
    </div>
  );
}

const inputBase =
  "w-full rounded-lg border border-line-strong bg-surface px-3 text-sm text-ink shadow-sm placeholder:text-faint focus:border-brand focus:outline-none focus:ring-4 focus:ring-brand/10 disabled:bg-canvas";

export function Input({ className, ...props }: ComponentProps<"input">) {
  return <input className={cn(inputBase, "h-10", className)} {...props} />;
}

export function Textarea({ className, ...props }: ComponentProps<"textarea">) {
  return <textarea className={cn(inputBase, "py-2.5 leading-relaxed", className)} {...props} />;
}

export function Select({ className, ...props }: ComponentProps<"select">) {
  return <select className={cn(inputBase, "h-10 pr-8", className)} {...props} />;
}
