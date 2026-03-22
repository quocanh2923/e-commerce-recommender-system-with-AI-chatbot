import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './OrdersPage.css'

const STEPS = [
  { key: 'pending',    label: 'Chờ xác nhận', icon: '🕐' },
  { key: 'processing', label: 'Đang xử lý',   icon: '⚙️' },
  { key: 'shipped',    label: 'Đang giao',    icon: '🚚' },
  { key: 'delivered',  label: 'Đã giao',      icon: '✅' },
]

const STATUS_LABEL = {
  pending:    { text: 'Chờ xác nhận', color: '#f59e0b' },
  processing: { text: 'Đang xử lý',   color: '#3b82f6' },
  shipped:    { text: 'Đang giao',    color: '#8b5cf6' },
  delivered:  { text: 'Đã giao',      color: '#10b981' },
  cancelled:  { text: 'Đã huỷ',       color: '#ef4444' },
}

export default function OrderDetailPage() {
  const { id } = useParams()
  const { token, authFetch } = useAuth()
  const navigate = useNavigate()
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    authFetch(`http://127.0.0.1:8000/orders/${id}`)
      .then(res => {
        if (!res.ok) throw new Error('Không tìm thấy đơn hàng')
        return res.json()
      })
      .then(data => { setOrder(data); setLoading(false) })
      .catch(err => { setError(err.message); setLoading(false) })
  }, [id, token])

  if (loading) return <div className="orders-container"><p className="orders-status">Đang tải...</p></div>
  if (error)   return <div className="orders-container"><p className="orders-status error">{error}</p></div>
  if (!order)  return null

  const s = STATUS_LABEL[order.status] || STATUS_LABEL.pending
  const isCancelled = order.status === 'cancelled'
  const currentStepIdx = STEPS.findIndex(s => s.key === order.status)
  const date = new Date(order.created_at).toLocaleDateString('vi-VN', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })

  return (
    <div className="orders-container">
      <button className="back-btn" onClick={() => navigate('/orders')}>← Đơn hàng của tôi</button>

      <div className="order-detail-card">
        {/* Header */}
        <div className="order-detail-header">
          <div>
            <h2>Đơn hàng #{order._id.slice(-8).toUpperCase()}</h2>
            <p className="order-date">{date}</p>
          </div>
          <span className="order-status-badge lg" style={{ background: s.color + '20', color: s.color }}>
            {s.text}
          </span>
        </div>

        {/* Timeline */}
        {!isCancelled && (
          <div className="order-timeline">
            {STEPS.map((step, i) => {
              const done = i <= currentStepIdx
              const active = i === currentStepIdx
              return (
                <div key={step.key} className={`timeline-step ${done ? 'done' : ''} ${active ? 'active' : ''}`}>
                  <div className="timeline-icon">{done ? step.icon : '○'}</div>
                  <div className="timeline-label">{step.label}</div>
                  {i < STEPS.length - 1 && (
                    <div className={`timeline-line ${i < currentStepIdx ? 'done' : ''}`} />
                  )}
                </div>
              )
            })}
          </div>
        )}

        {isCancelled && (
          <div className="order-cancelled-banner">
            ❌ Đơn hàng này đã bị huỷ
          </div>
        )}

        {/* Danh sách sản phẩm */}
        <div className="order-detail-section">
          <h3>Sản phẩm đã đặt</h3>
          <div className="order-items-list">
            {order.items.map((item, i) => (
              <div key={i} className="order-item-row">
                <div className="order-item-info">
                  <span className="order-item-name">{item.name}</span>
                  <span className="order-item-qty">×{item.quantity}</span>
                </div>
                <span className="order-item-price">
                  {(item.price * item.quantity).toLocaleString('vi-VN')}đ
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Tổng tiền */}
        <div className="order-detail-summary">
          <div className="summary-row">
            <span>Tạm tính</span>
            <span>{order.subtotal.toLocaleString('vi-VN')}đ</span>
          </div>
          <div className="summary-row">
            <span>Phí vận chuyển</span>
            <span>{order.shipping.toLocaleString('vi-VN')}đ</span>
          </div>
          <div className="summary-row total-row">
            <span>Tổng cộng</span>
            <span>{order.total.toLocaleString('vi-VN')}đ</span>
          </div>
        </div>
      </div>
    </div>
  )
}
