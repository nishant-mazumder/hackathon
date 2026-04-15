import { useEffect, useMemo, useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import GlassCard from '../components/GlassCard.jsx'
import { getJson, postJson } from '../lib/api.js'

const cx = (...xs) => xs.filter(Boolean).join(' ')

export default function AdminDashboard() {
  const [filters, setFilters] = useState({ branch: '', semester: '', subject: '' })
  const [data, setData] = useState(null)
  const [query, setQuery] = useState('Show students with attendance below 60% in Sem 3')
  const [chatResult, setChatResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const qs = useMemo(() => {
    const p = new URLSearchParams()
    if (filters.branch) p.set('branch', filters.branch)
    if (filters.semester) p.set('semester', filters.semester)
    if (filters.subject) p.set('subject', filters.subject)
    const s = p.toString()
    return s ? `?${s}` : ''
  }, [filters])

  useEffect(() => {
    setLoading(true)
    setError('')
    getJson(`/admin/analytics/${qs}`)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [qs])

  const runChat = async () => {
    setError('')
    try {
      const res = await postJson('/admin/chat-query/', { query })
      setChatResult(res)
    } catch (e) {
      setError(e.message)
    }
  }

  const deptChart = (data?.department_stats || []).map((r) => ({
    branch: r.student__branch,
    avg: Number(r.avg_cgpa || 0).toFixed ? Number(r.avg_cgpa).toFixed(2) : r.avg_cgpa,
  }))

  return (
    <div className="space-y-4">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <div className="text-sm text-slate-600 dark:text-slate-300/80">Admin Dashboard</div>
          <div className="text-2xl font-semibold">Oversight & Risk Detection</div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={filters.branch}
            onChange={(e) => setFilters((f) => ({ ...f, branch: e.target.value }))}
            className="px-3 py-2 rounded-xl border border-slate-900/10 bg-white/70 text-slate-900 text-sm
                       dark:border-white/10 dark:bg-white/5 dark:text-slate-100"
          >
            <option value="" className="bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-100">All branches</option>
            <option value="CS" className="bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-100">CS</option>
            <option value="IT" className="bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-100">IT</option>
            <option value="Mechanical" className="bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-100">Mechanical</option>
          </select>
          <select
            value={filters.semester}
            onChange={(e) => setFilters((f) => ({ ...f, semester: e.target.value }))}
            className="px-3 py-2 rounded-xl border border-slate-900/10 bg-white/70 text-slate-900 text-sm
                       dark:border-white/10 dark:bg-white/5 dark:text-slate-100"
          >
            <option value="" className="bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-100">All semesters</option>
            {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
              <option key={s} value={String(s)} className="bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-100">
                Sem {s}
              </option>
            ))}
          </select>
          <input
            value={filters.subject}
            onChange={(e) => setFilters((f) => ({ ...f, subject: e.target.value }))}
            placeholder="Subject filter (optional)"
            className="px-3 py-2 rounded-xl border border-slate-900/10 bg-white/70 text-slate-900 text-sm placeholder:text-slate-500
                       dark:border-white/10 dark:bg-white/5 dark:text-slate-100 dark:placeholder:text-slate-400"
          />
        </div>
      </div>

      {error && (
        <div className="rounded-2xl border border-rose-600/25 bg-rose-500/10 p-4 text-sm text-rose-900 dark:text-rose-100">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <GlassCard title="Department Analytics (Avg CGPA)" className="lg:col-span-2">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={deptChart}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.35)" />
                <XAxis dataKey="branch" stroke="rgba(100,116,139,0.9)" />
                <YAxis domain={[0, 10]} stroke="rgba(100,116,139,0.9)" />
                <Tooltip />
                <Bar dataKey="avg" fill="rgba(99,102,241,0.75)" radius={[10, 10, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        <GlassCard title="Top Students">
          {loading && <div className="text-sm text-slate-600 dark:text-slate-300/80">Loading…</div>}
          <div className="space-y-2">
            {(data?.top_students || []).slice(0, 10).map((s) => (
              <div
                key={`${s.student_id}`}
                className="rounded-xl border border-slate-900/10 bg-white/60 p-3
                           dark:border-white/10 dark:bg-white/5"
              >
                <div className="text-sm font-medium">{s.student__name}</div>
                <div className="text-xs text-slate-600 dark:text-slate-300/80">
                  {s.student__branch} • Sem {s.student__semester}
                </div>
                <div className="mt-1 text-sm">Avg CGPA: {Number(s.best_cgpa).toFixed(2)}</div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <GlassCard title="At-risk students">
          <div className="space-y-2">
            {(data?.at_risk_students || []).map((s) => (
              <div
                key={s.id}
                className={cx(
                  'rounded-2xl border p-4 transition',
                  'border-white/10 bg-white/5 hover:bg-white/10'
                )}
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-medium">{s.name}</div>
                  <div className="text-xs text-slate-600 dark:text-slate-300/80">
                    {s.branch} • Sem {s.semester}{s.division}
                  </div>
                </div>
                <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-slate-700 dark:text-slate-200/80">
                  <div className="rounded-xl border border-slate-900/10 bg-white/60 p-2 dark:border-white/10 dark:bg-white/5">
                    Attendance: {s.attendance_percent.toFixed(1)}%
                  </div>
                  <div className="rounded-xl border border-slate-900/10 bg-white/60 p-2 dark:border-white/10 dark:bg-white/5">
                    Health: {s.health_score}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>

        <GlassCard title="Chat query interface (simple NLP)">
          <div className="text-sm text-slate-700 dark:text-slate-200/80">
            Example: <span className="font-mono">Show students with attendance below 60% in Sem 3</span>
          </div>
          <div className="mt-3 flex gap-2">
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex-1 px-3 py-2 rounded-xl border border-slate-900/10 bg-white/70 text-slate-900 text-sm placeholder:text-slate-500
                         dark:border-white/10 dark:bg-white/5 dark:text-slate-100 dark:placeholder:text-slate-400"
            />
            <button
              onClick={runChat}
              className="px-3 py-2 rounded-xl bg-fuchsia-500/80 hover:bg-fuchsia-500 transition text-sm"
            >
              Run
            </button>
          </div>

          {chatResult && (
            <div className="mt-4 space-y-2">
              <div className="text-xs text-slate-600 dark:text-slate-300/80">
                Parsed: <span className="font-mono">{JSON.stringify(chatResult.parsed)}</span>
              </div>
              <div className="text-sm">Results (showing {Math.min(chatResult.results.length, 50)}):</div>
              <div className="max-h-72 overflow-auto space-y-2 pr-2">
                {chatResult.results.map((r) => (
                  <div
                    key={r.id}
                    className="rounded-xl border border-slate-900/10 bg-white/60 p-3
                               dark:border-white/10 dark:bg-white/5"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-medium">{r.name}</div>
                      <div className="text-xs text-slate-600 dark:text-slate-300/80">{r.attendance_percent.toFixed(1)}%</div>
                    </div>
                    <div className="text-xs text-slate-600 dark:text-slate-300/80">
                      {r.branch} • Sem {r.semester}{r.division}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </GlassCard>
      </div>

      <GlassCard title="Subject difficulty (low attendance subjects)">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {(data?.subject_difficulty || []).map((s) => (
            <div
              key={s.subject}
              className="rounded-xl border border-slate-900/10 bg-white/60 p-3
                         dark:border-white/10 dark:bg-white/5"
            >
              <div className="text-sm font-medium">{s.subject}</div>
              <div className="text-xs text-slate-600 dark:text-slate-300/80">
                Avg attendance: {s.attendance_percent.toFixed(1)}%
              </div>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  )
}

