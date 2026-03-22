import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

const STATUS_LABEL = {
  pending:    { text: 'Chờ xác nhận', color: '#f59e0b' },
  processing: { text: 'Đang xử lý',   color: '#3b82f6' },
  shipped:    { text: 'Đang giao',    color: '#8b5cf6' },
  delivered:  { text: 'Đã giao',      color: '#10b981' },
  cancelled:  { text: 'Đã huỷ',       color: '#ef4444' },
}

export default function AdminDashboard() {
  const { authFetch } = useAuth()
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    authFetch('http://127.0.0.1:8000/admin/stats')
      .then(r => r.json())
      .then(data => { setStats(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return <div className="admin-loading">Đang tải...</div>
  if (!stats)  return <div className="admin-loading">Không thể tải dữ liệu</div>

  const statCards = [
    { label: 'Tổng sản phẩm',  value: stats.total_products, icon: '📦', color: '#6366f1', link: '/admin/products' },
    { label: 'Tổng đơn hàng',  value: stats.total_orders,   icon: '🧾', color: '#f59e0b', link: '/admin/orders' },
    { label: 'Tổng người dùng',value: stats.total_users,    icon: '👥', color: '#10b981', link: '/admin/users' },
    { label: 'Doanh thu',       value: stats.total_revenue?.toLocaleString('vi-VN') + ' ₫', icon: '💰', color: '#ef4444', link: null },
  ]

  return (
    <div className="admin-page">
      <h1 className="admin-page-title">Dashboard</h1>

      {/* Stat Cards */}
      <div className="admin-stat-grid">
        {statCards.map(card => (
          <div
            key={card.label}
            className={`admin-stat-card ${card.link ? 'clickable' : ''}`}
            style={{ borderLeftColor: card.color }}
            onClick={() => card.link && navigate(card.link)}
          >
            <div className="stat-icon">{card.icon}</div>
            <div>
              <p className="stat-value">{card.value}</p>
              <p className="stat-label">{card.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Orders by status */}
      <div className="admin-section">
        <h2>Đơn hàng theo trạng thái</h2>
        <div className="status-bar">
          {Object.entries(STATUS_LABEL).map(([key, s]) => (
            <div key={key} className="status-bar-item">
              <span className="status-dot" style={{ background: s.color }}></span>
              <span>{s.text}: <strong>{stats.orders_by_status?.[key] ?? 0}</strong></span>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Orders */}
      <div className="admin-section">
        <h2>Đơn hàng gần đây</h2>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Mã đơn</th>
              <th>Ngày đặt</th>
              <th>Tổng tiền</th>
              <th>Trạng thái</th>
            </tr>
          </thead>
          <tbody>
            {stats.recent_orders?.map(order => {
              const s = STATUS_LABEL[order.status] || STATUS_LABEL.pending
              return (
                <tr key={order._id} className="clickable" onClick={() => navigate('/admin/orders')}>
                  <td><code>#{order._id.slice(-8).toUpperCase()}</code></td>
                  <td>{new Date(order.created_at).toLocaleDateString('vi-VN')}</td>
                  <td>{order.total?.toLocaleString('vi-VN')} ₫</td>
                  <td>
                    <span className="status-badge" style={{ background: s.color + '20', color: s.color }}>
                      {s.text}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
