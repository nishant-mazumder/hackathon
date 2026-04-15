export default function GlassCard({ title, right, children, className }) {
  return (
    <section
      className={[
        'rounded-2xl border border-slate-900/10 bg-white/70 text-slate-900 backdrop-blur-xl shadow-xl shadow-black/10',
        'dark:border-white/10 dark:bg-white/5 dark:text-slate-100',
        'p-4 md:p-5',
        className || '',
      ].join(' ')}
    >
      {(title || right) && (
        <div className="flex items-center justify-between gap-3 mb-3">
          <div className="font-medium">{title}</div>
          {right}
        </div>
      )}
      {children}
    </section>
  )
}

