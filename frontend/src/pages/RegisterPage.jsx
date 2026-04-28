import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import API_URL from '../config'
import './AuthPages.css'

export default function RegisterPage() {
  const [form, setForm] = useState({ username: '', email: '', password: '', full_name: '' })
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const res = await fetch(`${API_URL}/users/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })

      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Registration failed')

      navigate('/login')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <h2>Create Account</h2>
        <p className="auth-sub">Join ShopAI today</p>

        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <label>Full Name</label>
          <input
            type="text"
            placeholder="John Doe"
            value={form.full_name}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          />

          <label>Username</label>
          <input
            type="text"
            placeholder="nguyenvana"
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
            required
          />

          <label>Email</label>
          <input
            type="email"
            placeholder="you@example.com"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
          />

          <label>Password</label>
          <input
            type="password"
            placeholder="At least 6 characters"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
            minLength={6}
          />

          <button type="submit" disabled={loading} className="auth-submit">
            {loading ? 'Creating account...' : 'Register'}
          </button>
        </form>

        <p className="auth-switch">
          Already have an account? <Link to="/login">Sign In</Link>
        </p>
      </div>
    </div>
  )
}
