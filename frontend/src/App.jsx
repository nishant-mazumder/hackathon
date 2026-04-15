import { BrowserRouter, Link, NavLink, Route, Routes } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'
import AdminDashboard from './pages/AdminDashboard.jsx'
import AdminLogin from './pages/AdminLogin.jsx'
import AdminRegister from './pages/AdminRegister.jsx'
import StudentDashboard from './pages/StudentDashboard.jsx'
import { isAuthed, setToken } from './lib/api.js'

const cx = (...xs) => xs.filter(Boolean).join(' ')

function ThemeToggle({ theme, setTheme }) {
  return (
    <button
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      className="px-3 py-2 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 transition text-sm"
      title="Toggle theme"
    >
      {theme === 'dark' ? 'Dark' : 'Light'}
    </button>
  )
}

function Shell({ theme, setTheme, children }) {
  return (
    <div className={cx('min-h-full', theme === 'dark' ? 'app-bg text-slate-100' : 'app-bg-light text-slate-900')}>
      <div className="max-w-7xl mx-auto px-4 py-6">
        <header className="flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-2xl bg-gradient-to-br from-indigo-500 to-fuchsia-500 shadow-lg shadow-indigo-500/20" />
            <div>
              <div className="font-semibold leading-tight">CampusLedger</div>
              <div className={cx('text-xs', theme === 'dark' ? 'text-slate-300' : 'text-slate-600')}>
                Smart student analytics
              </div>
            </div>
          </Link>
          <nav className="flex items-center gap-2">
            <NavLink
              to="/student"
              className={({ isActive }) =>
                cx(
                  'px-3 py-2 rounded-xl text-sm transition',
                  isActive ? 'bg-white/10 border border-white/15' : 'hover:bg-white/5'
                )
              }
            >
              Student
            </NavLink>
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                cx(
                  'px-3 py-2 rounded-xl text-sm transition',
                  isActive ? 'bg-white/10 border border-white/15' : 'hover:bg-white/5'
                )
              }
            >
              Admin
            </NavLink>
            <ThemeToggle theme={theme} setTheme={setTheme} />
          </nav>
        </header>

        <main className="mt-6">{children}</main>
        <footer className={cx('mt-10 text-xs', theme === 'dark' ? 'text-slate-400' : 'text-slate-600')}>
          CampusLedger © {new Date().getFullYear()}
        </footer>
      </div>
    </div>
  )
}

export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem('cl_theme') || 'dark')

  useEffect(() => {
    localStorage.setItem('cl_theme', theme)
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])

  const shellProps = useMemo(() => ({ theme, setTheme }), [theme])

  return (
    <BrowserRouter>
      <Shell {...shellProps}>
        <Routes>
          <Route path="/" element={<StudentDashboard />} />
          <Route path="/student" element={<StudentDashboard />} />
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/admin/register" element={<AdminRegister />} />
          <Route path="/admin" element={isAuthed() ? <AdminDashboard /> : <AdminLogin />} />
        </Routes>
      </Shell>
    </BrowserRouter>
  )
}
