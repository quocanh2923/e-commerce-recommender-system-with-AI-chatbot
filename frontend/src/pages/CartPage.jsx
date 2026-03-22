import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useCart } from '../context/CartContext'
import { useAuth } from '../context/AuthContext'
import './CartPage.css'

const SHIPPING = 30000

export default function CartPage() {
  const { cart, updateQuantity, removeItem, subtotal, fetchCart } = useCart()
  const { token, authFetch } = useAuth()
  const navigate = useNavigate()
  const [ordering, setOrdering] = useState(false)
  const [orderDone, setOrderDone] = useState(null)

  const items = cart.items ?? []
  const total = subtotal + SHIPPING

  const handleCheckout = async () => {
    setOrdering(true)
    try {
      const res = await authFetch('http://127.0.0.1:8000/orders/', {
        method: 'POST',
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail)
      await fetchCart()   // đồng bộ giỏ hàng về trống
      setOrderDone(data)
    } catch (err) {
      alert('Đặt hàng thất bại: ' + err.message)
    } finally {
      setOrdering(false)
    }
  }

  if (orderDone) {
    return (
      <div className="cart-wrapper">
        <div className="order-success">
          <div className="success-icon">✓</div>
          <h2>Đặt hàng thành công!</h2>
          <p>Mã đơn hàng: <strong>#{orderDone._id?.slice(-8).toUpperCase()}</strong></p>
          <p className="total-confirm">Tổng tiền: <strong>{orderDone.total?.toLocaleString('vi-VN')} ₫</strong></p>
          <div className="success-actions">
            <button onClick={() => navigate('/orders')} className="btn-primary">Xem đơn hàng</button>
            <button onClick={() => navigate('/products')} className="btn-secondary">Tiếp tục mua sắm</button>
          </div>
        </div>
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className="cart-wrapper">
        <div className="cart-empty">
          <p>🛒 Giỏ hàng của bạn đang trống</p>
          <Link to="/" className="btn-primary">Khám phá sản phẩm</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="cart-wrapper">
      <h1>Giỏ hàng</h1>
      <div className="cart-layout">

        {/* Danh sách sản phẩm */}
        <div className="cart-items">
          {items.map((item) => (
            <div key={item.product_id} className="cart-item">
              <div className="cart-item-image">
                <img
                  src={item.image_url || 'https://placehold.co/80x80?text=...'}
                  alt={item.name}
                  onError={(e) => { e.target.src = 'https://placehold.co/80x80?text=...' }}
                />
              </div>
              <div className="cart-item-info">
                <p className="cart-item-name">{item.name}</p>
                <p className="cart-item-price">{item.price.toLocaleString('vi-VN')} ₫</p>
              </div>
              <div className="cart-item-qty">
                <select
                  value={item.quantity}
                  onChange={(e) => updateQuantity(item.product_id, Number(e.target.value))}
                >
                  {[1,2,3,4,5,6,7,8,9,10].map(n => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>
              </div>
              <div className="cart-item-subtotal">
                {(item.price * item.quantity).toLocaleString('vi-VN')} ₫
              </div>
              <button className="cart-item-remove" onClick={() => removeItem(item.product_id)}>
                ✕
              </button>
            </div>
          ))}
        </div>

        {/* Order Summary */}
        <div className="cart-summary">
          <h3>Tóm tắt đơn hàng</h3>
          <div className="summary-row">
            <span>Tạm tính</span>
            <span>{subtotal.toLocaleString('vi-VN')} ₫</span>
          </div>
          <div className="summary-row">
            <span>Phí vận chuyển</span>
            <span>{SHIPPING.toLocaleString('vi-VN')} ₫</span>
          </div>
          <div className="summary-row total">
            <span>Tổng cộng</span>
            <span>{total.toLocaleString('vi-VN')} ₫</span>
          </div>
          <button
            className="btn-checkout"
            onClick={handleCheckout}
            disabled={ordering}
          >
            {ordering ? 'Đang xử lý...' : 'Đặt hàng ngay'}
          </button>
        </div>

      </div>
    </div>
  )
}
