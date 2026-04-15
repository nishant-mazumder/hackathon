const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api'

function getToken() {
  return localStorage.getItem('cl_token') || ''
}

async function request(path, options) {
  const token = getToken()
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options && options.headers ? options.headers : {}),
    },
    ...options,
  })

  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`API ${res.status}: ${text || res.statusText}`)
  }
  return res
}

export async function getJson(path) {
  const res = await request(path)
  return await res.json()
}

export async function postJson(path, body) {
  const res = await request(path, { method: 'POST', body: JSON.stringify(body || {}) })
  return await res.json()
}

export function downloadFile(path, filename) {
  return request(path).then(async (res) => {
    const blob = await res.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename || 'download'
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
  })
}

export function setToken(token) {
  if (token) localStorage.setItem('cl_token', token)
  else localStorage.removeItem('cl_token')
}

export function isAuthed() {
  return Boolean(getToken())
}

