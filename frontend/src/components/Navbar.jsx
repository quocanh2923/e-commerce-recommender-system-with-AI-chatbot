import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'
import './Navbar.css'

export default function Navbar() {
  const { user, logout } = useAuth()
  const { totalItems } = useCart()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="navbar-logo">ShopAI</Link>

        <div className="navbar-search">
          <input type="text" placeholder="Tìm kiếm sản phẩm..." />
          <button>Tìm</button>
        </div>

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
