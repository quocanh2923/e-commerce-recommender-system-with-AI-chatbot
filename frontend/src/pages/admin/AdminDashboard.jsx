import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import API_URL from '../../config'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts'

const STATUS_LABEL = {
  pending:    { text: 'Pending',    color: '#f59e0b' },
  processing: { text: 'Processing', color: '#3b82f6' },
  shipped:    { text: 'Shipped',    color: '#8b5cf6' },
  delivered:  { text: 'Delivered',  color: '#10b981' },
  cancelled:  { text: 'Cancelled',  color: '#ef4444' },
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
    const fetchStats = authFetch(`${API_URL}/admin/stats`)
      .then(r => r.json())
      .catch(() => null)
    const fetchCharts = authFetch(`${API_URL}/admin/chart-data`)
      .then(r => r.ok ? r.json() : null)
      .catch(() => null)
    Promise.all([fetchStats, fetchCharts]).then(([statsData, charts]) => {
      setStats(statsData)
      setChartData(charts)
      setLoading(false)
    })
  }, [])

  if (loading) return <div className="admin-loading">Loading...</div>
  if (!stats)  return <div className="admin-loading">Failed to load data — check backend connection</div>

  const statCards = [
    { label: 'Total Products',      value: stats.total_products, icon: '📦', color: '#6366f1', link: '/admin/products' },
    { label: 'Total Orders',         value: stats.total_orders,   icon: '🧾', color: '#f59e0b', link: '/admin/orders' },
    { label: 'Total Users',          value: stats.total_users,    icon: '👥', color: '#10b981', link: '/admin/users' },
    { label: 'Revenue (Delivered)',  value: stats.total_revenue?.toLocaleString('en-GB') + ' ₫', icon: '💰', color: '#ef4444', link: null },
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
            <h2>Revenue Last 7 Days</h2>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={chartData.revenue_by_day} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis tickFormatter={formatVND} tick={{ fontSize: 11 }} width={48} />
                <Tooltip
                  formatter={(v) => [v.toLocaleString('en-GB') + ' ₫', 'Revenue']}
                  labelStyle={{ fontWeight: 600 }}
                />
                <Bar dataKey="revenue" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Pie chart: tỉ lệ đơn hàng */}
          <div className="dashboard-chart-card">
            <h2>Order Distribution</h2>
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
                  <Tooltip formatter={(v, name) => [v + ' orders', name]} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="chart-empty">No data yet</p>
            )}
          </div>

        </div>
      )}

      {/* Top categories chart */}
      {chartData?.top_categories?.length > 0 && (
        <div className="admin-section">
          <h2>Top Selling Categories</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart
              data={chartData.top_categories}
              layout="vertical"
              margin={{ top: 4, right: 24, left: 8, bottom: 4 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="category" tick={{ fontSize: 12 }} width={80} />
              <Tooltip formatter={(v) => [v + ' items', 'Qty Sold']} />
              <Bar dataKey="quantity" fill="#10b981" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Orders by status text summary */}
      <div className="admin-section">
        <h2>Orders by Status</h2>
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
        <h2>Recent Orders</h2>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Date</th>
              <th>Total</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {stats.recent_orders?.map(order => {
              const s = STATUS_LABEL[order.status] || STATUS_LABEL.pending
              return (
                <tr key={order._id} className="clickable" onClick={() => navigate('/admin/orders')}>
                  <td><code>#{order._id.slice(-8).toUpperCase()}</code></td>
                  <td>{new Date(order.created_at).toLocaleDateString('en-GB')}</td>
                  <td>{order.total?.toLocaleString('en-GB')} ₫</td>
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
