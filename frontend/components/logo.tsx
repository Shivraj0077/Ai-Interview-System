import Link from "next/link";

export function Logo({ href = "/" }: { href?: string }) {
  return (
    <Link href={href} className="flex items-center gap-2 font-semibold tracking-tight text-ink">
      <span className="grid size-7 place-items-center rounded-lg bg-ink text-white">
        <svg viewBox="0 0 24 24" className="size-4" fill="none" stroke="currentColor" strokeWidth="2.2" aria-hidden>
          <path d="M4 17l4-9 4 6 3-4 5 7" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>
      AI Interviewer
    </Link>
  );
}
