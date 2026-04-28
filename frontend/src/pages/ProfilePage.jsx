import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import API_URL from '../config'
import './ProfilePage.css'

export default function ProfilePage() {
  const { user, authFetch, login, token } = useAuth()

  const [profileForm, setProfileForm] = useState({
    full_name: user?.full_name || '',
    phone: user?.phone || '',
    address: user?.address || '',
  })
  const [profileMsg, setProfileMsg] = useState(null)
  const [profileLoading, setProfileLoading] = useState(false)

  const [pwForm, setPwForm] = useState({ current_password: '', new_password: '', confirm_password: '' })
  const [pwMsg, setPwMsg] = useState(null)
  const [pwLoading, setPwLoading] = useState(false)

  const handleProfileChange = (e) => {
    setProfileForm({ ...profileForm, [e.target.name]: e.target.value })
  }

  const handleProfileSubmit = async (e) => {
    e.preventDefault()
    setProfileLoading(true)
    setProfileMsg(null)
    try {
      const res = await authFetch(`${API_URL}/users/me`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profileForm),
      })
      const data = await res.json()
      if (!res.ok) {
        setProfileMsg({ type: 'error', text: data.detail || 'Update failed' })
      } else {
        // Cập nhật lại user trong localStorage/context
        login(token, data)
        setProfileMsg({ type: 'success', text: 'Profile updated successfully!' })
      }
    } catch {
      setProfileMsg({ type: 'error', text: 'Server connection error' })
    } finally {
      setProfileLoading(false)
    }
  }

  const handlePwChange = (e) => {
    setPwForm({ ...pwForm, [e.target.name]: e.target.value })
  }

  const handlePwSubmit = async (e) => {
    e.preventDefault()
    setPwMsg(null)
    if (pwForm.new_password !== pwForm.confirm_password) {
      setPwMsg({ type: 'error', text: 'New passwords do not match' })
      return
    }
    setPwLoading(true)
    try {
      const res = await authFetch(`${API_URL}/users/me/password`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_password: pwForm.current_password,
          new_password: pwForm.new_password,
        }),
      })
      const data = await res.json()
      if (!res.ok) {
        setPwMsg({ type: 'error', text: data.detail || 'Failed to change password' })
      } else {
        setPwMsg({ type: 'success', text: 'Password changed successfully!' })
        setPwForm({ current_password: '', new_password: '', confirm_password: '' })
      }
    } catch {
      setPwMsg({ type: 'error', text: 'Server connection error' })
    } finally {
      setPwLoading(false)
    }
  }

  return (
    <div className="profile-page">
      <h1 className="profile-title">My Profile</h1>

      {/* ── Thông tin tài khoản (chỉ đọc) ── */}
      <div className="profile-card">
        <h2>Account Information</h2>
        <div className="profile-info-row">
          <span className="profile-label">Username</span>
          <span className="profile-value">{user?.username}</span>
        </div>
        <div className="profile-info-row">
          <span className="profile-label">Email</span>
          <span className="profile-value">{user?.email}</span>
        </div>
        <div className="profile-info-row">
          <span className="profile-label">Role</span>
          <span className={`profile-role-badge ${user?.role}`}>{user?.role === 'admin' ? 'Administrator' : 'Customer'}</span>
        </div>
      </div>

      {/* ── Chỉnh sửa thông tin cá nhân ── */}
      <div className="profile-card">
        <h2>Edit Information</h2>
        <form onSubmit={handleProfileSubmit} className="profile-form">
          <div className="profile-field">
            <label>Full Name</label>
            <input
              type="text"
              name="full_name"
              value={profileForm.full_name}
              onChange={handleProfileChange}
              placeholder="Enter your full name"
            />
          </div>
          <div className="profile-field">
            <label>Phone Number</label>
            <input
              type="tel"
              name="phone"
              value={profileForm.phone}
              onChange={handleProfileChange}
              placeholder="Enter phone number"
            />
          </div>
          <div className="profile-field">
            <label>Address</label>
            <textarea
              name="address"
              value={profileForm.address}
              onChange={handleProfileChange}
              placeholder="Enter your default shipping address"
              rows={3}
            />
          </div>
          {profileMsg && (
            <div className={`profile-msg ${profileMsg.type}`}>{profileMsg.text}</div>
          )}
          <button type="submit" className="profile-btn" disabled={profileLoading}>
            {profileLoading ? 'Saving...' : 'Save Changes'}
          </button>
        </form>
      </div>

      {/* ── Đổi mật khẩu ── */}
      <div className="profile-card">
        <h2>Change Password</h2>
        <form onSubmit={handlePwSubmit} className="profile-form">
          <div className="profile-field">
            <label>Current Password</label>
            <input
              type="password"
              name="current_password"
              value={pwForm.current_password}
              onChange={handlePwChange}
              required
              placeholder="Enter current password"
            />
          </div>
          <div className="profile-field">
            <label>New Password</label>
            <input
              type="password"
              name="new_password"
              value={pwForm.new_password}
              onChange={handlePwChange}
              required
              minLength={6}
              placeholder="At least 6 characters"
            />
          </div>
          <div className="profile-field">
            <label>Confirm New Password</label>
            <input
              type="password"
              name="confirm_password"
              value={pwForm.confirm_password}
              onChange={handlePwChange}
              required
              placeholder="Re-enter new password"
            />
          </div>
          {pwMsg && (
            <div className={`profile-msg ${pwMsg.type}`}>{pwMsg.text}</div>
          )}
          <button type="submit" className="profile-btn" disabled={pwLoading}>
            {pwLoading ? 'Processing...' : 'Change Password'}
          </button>
        </form>
      </div>
    </div>
  )
}
