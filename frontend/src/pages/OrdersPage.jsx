import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './OrdersPage.css'

const STATUS_LABEL = {
  pending:    { text: 'Pending',    color: '#f59e0b' },
  processing: { text: 'Processing', color: '#3b82f6' },
  shipped:    { text: 'Shipped',    color: '#8b5cf6' },
  delivered:  { text: 'Delivered', color: '#10b981' },
  cancelled:  { text: 'Cancelled', color: '#ef4444' },
}

export default function OrdersPage() {
  const { token, authFetch } = useAuth()
  const navigate = useNavigate()
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    authFetch('http://127.0.0.1:8000/orders/')
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then(data => { setOrders(data); setLoading(false) })
      .catch(err => { setError(err.message); setLoading(false) })
  }, [token])

  if (loading) return <div className="orders-container"><p className="orders-status">Loading orders...</p></div>
  if (error)   return <div className="orders-container"><p className="orders-status error">Error: {error}</p></div>

  return (
    <div className="orders-container">
      <div className="orders-header">
        <h1>My Orders</h1>
        <Link to="/products" className="orders-shop-btn">Continue Shopping →</Link>
      </div>

      {orders.length === 0 ? (
        <div className="orders-empty">
          <div className="orders-empty-icon">📦</div>
          <p>You don't have any orders yet.</p>
          <Link to="/products" className="orders-shop-btn">Explore Products</Link>
        </div>
      ) : (
        <div className="orders-list">
          {orders.map(order => {
            const s = STATUS_LABEL[order.status] || STATUS_LABEL.pending
            const date = new Date(order.created_at).toLocaleDateString('vi-VN', {
              day: '2-digit', month: '2-digit', year: 'numeric',
              hour: '2-digit', minute: '2-digit'
            })
            return (
              <div
                key={order._id}
                className="order-card"
                onClick={() => navigate(`/orders/${order._id}`)}
              >
                <div className="order-card-top">
                  <div>
                    <span className="order-id">#{order._id.slice(-8).toUpperCase()}</span>
                    <span className="order-date">{date}</span>
                  </div>
                  <span className="order-status-badge" style={{ background: s.color + '20', color: s.color }}>
                    {s.text}
                  </span>
                </div>

                <div className="order-items-preview">
                  {order.items.slice(0, 3).map((item, i) => (
                    <span key={i} className="order-item-pill">
                      {item.name} ×{item.quantity}
                    </span>
                  ))}
                  {order.items.length > 3 && (
                    <span className="order-item-pill order-item-more">+{order.items.length - 3} more</span>
                  )}
                </div>

                <div className="order-card-bottom">
                  <span className="order-total">
                    Total: <strong>{order.total.toLocaleString('vi-VN')}₫</strong>
                  </span>
                  <span className="order-detail-link">View Details →</span>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
