interface SourceBadgeProps {
  source: string;
}

const STYLES: Record<string, string> = {
  live: "bg-teal-50 text-teal-700 border-teal-200",
  dataset: "bg-amber-50 text-amber-700 border-amber-200",
  estimate: "bg-amber-50 text-amber-700 border-amber-200",
  unavailable: "bg-slate-100 text-slate-500 border-slate-200",
};

const LABELS: Record<string, string> = {
  live: "Live data",
  dataset: "Local dataset",
  estimate: "Estimated",
  unavailable: "Unavailable",
};

export function SourceBadge({ source }: SourceBadgeProps) {
  const key = source.toLowerCase();
  const style = STYLES[key] ?? STYLES.unavailable;
  const label = LABELS[key] ?? source;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide ${style}`}
    >
      <span
        className="h-1.5 w-1.5 rounded-full bg-current"
        aria-hidden="true"
      />
      {label}
    </span>
  );
}
