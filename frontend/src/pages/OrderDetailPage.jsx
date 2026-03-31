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

/* ── Star Rating Component ─────────────────────── */
function StarRating({ value, onChange, disabled }) {
  const [hover, setHover] = useState(0)
  return (
    <span className="star-rating">
      {[1, 2, 3, 4, 5].map(star => (
        <span
          key={star}
          className={`star ${star <= (hover || value) ? 'filled' : ''} ${disabled ? 'disabled' : ''}`}
          onClick={() => !disabled && onChange(star)}
          onMouseEnter={() => !disabled && setHover(star)}
          onMouseLeave={() => !disabled && setHover(0)}
        >
          ★
        </span>
      ))}
    </span>
  )
}

export default function OrderDetailPage() {
  const { id } = useParams()
  const { token, authFetch } = useAuth()
  const navigate = useNavigate()
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [reviews, setReviews] = useState({})        // { product_id: { rating, feedback } }
  const [pendingRatings, setPendingRatings] = useState({}) // { product_id: rating }
  const [pendingFeedback, setPendingFeedback] = useState({}) // { product_id: text }
  const [submitting, setSubmitting] = useState(false)
  const [toast, setToast] = useState(null) // { type: 'success'|'error', message }

  const showToast = (type, message) => {
    setToast({ type, message })
    setTimeout(() => setToast(null), 3500)
  }

  useEffect(() => {
    authFetch(`http://127.0.0.1:8000/orders/${id}`)
      .then(res => {
        if (!res.ok) throw new Error('Không tìm thấy đơn hàng')
        return res.json()
      })
      .then(data => { setOrder(data); setLoading(false) })
      .catch(err => { setError(err.message); setLoading(false) })
  }, [id, token])

  // Fetch existing reviews for this order
  useEffect(() => {
    if (!order || order.status !== 'delivered') return
    authFetch(`http://127.0.0.1:8000/products/reviews/${id}`)
      .then(res => res.ok ? res.json() : {})
      .then(data => setReviews(data))
      .catch(() => {})
  }, [order, id])

  const handleSubmitAll = async () => {
    const entries = Object.entries(pendingRatings)
    if (entries.length === 0) return
    setSubmitting(true)
    let success = 0
    let fail = 0
    for (const [productId, rating] of entries) {
      try {
        const res = await authFetch(`http://127.0.0.1:8000/products/${productId}/rate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            rating,
            order_id: id,
            feedback: pendingFeedback[productId] || '',
          }),
        })
        if (res.ok) {
          setReviews(prev => ({
            ...prev,
            [productId]: { rating, feedback: pendingFeedback[productId] || '' },
          }))
          setPendingRatings(prev => { const copy = { ...prev }; delete copy[productId]; return copy })
          setPendingFeedback(prev => { const copy = { ...prev }; delete copy[productId]; return copy })
          success++
        } else { fail++ }
      } catch { fail++ }
    }
    // Gửi 1 thông báo gộp cho admin
    if (success > 0) {
      try {
        await authFetch('http://127.0.0.1:8000/products/reviews/notify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ order_id: id, count: success }),
        })
      } catch {}
    }
    setSubmitting(false)
    if (success > 0 && fail === 0) {
      showToast('success', `Đã gửi đánh giá ${success} sản phẩm thành công!`)
    } else if (success > 0 && fail > 0) {
      showToast('error', `Đánh giá ${success} thành công, ${fail} thất bại`)
    } else {
      showToast('error', 'Gửi đánh giá thất bại, vui lòng thử lại')
    }
  }

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
            {order.items.map((item, i) => {
              const reviewData = reviews[item.product_id]
              const alreadyRated = reviewData?.rating
              const pending = pendingRatings[item.product_id]
              return (
                <div key={i} className="order-item-row">
                  <div className="order-item-info">
                    <span className="order-item-name">{item.name}</span>
                    <span className="order-item-qty">×{item.quantity}</span>
                  </div>
                  <span className="order-item-price">
                    {(item.price * item.quantity).toLocaleString('vi-VN')}đ
                  </span>
                  {/* Rating UI — only for delivered orders */}
                  {order.status === 'delivered' && (
                    <div className="order-item-rating">
                      {alreadyRated ? (
                        <span className="rating-done">
                          <StarRating value={alreadyRated} onChange={() => {}} disabled />
                          <span className="rating-done-text">Đã đánh giá</span>
                          {reviewData.feedback && (
                            <div className="rating-feedback-display">"{reviewData.feedback}"</div>
                          )}
                        </span>
                      ) : (
                        <div className="rating-pending-wrap">
                          <span className="rating-pending">
                            <StarRating
                              value={pending || 0}
                              onChange={v => setPendingRatings(prev => ({ ...prev, [item.product_id]: v }))}
                              disabled={submitting}
                            />
                            {pending && <span className="rating-stars-text">{pending}/5</span>}
                          </span>
                          {pending && (
                            <textarea
                              className="rating-feedback-input"
                              placeholder="Viết nhận xét của bạn (tuỳ chọn)..."
                              value={pendingFeedback[item.product_id] || ''}
                              onChange={e => setPendingFeedback(prev => ({ ...prev, [item.product_id]: e.target.value }))}
                              disabled={submitting}
                              rows={2}
                              maxLength={500}
                            />
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {/* Batch submit button */}
          {order.status === 'delivered' && Object.keys(pendingRatings).length > 0 && (
            <div className="rating-batch-submit">
              <button
                className="rating-batch-btn"
                onClick={handleSubmitAll}
                disabled={submitting}
              >
                {submitting
                  ? 'Đang gửi...'
                  : `Gửi đánh giá (${Object.keys(pendingRatings).length} sản phẩm)`}
              </button>
            </div>
          )}
        </div>

        {/* Tổng tiền */}
        <div className="order-detail-summary">
          {order.shipping_address && (
            <div className="order-shipping-address">
              <h4>Địa chỉ giao hàng</h4>
              <p><strong>{order.shipping_address.full_name}</strong> — {order.shipping_address.phone}</p>
              <p>{order.shipping_address.address}</p>
            </div>
          )}
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

      {/* Toast notification */}
      {toast && (
        <div className={`toast-notification ${toast.type}`}>
          {toast.type === 'success' ? '✅' : '❌'} {toast.message}
        </div>
      )}
    </div>
  )
}
