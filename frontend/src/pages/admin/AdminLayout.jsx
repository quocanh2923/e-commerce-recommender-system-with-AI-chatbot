import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import NotificationBell from '../../components/NotificationBell'
import './Admin.css'

const NAV_ITEMS = [
  { to: '/admin',          label: 'Dashboard',    icon: '📊', end: true },
  { to: '/admin/products', label: 'Sản phẩm',     icon: '📦' },
  { to: '/admin/orders',   label: 'Đơn hàng',     icon: '🧾' },
  { to: '/admin/users',    label: 'Người dùng',   icon: '👥' },
]

export default function AdminLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => { logout(); navigate('/') }

  return (
    <div className="admin-layout">
      <aside className="admin-sidebar">
        <div className="admin-sidebar-logo">
          <span>⚙️ Admin Panel</span>
        </div>
        <nav className="admin-nav">
          {NAV_ITEMS.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `admin-nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="admin-nav-icon">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="admin-sidebar-footer">
          <span className="admin-user-info">👤 {user?.username}</span>
          <button className="admin-logout-btn" onClick={handleLogout}>Đăng xuất</button>
          <button className="admin-back-btn" onClick={() => navigate('/')}>← Về trang chủ</button>
        </div>
      </aside>

      <main className="admin-main">
        <div className="admin-topbar">
          <div className="admin-topbar-left" />
          <div className="admin-topbar-right">
            <NotificationBell isAdmin />
            <span className="admin-topbar-user">👤 {user?.username}</span>
          </div>
        </div>
        <Outlet />
      </main>
    </div>
  )
}
