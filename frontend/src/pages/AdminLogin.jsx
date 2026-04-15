import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import GlassCard from '../components/GlassCard.jsx'
import { postJson, setToken } from '../lib/api.js'

export default function AdminLogin() {
  const nav = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await postJson('/auth/login/', { username, password })
      setToken(res.access)
      nav('/admin')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto">
      <GlassCard title="Admin Login">
        <form onSubmit={submit} className="space-y-3">
          <div>
            <div className="text-sm text-slate-600 dark:text-slate-300/80 mb-1">Username</div>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-slate-900/10 bg-white/70 text-slate-900 text-sm
                         dark:border-white/10 dark:bg-white/5 dark:text-slate-100"
            />
          </div>
          <div>
            <div className="text-sm text-slate-600 dark:text-slate-300/80 mb-1">Password</div>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-slate-900/10 bg-white/70 text-slate-900 text-sm
                         dark:border-white/10 dark:bg-white/5 dark:text-slate-100"
            />
          </div>

          {error && (
            <div className="rounded-xl border border-rose-600/25 bg-rose-500/10 p-3 text-sm text-rose-900 dark:text-rose-100">
              {error}
            </div>
          )}

          <button
            disabled={loading}
            className="w-full px-3 py-2 rounded-xl bg-indigo-500/85 hover:bg-indigo-500 transition text-sm text-white disabled:opacity-60"
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>

          <div className="text-sm text-slate-600 dark:text-slate-300/80">
            No admin account? <Link className="underline" to="/admin/register">Register</Link>
          </div>
        </form>
      </GlassCard>
    </div>
  )
}

