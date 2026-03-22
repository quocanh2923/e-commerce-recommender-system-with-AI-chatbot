import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../../context/AuthContext'
import { useSearchParams } from 'react-router-dom'

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
  const [searchParams, setSearchParams] = useSearchParams()
  const [data, setData]           = useState({ orders: [], total: 0 })
  const [loading, setLoading]     = useState(true)
  const [statusFilter, setFilter] = useState('')
  const [page, setPage]           = useState(1)
  const [updating, setUpdating]   = useState(null)
  const [detail, setDetail]       = useState(null)
  const [detailReviews, setDetailReviews] = useState({})

  const fetchOrders = useCallback(async () => {
    setLoading(true)
    const params = new URLSearchParams({ page, limit: 20, ...(statusFilter ? { status: statusFilter } : {}) })
    const res = await authFetch(`http://127.0.0.1:8000/admin/orders?${params}`)
    if (res.ok) setData(await res.json())
    setLoading(false)
  }, [page, statusFilter])

  useEffect(() => { fetchOrders() }, [fetchOrders])

  // Open detail from notification ?review=orderId
  useEffect(() => {
    const reviewOrderId = searchParams.get('review')
    if (reviewOrderId && data.orders.length > 0) {
      const order = data.orders.find(o => o._id === reviewOrderId)
      if (order) {
        openDetail(order)
        setSearchParams({}, { replace: true })
      }
    }
  }, [data.orders, searchParams])

  const openDetail = async (order) => {
    setDetail(order)
    try {
      const res = await authFetch(`http://127.0.0.1:8000/admin/orders/${order._id}/reviews`)
      if (res.ok) setDetailReviews(await res.json())
      else setDetailReviews({})
    } catch { setDetailReviews({}) }
  }

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
                  <tr key={order._id} className="clickable" onClick={() => openDetail(order)}>
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
                    <td onClick={e => e.stopPropagation()}>
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

      {/* Order Detail Modal */}
      {detail && (() => {
        const s = STATUS_MAP[detail.status] || STATUS_MAP.pending
        const closeModal = () => { setDetail(null); setDetailReviews({}) }
        return (
          <div className="admin-modal-overlay" onClick={closeModal}>
            <div className="admin-modal" onClick={e => e.stopPropagation()}>
              <h2>Chi tiết đơn hàng #{detail._id.slice(-8).toUpperCase()}</h2>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <span style={{ fontSize: '0.85rem', color: '#64748b' }}>
                  {new Date(detail.created_at).toLocaleDateString('vi-VN', {
                    day: '2-digit', month: '2-digit', year: 'numeric',
                    hour: '2-digit', minute: '2-digit'
                  })}
                </span>
                <span className="status-badge" style={{ background: s.color + '20', color: s.color }}>
                  {s.label}
                </span>
              </div>

              {(detail.username || detail.user_id) && (
                <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: 12 }}>
                  Khách hàng: <strong>{detail.username || detail.user_id}</strong>
                </p>
              )}

              {/* Products table with reviews */}
              <div className="admin-order-items">
                {detail.items?.map((item, i) => {
                  const review = detailReviews[item.product_id]
                  return (
                    <div key={i} className="admin-order-item-block">
                      <div className="admin-order-item-row">
                        <span className="admin-order-item-name">{item.name}</span>
                        <span className="admin-order-item-qty">×{item.quantity}</span>
                        <span className="admin-order-item-price">{(item.price * item.quantity).toLocaleString('vi-VN')} ₫</span>
                      </div>
                      {review && (
                        <div className="admin-review-block">
                          <div className="admin-review-stars">
                            {'★'.repeat(Math.round(review.rating))}{'☆'.repeat(5 - Math.round(review.rating))}
                            <span className="admin-review-score">{review.rating}/5</span>
                            {review.username && <span className="admin-review-user">— {review.username}</span>}
                          </div>
                          {review.feedback && (
                            <div className="admin-review-feedback">"{review.feedback}"</div>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>

              <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: 12, display: 'flex', flexDirection: 'column', gap: 4, fontSize: '0.9rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b' }}>
                  <span>Tạm tính</span>
                  <span>{detail.subtotal?.toLocaleString('vi-VN')} ₫</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b' }}>
                  <span>Phí vận chuyển</span>
                  <span>{detail.shipping?.toLocaleString('vi-VN')} ₫</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700, fontSize: '1.05rem', borderTop: '2px solid #e2e8f0', paddingTop: 8, marginTop: 4 }}>
                  <span>Tổng cộng</span>
                  <span style={{ color: '#e74c3c' }}>{detail.total?.toLocaleString('vi-VN')} ₫</span>
                </div>
              </div>

              <div className="modal-actions" style={{ marginTop: 20 }}>
                <button className="admin-btn outline" onClick={closeModal}>Đóng</button>
              </div>
            </div>
          </div>
        )
      })()}
    </div>
  )
}
