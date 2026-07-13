export function SectionTitle({ eyebrow, title, description, badge }) {
  return (
    <div className="section-title flex items-end justify-between gap-6">
      <div>
        {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
        <h1>{title}</h1>
        {description ? <p>{description}</p> : null}
      </div>
      {badge ? <span className="chip chip-sage">{badge}</span> : null}
    </div>
  );
}

export function ConfidenceChip({ score, level = "high" }) {
  const className = level === "high" ? "chip chip-sage" : level === "medium" ? "chip chip-warning" : "chip chip-danger";
  const label = level === "high" ? "高置信" : level === "medium" ? "中置信" : "低置信";
  return <span className={className}>{label} {score}</span>;
}

export function Panel({ title, meta, children }) {
  return (
    <section className="panel">
      <div className="panel-head">
        <h3 className="text-sm font-semibold">{title}</h3>
        {meta ? <span className="text-xs text-[color:var(--muted)]">{meta}</span> : null}
      </div>
      <div className="panel-body">{children}</div>
    </section>
  );
}
