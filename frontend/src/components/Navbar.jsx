import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'
import NotificationBell from './NotificationBell'
import './Navbar.css'

export default function Navbar() {
  const { user, logout } = useAuth()
  const { totalItems } = useCart()
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const handleSearch = (e) => {
    e.preventDefault()
    const q = searchQuery.trim()
    if (q) {
      navigate(`/products?search=${encodeURIComponent(q)}`)
    } else {
      navigate('/products')
    }
  }

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="navbar-logo">ShopAI</Link>

        <form className="navbar-search" onSubmit={handleSearch}>
          <input
            type="text"
            placeholder="Tìm kiếm sản phẩm..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button type="submit">Tìm</button>
        </form>

        <div className="navbar-actions">
          {user ? (
            <>
              <span className="navbar-username">Xin chào, {user.username}</span>
              {user.role === 'admin' && (
                <Link to="/admin" className="navbar-btn outline">Admin</Link>
              )}
              <Link to="/cart" className="navbar-cart">
                🛒
                {totalItems > 0 && <span className="cart-badge">{totalItems}</span>}
              </Link>
              <NotificationBell />
              <Link to="/orders" className="navbar-btn outline">Đơn hàng</Link>
              <button onClick={handleLogout} className="navbar-btn outline">Đăng xuất</button>
            </>
          ) : (
            <>
              <Link to="/cart" className="navbar-cart">🛒</Link>
              <Link to="/login" className="navbar-btn outline">Đăng nhập</Link>
              <Link to="/register" className="navbar-btn primary">Đăng ký</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
