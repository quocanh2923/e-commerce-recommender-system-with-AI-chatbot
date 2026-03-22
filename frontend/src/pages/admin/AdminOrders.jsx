import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../../context/AuthContext'

const STATUS_OPTIONS = [
  { value: 'pending',    label: 'Chờ xác nhận', color: '#f59e0b' },
  { value: 'processing', label: 'Đang xử lý',   color: '#3b82f6' },
  { value: 'shipped',    label: 'Đang giao',    color: '#8b5cf6' },
  { value: 'delivered',  label: 'Đã giao',      color: '#10b981' },
  { value: 'cancelled',  label: 'Đã huỷ',       color: '#ef4444' },
]
const STATUS_MAP = Object.fromEntries(STATUS_OPTIONS.map(s => [s.value, s]))

export default function AdminOrders() {
  const { authFetch } = useAuth()
  const [data, setData]           = useState({ orders: [], total: 0 })
  const [loading, setLoading]     = useState(true)
  const [statusFilter, setFilter] = useState('')
  const [page, setPage]           = useState(1)
  const [updating, setUpdating]   = useState(null)

  const fetchOrders = useCallback(async () => {
    setLoading(true)
    const params = new URLSearchParams({ page, limit: 20, ...(statusFilter ? { status: statusFilter } : {}) })
    const res = await authFetch(`http://127.0.0.1:8000/admin/orders?${params}`)
    if (res.ok) setData(await res.json())
    setLoading(false)
  }, [page, statusFilter])

  useEffect(() => { fetchOrders() }, [fetchOrders])

  const handleStatusChange = async (orderId, newStatus) => {
    setUpdating(orderId)
    const res = await authFetch(`http://127.0.0.1:8000/admin/orders/${orderId}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus }),
    })
    if (res.ok) {
      const updated = await res.json()
      setData(prev => ({
        ...prev,
        orders: prev.orders.map(o => o._id === orderId ? updated : o)
      }))
    }
    setUpdating(null)
  }

  const totalPages = Math.ceil(data.total / 20)

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <h1 className="admin-page-title">Quản lý đơn hàng <span className="admin-count">({data.total})</span></h1>
      </div>

      {/* Filter */}
      <div className="admin-toolbar">
        <select
          className="admin-select"
          value={statusFilter}
          onChange={e => { setFilter(e.target.value); setPage(1) }}
        >
          <option value="">Tất cả trạng thái</option>
          {STATUS_OPTIONS.map(s => (
            <option key={s.value} value={s.value}>{s.label}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      {loading ? <div className="admin-loading">Đang tải...</div> : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Mã đơn</th>
                <th>Ngày đặt</th>
                <th>Sản phẩm</th>
                <th>Tổng tiền</th>
                <th>Trạng thái</th>
                <th>Cập nhật</th>
              </tr>
            </thead>
            <tbody>
              {data.orders.map(order => {
                const s = STATUS_MAP[order.status] || STATUS_MAP.pending
                return (
                  <tr key={order._id}>
                    <td><code>#{order._id.slice(-8).toUpperCase()}</code></td>
                    <td>{new Date(order.created_at).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' })}</td>
                    <td className="order-items-cell">
                      {order.items?.slice(0, 2).map((item, i) => (
                        <span key={i} className="order-item-tag">{item.name} ×{item.quantity}</span>
                      ))}
                      {order.items?.length > 2 && <span className="order-item-tag">+{order.items.length - 2}</span>}
                    </td>
                    <td><strong>{order.total?.toLocaleString('vi-VN')} ₫</strong></td>
                    <td>
                      <span className="status-badge" style={{ background: s.color + '20', color: s.color }}>
                        {s.label}
                      </span>
                    </td>
                    <td>
                      <select
                        className="admin-select sm"
                        value={order.status}
                        disabled={updating === order._id}
                        onChange={e => handleStatusChange(order._id, e.target.value)}
                      >
                        {STATUS_OPTIONS.map(opt => (
                          <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                      </select>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="admin-pagination">
          <button disabled={page === 1} onClick={() => setPage(p => p - 1)}>‹</button>
          <span>Trang {page} / {totalPages}</span>
          <button disabled={page === totalPages} onClick={() => setPage(p => p + 1)}>›</button>
        </div>
      )}
    </div>
  )
}
