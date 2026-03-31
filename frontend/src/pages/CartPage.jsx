import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useCart } from '../context/CartContext'
import { useAuth } from '../context/AuthContext'
import './CartPage.css'

const SHIPPING = 30000

export default function CartPage() {
  const { cart, updateQuantity, removeItem, subtotal, fetchCart } = useCart()
  const { user, authFetch } = useAuth()
  const navigate = useNavigate()
  const [ordering, setOrdering] = useState(false)
  const [orderDone, setOrderDone] = useState(null)
  const [showAddressForm, setShowAddressForm] = useState(false)

  const [address, setAddress] = useState({
    full_name: '',
    phone: '',
    address: '',
  })
  const [addressErr, setAddressErr] = useState({})

  // Tự điền từ profile nếu có
  useEffect(() => {
    if (user) {
      setAddress({
        full_name: user.full_name || '',
        phone: user.phone || '',
        address: user.address || '',
      })
    }
  }, [user])

  const items = cart.items ?? []
  const total = subtotal + SHIPPING

  const validateAddress = () => {
    const errs = {}
    if (!address.full_name.trim()) errs.full_name = 'Please enter your full name'
    if (!address.phone.trim() || address.phone.trim().length < 8) errs.phone = 'Invalid phone number'
    if (!address.address.trim() || address.address.trim().length < 5) errs.address = 'Please enter a complete address'
    return errs
  }

  const handleCheckoutClick = () => {
    setAddressErr({})
    setShowAddressForm(true)
  }

  const handleCheckout = async () => {
    const errs = validateAddress()
    if (Object.keys(errs).length > 0) {
      setAddressErr(errs)
      return
    }
    setOrdering(true)
    try {
      const res = await authFetch('http://127.0.0.1:8000/orders/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ shipping_address: address }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail)
      await fetchCart()
      setOrderDone(data)
    } catch (err) {
      alert('Order failed: ' + err.message)
    } finally {
      setOrdering(false)
    }
  }

  if (orderDone) {
    return (
      <div className="cart-wrapper">
        <div className="order-success">
          <div className="success-icon">✓</div>
          <h2>Order Placed Successfully!</h2>
          <p>Order ID: <strong>#{orderDone._id?.slice(-8).toUpperCase()}</strong></p>
          <p className="total-confirm">Total: <strong>{orderDone.total?.toLocaleString('vi-VN')} ₫</strong></p>
          {orderDone.shipping_address && (
            <p className="success-address">
              Deliver to: <strong>{orderDone.shipping_address.full_name}</strong> — {orderDone.shipping_address.phone}<br />
              {orderDone.shipping_address.address}
            </p>
          )}
          <div className="success-actions">
            <button onClick={() => navigate('/orders')} className="btn-primary">View Orders</button>
            <button onClick={() => navigate('/products')} className="btn-secondary">Continue Shopping</button>
          </div>
        </div>
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className="cart-wrapper">
        <div className="cart-empty">
          <p>🛒 Your cart is empty</p>
          <Link to="/" className="btn-primary">Explore Products</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="cart-wrapper">
      <h1>Cart</h1>
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
          <h3>Order Summary</h3>
          <div className="summary-row">
            <span>Subtotal</span>
            <span>{subtotal.toLocaleString('vi-VN')} ₫</span>
          </div>
          <div className="summary-row">
            <span>Shipping</span>
            <span>{SHIPPING.toLocaleString('vi-VN')} ₫</span>
          </div>
          <div className="summary-row total">
            <span>Total</span>
            <span>{total.toLocaleString('vi-VN')} ₫</span>
          </div>

          {!showAddressForm ? (
            <button className="btn-checkout" onClick={handleCheckoutClick}>
              Checkout
            </button>
          ) : (
            <div className="shipping-form">
              <h4>Shipping Address</h4>
              <div className="shipping-field">
                <label>Full Name *</label>
                <input
                  type="text"
                  value={address.full_name}
                  onChange={(e) => setAddress({ ...address, full_name: e.target.value })}
                  placeholder="Nguyễn Văn A"
                />
                {addressErr.full_name && <span className="field-err">{addressErr.full_name}</span>}
              </div>
              <div className="shipping-field">
                <label>Phone Number *</label>
                <input
                  type="tel"
                  value={address.phone}
                  onChange={(e) => setAddress({ ...address, phone: e.target.value })}
                  placeholder="0901234567"
                />
                {addressErr.phone && <span className="field-err">{addressErr.phone}</span>}
              </div>
              <div className="shipping-field">
                <label>Address *</label>
                <textarea
                  value={address.address}
                  onChange={(e) => setAddress({ ...address, address: e.target.value })}
                  placeholder="House no., street, district, city"
                  rows={3}
                />
                {addressErr.address && <span className="field-err">{addressErr.address}</span>}
              </div>
              <div className="shipping-actions">
                <button
                  className="btn-secondary"
                  onClick={() => setShowAddressForm(false)}
                  disabled={ordering}
                >
                  Back
                </button>
                <button
                  className="btn-checkout"
                  onClick={handleCheckout}
                  disabled={ordering}
                >
                  {ordering ? 'Processing...' : 'Place Order'}
                </button>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  )
}
