import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
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
      const res = await authFetch('http://127.0.0.1:8000/users/me', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profileForm),
      })
      const data = await res.json()
      if (!res.ok) {
        setProfileMsg({ type: 'error', text: data.detail || 'Cập nhật thất bại' })
      } else {
        // Cập nhật lại user trong localStorage/context
        login(token, data)
        setProfileMsg({ type: 'success', text: 'Cập nhật thông tin thành công!' })
      }
    } catch {
      setProfileMsg({ type: 'error', text: 'Lỗi kết nối máy chủ' })
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
      setPwMsg({ type: 'error', text: 'Mật khẩu mới không khớp' })
      return
    }
    setPwLoading(true)
    try {
      const res = await authFetch('http://127.0.0.1:8000/users/me/password', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_password: pwForm.current_password,
          new_password: pwForm.new_password,
        }),
      })
      const data = await res.json()
      if (!res.ok) {
        setPwMsg({ type: 'error', text: data.detail || 'Đổi mật khẩu thất bại' })
      } else {
        setPwMsg({ type: 'success', text: 'Đổi mật khẩu thành công!' })
        setPwForm({ current_password: '', new_password: '', confirm_password: '' })
      }
    } catch {
      setPwMsg({ type: 'error', text: 'Lỗi kết nối máy chủ' })
    } finally {
      setPwLoading(false)
    }
  }

  return (
    <div className="profile-page">
      <h1 className="profile-title">Trang cá nhân</h1>

      {/* ── Thông tin tài khoản (chỉ đọc) ── */}
      <div className="profile-card">
        <h2>Thông tin tài khoản</h2>
        <div className="profile-info-row">
          <span className="profile-label">Tên đăng nhập</span>
          <span className="profile-value">{user?.username}</span>
        </div>
        <div className="profile-info-row">
          <span className="profile-label">Email</span>
          <span className="profile-value">{user?.email}</span>
        </div>
        <div className="profile-info-row">
          <span className="profile-label">Vai trò</span>
          <span className={`profile-role-badge ${user?.role}`}>{user?.role === 'admin' ? 'Quản trị viên' : 'Khách hàng'}</span>
        </div>
      </div>

      {/* ── Chỉnh sửa thông tin cá nhân ── */}
      <div className="profile-card">
        <h2>Chỉnh sửa thông tin</h2>
        <form onSubmit={handleProfileSubmit} className="profile-form">
          <div className="profile-field">
            <label>Họ và tên</label>
            <input
              type="text"
              name="full_name"
              value={profileForm.full_name}
              onChange={handleProfileChange}
              placeholder="Nhập họ và tên"
            />
          </div>
          <div className="profile-field">
            <label>Số điện thoại</label>
            <input
              type="tel"
              name="phone"
              value={profileForm.phone}
              onChange={handleProfileChange}
              placeholder="Nhập số điện thoại"
            />
          </div>
          <div className="profile-field">
            <label>Địa chỉ</label>
            <textarea
              name="address"
              value={profileForm.address}
              onChange={handleProfileChange}
              placeholder="Nhập địa chỉ giao hàng mặc định"
              rows={3}
            />
          </div>
          {profileMsg && (
            <div className={`profile-msg ${profileMsg.type}`}>{profileMsg.text}</div>
          )}
          <button type="submit" className="profile-btn" disabled={profileLoading}>
            {profileLoading ? 'Đang lưu...' : 'Lưu thay đổi'}
          </button>
        </form>
      </div>

      {/* ── Đổi mật khẩu ── */}
      <div className="profile-card">
        <h2>Đổi mật khẩu</h2>
        <form onSubmit={handlePwSubmit} className="profile-form">
          <div className="profile-field">
            <label>Mật khẩu hiện tại</label>
            <input
              type="password"
              name="current_password"
              value={pwForm.current_password}
              onChange={handlePwChange}
              required
              placeholder="Nhập mật khẩu hiện tại"
            />
          </div>
          <div className="profile-field">
            <label>Mật khẩu mới</label>
            <input
              type="password"
              name="new_password"
              value={pwForm.new_password}
              onChange={handlePwChange}
              required
              minLength={6}
              placeholder="Tối thiểu 6 ký tự"
            />
          </div>
          <div className="profile-field">
            <label>Xác nhận mật khẩu mới</label>
            <input
              type="password"
              name="confirm_password"
              value={pwForm.confirm_password}
              onChange={handlePwChange}
              required
              placeholder="Nhập lại mật khẩu mới"
            />
          </div>
          {pwMsg && (
            <div className={`profile-msg ${pwMsg.type}`}>{pwMsg.text}</div>
          )}
          <button type="submit" className="profile-btn" disabled={pwLoading}>
            {pwLoading ? 'Đang xử lý...' : 'Đổi mật khẩu'}
          </button>
        </form>
      </div>
    </div>
  )
}
