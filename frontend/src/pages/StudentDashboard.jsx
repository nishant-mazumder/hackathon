import { useEffect, useMemo, useState } from 'react'
import { Line, LineChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import GlassCard from '../components/GlassCard.jsx'
import Heatmap from '../components/Heatmap.jsx'
import { downloadFile, getJson } from '../lib/api.js'

const pct = (n) => (typeof n === 'number' ? `${n.toFixed(1)}%` : '—')

function HealthPill({ label }) {
  const cls =
    label === 'Excellent'
      ? 'bg-emerald-500/15 text-emerald-800 border-emerald-600/25 dark:bg-emerald-500/20 dark:text-emerald-200 dark:border-emerald-400/30'
      : label === 'At Risk'
        ? 'bg-amber-500/15 text-amber-900 border-amber-600/25 dark:bg-amber-500/20 dark:text-amber-200 dark:border-amber-400/30'
        : 'bg-rose-500/15 text-rose-900 border-rose-600/25 dark:bg-rose-500/20 dark:text-rose-200 dark:border-rose-400/30'
  return <span className={`px-2 py-1 text-xs rounded-lg border ${cls}`}>{label}</span>
}

export default function StudentDashboard() {
  const [students, setStudents] = useState([])
  const [studentId, setStudentId] = useState(null)
  const [profile, setProfile] = useState(null)
  const [trend, setTrend] = useState([])
  const [heatmap, setHeatmap] = useState([])
  const [timeline, setTimeline] = useState([])
  const [pred, setPred] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [recoveryTarget, setRecoveryTarget] = useState(75)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let mounted = true
    getJson('/students/')
      .then((data) => {
        if (!mounted) return
        setStudents(data)
        if (data && data.length) setStudentId(data[0].id)
      })
      .catch((e) => setError(e.message))
    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    if (!studentId) return
    setLoading(true)
    setError('')
    Promise.all([
      getJson(`/students/${studentId}/`),
      getJson(`/students/${studentId}/grades/trend/`),
      getJson(`/students/${studentId}/attendance/heatmap/?days=120`),
      getJson(`/students/${studentId}/activities/timeline/?limit=30`),
      getJson(`/students/${studentId}/predict/`),
      getJson(`/students/${studentId}/alerts/`),
    ])
      .then(([p, t, h, a, pr, al]) => {
        setProfile(p)
        setTrend((t && t.trend) || [])
        setHeatmap((h && h.heatmap) || [])
        setTimeline((a && a.timeline) || [])
        setPred(pr)
        setAlerts((al && al.alerts) || [])
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [studentId])

  const recoverySim = useMemo(() => {
    const att = profile?.attendance
    if (!att || !att.total_classes) return null
    const attended = att.attended_classes
    const total = att.total_classes
    const target = recoveryTarget / 100
    const current = attended / total
    if (current >= target) return { needed: 0, message: 'Already at/above target.' }
    const x = Math.ceil((target * total - attended) / (1 - target))
    return { needed: x, message: `Attend next ${x} classes to reach ${recoveryTarget}%.` }
  }, [profile, recoveryTarget])

  return (
    <div className="space-y-4">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <div className="text-sm text-slate-600 dark:text-slate-300/80">Student Dashboard</div>
          <div className="text-2xl font-semibold">Analytics & Insights</div>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={studentId || ''}
            onChange={(e) => setStudentId(Number(e.target.value))}
            className="px-3 py-2 rounded-xl border border-slate-900/10 bg-white/70 text-slate-900 backdrop-blur text-sm
                       dark:border-white/10 dark:bg-white/5 dark:text-slate-100"
          >
            {students.map((s) => (
              <option key={s.id} value={s.id} className="bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-100">
                {s.name} • {s.branch} • Sem {s.semester}
              </option>
            ))}
          </select>
          <button
            onClick={() => downloadFile(`/students/${studentId}/report.pdf`, `CampusLedger_${studentId}.pdf`)}
            className="px-3 py-2 rounded-xl bg-indigo-500/80 hover:bg-indigo-500 transition text-sm"
          >
            Download PDF
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-2xl border border-rose-600/25 bg-rose-500/10 p-4 text-sm text-rose-900 dark:text-rose-100">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <GlassCard title="Health Score">
          <div className="flex items-end justify-between">
            <div>
              <div className="text-4xl font-semibold">{profile?.health?.score ?? '—'}</div>
              <div className="mt-1">{profile?.health?.label ? <HealthPill label={profile.health.label} /> : null}</div>
            </div>
            <div className="text-xs text-slate-600 dark:text-slate-300/80 text-right">
              Attendance: {pct(profile?.attendance?.percent)}
              <br />
              Predicted CGPA: {pred?.predicted_cgpa?.toFixed ? pred.predicted_cgpa.toFixed(2) : '—'} ({pred?.risk_level})
            </div>
          </div>
          <div className="mt-3 space-y-2 text-sm">
            <div className="text-slate-800 dark:text-slate-200/90">Reasons</div>
            <ul className="list-disc pl-5 text-slate-700 dark:text-slate-200/80">
              {(profile?.health?.reasons || []).slice(0, 4).map((r, idx) => (
                <li key={idx}>{r}</li>
              ))}
            </ul>
            <div className="text-slate-800 dark:text-slate-200/90">Recommendations</div>
            <ul className="list-disc pl-5 text-slate-700 dark:text-slate-200/80">
              {(profile?.health?.recommendations || []).slice(0, 4).map((r, idx) => (
                <li key={idx}>{r}</li>
              ))}
            </ul>
          </div>
        </GlassCard>

        <GlassCard title="CGPA Trend (Line chart)" className="lg:col-span-2">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.35)" />
                <XAxis dataKey="semester" stroke="rgba(100,116,139,0.9)" />
                <YAxis domain={[0, 10]} stroke="rgba(100,116,139,0.9)" />
                <Tooltip />
                <Line type="monotone" dataKey="cgpa" stroke="#a78bfa" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <GlassCard title="Attendance Heatmap" className="lg:col-span-2">
          <Heatmap data={heatmap} />
        </GlassCard>

        <GlassCard title="Attendance Recovery Simulator">
          <div className="text-sm text-slate-700 dark:text-slate-200/80">
            Current: {pct(profile?.attendance?.percent)} ({profile?.attendance?.attended_classes ?? '—'}/
            {profile?.attendance?.total_classes ?? '—'})
          </div>
          <div className="mt-3">
            <input
              type="range"
              min="60"
              max="90"
              value={recoveryTarget}
              onChange={(e) => setRecoveryTarget(Number(e.target.value))}
              className="w-full"
            />
            <div className="flex items-center justify-between text-xs text-slate-600 dark:text-slate-300/80 mt-1">
              <span>60%</span>
              <span>Target: {recoveryTarget}%</span>
              <span>90%</span>
            </div>
          </div>
          <div className="mt-3 text-sm">
            {recoverySim ? (
              <div className="rounded-xl border border-slate-900/10 bg-white/60 p-3 dark:border-white/10 dark:bg-white/5">
                {recoverySim.message}
              </div>
            ) : (
              <div className="text-slate-600 dark:text-slate-300/80">No attendance data yet.</div>
            )}
          </div>

          <div className="mt-4">
            <div className="text-sm text-slate-800 dark:text-slate-200/90 mb-2">Smart Alerts</div>
            {alerts.length ? (
              <div className="space-y-2">
                {alerts.map((a, idx) => (
                  <div
                    key={idx}
                    className="rounded-xl border border-rose-600/20 bg-rose-500/10 p-3 text-sm text-rose-900 dark:text-slate-100"
                  >
                    <div className="font-medium">{a.message}</div>
                    <div className="text-xs text-slate-700/80 dark:text-slate-200/70">
                      Recovery needed: {a.recovery_classes_needed} classes
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-slate-600 dark:text-slate-300/80">No active alerts.</div>
            )}
          </div>
        </GlassCard>
      </div>

      <GlassCard title="Activity Timeline (LinkedIn style)">
        {loading && <div className="text-sm text-slate-600 dark:text-slate-300/80">Loading…</div>}
        {!loading && (
          <div className="space-y-3">
            {timeline.map((a) => (
              <div
                key={a.id}
                className="rounded-2xl border border-slate-900/10 bg-white/60 p-4 hover:bg-white/80 transition
                           dark:border-white/10 dark:bg-white/5 dark:hover:bg-white/10"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-medium">{a.activity}</div>
                  <div className="text-xs text-slate-600 dark:text-slate-300/80">{a.date}</div>
                </div>
                <div className="mt-1 text-xs text-slate-600 dark:text-slate-300/80">{a.type}</div>
              </div>
            ))}
          </div>
        )}
      </GlassCard>
    </div>
  )
}

