import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts'

const STATUS_LABEL = {
  pending:    { text: 'Chờ xác nhận', color: '#f59e0b' },
  processing: { text: 'Đang xử lý',   color: '#3b82f6' },
  shipped:    { text: 'Đang giao',    color: '#8b5cf6' },
  delivered:  { text: 'Đã giao',      color: '#10b981' },
  cancelled:  { text: 'Đã huỷ',       color: '#ef4444' },
}

const formatVND = (v) => {
  if (v >= 1_000_000) return (v / 1_000_000).toFixed(1) + 'tr'
  if (v >= 1_000) return (v / 1_000).toFixed(0) + 'k'
  return v
}

export default function AdminDashboard() {
  const { authFetch } = useAuth()
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [chartData, setChartData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = authFetch('http://127.0.0.1:8000/admin/stats')
      .then(r => r.json())
      .catch(() => null)
    const fetchCharts = authFetch('http://127.0.0.1:8000/admin/chart-data')
      .then(r => r.ok ? r.json() : null)
      .catch(() => null)
    Promise.all([fetchStats, fetchCharts]).then(([statsData, charts]) => {
      setStats(statsData)
      setChartData(charts)
      setLoading(false)
    })
  }, [])

  if (loading) return <div className="admin-loading">Đang tải...</div>
  if (!stats)  return <div className="admin-loading">Không thể tải dữ liệu — kiểm tra kết nối backend</div>

  const statCards = [
    { label: 'Tổng sản phẩm',  value: stats.total_products, icon: '📦', color: '#6366f1', link: '/admin/products' },
    { label: 'Tổng đơn hàng',  value: stats.total_orders,   icon: '🧾', color: '#f59e0b', link: '/admin/orders' },
    { label: 'Tổng người dùng',value: stats.total_users,    icon: '👥', color: '#10b981', link: '/admin/users' },
    { label: 'Doanh thu (đã giao)', value: stats.total_revenue?.toLocaleString('vi-VN') + ' ₫', icon: '💰', color: '#ef4444', link: null },
  ]

  // Dữ liệu pie chart trạng thái đơn
  const pieData = Object.entries(STATUS_LABEL)
    .map(([key, s]) => ({ name: s.text, value: stats.orders_by_status?.[key] ?? 0, color: s.color }))
    .filter(d => d.value > 0)

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

      {/* Charts row */}
      {chartData && (
        <div className="dashboard-charts-row">

          {/* Bar chart: doanh thu 7 ngày */}
          <div className="dashboard-chart-card wide">
            <h2>Doanh thu 7 ngày gần đây</h2>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={chartData.revenue_by_day} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis tickFormatter={formatVND} tick={{ fontSize: 11 }} width={48} />
                <Tooltip
                  formatter={(v) => [v.toLocaleString('vi-VN') + ' ₫', 'Doanh thu']}
                  labelStyle={{ fontWeight: 600 }}
                />
                <Bar dataKey="revenue" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Pie chart: tỉ lệ đơn hàng */}
          <div className="dashboard-chart-card">
            <h2>Tỉ lệ đơn hàng</h2>
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="45%"
                    outerRadius={72}
                    dataKey="value"
                    label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Legend iconSize={10} wrapperStyle={{ fontSize: 12 }} />
                  <Tooltip formatter={(v, name) => [v + ' đơn', name]} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="chart-empty">Chưa có dữ liệu</p>
            )}
          </div>

        </div>
      )}

      {/* Top categories chart */}
      {chartData?.top_categories?.length > 0 && (
        <div className="admin-section">
          <h2>Top danh mục bán chạy</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart
              data={chartData.top_categories}
              layout="vertical"
              margin={{ top: 4, right: 24, left: 8, bottom: 4 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="category" tick={{ fontSize: 12 }} width={80} />
              <Tooltip formatter={(v) => [v + ' sản phẩm', 'Số lượng bán']} />
              <Bar dataKey="quantity" fill="#10b981" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Orders by status text summary */}
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
