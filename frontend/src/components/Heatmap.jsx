const colorFor = (pct) => {
  if (pct >= 95) return 'bg-emerald-500/80'
  if (pct >= 85) return 'bg-emerald-400/70'
  if (pct >= 75) return 'bg-lime-400/60'
  if (pct >= 65) return 'bg-amber-400/60'
  if (pct >= 50) return 'bg-orange-500/60'
  return 'bg-rose-500/65'
}

export default function Heatmap({ data }) {
  // Expect [{date:'YYYY-MM-DD', percent:number}] sorted by date.
  const days = (data || []).slice(-84) // ~12 weeks
  const boxes = days.map((d) => ({
    ...d,
    pct: typeof d.percent === 'number' ? d.percent : 0,
  }))

  return (
    <div className="overflow-x-auto">
      <div className="grid grid-flow-col auto-cols-max gap-2">
        {boxes.map((d) => (
          <div key={d.date} className="flex flex-col items-center gap-1">
            <div
              title={`${d.date}: ${d.pct.toFixed(0)}%`}
              className={[
                'h-4 w-4 rounded-sm border border-white/10',
                colorFor(d.pct),
                'transition hover:scale-110',
              ].join(' ')}
            />
          </div>
        ))}
      </div>
      <div className="mt-3 text-xs text-slate-300/80 dark:text-slate-300/80">
        GitHub-style attendance intensity (last ~12 weeks).
      </div>
    </div>
  )
}

