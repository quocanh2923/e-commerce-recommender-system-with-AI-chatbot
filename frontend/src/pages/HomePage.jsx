import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import RecommendSection from '../components/RecommendSection'
import '../App.css'

export default function HomePage() {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()
  const { user, token } = useAuth()

  useEffect(() => {
    fetch('http://127.0.0.1:8000/products/?limit=8&sort_by=newest')
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then(data => { setProducts(data); setLoading(false) })
      .catch(err => { setError(err.message); setLoading(false) })
  }, [])

  return (
    <div>
      {/* ── Hero Banner ── */}
      <div className="hero-banner">
        <div className="hero-content">
          <h1>Khám phá thời trang <span className="hero-highlight">AI</span></h1>
          <p>Gợi ý sản phẩm thông minh dành riêng cho bạn</p>
          <Link to="/products" className="hero-btn">Mua sắm ngay →</Link>
        </div>
      </div>

      {/* ── Sản phẩm mới nhất ── */}
      <div className="container">
        <div className="section-header">
          <h2>Sản phẩm mới nhất</h2>
          <Link to="/products" className="view-all-link">Xem tất cả →</Link>
        </div>

        {loading ? (
          <p className="status-msg">Đang tải...</p>
        ) : error ? (
          <p className="status-msg error">Lỗi: {error}</p>
        ) : (
          <div className="products-grid">
            {products.map((product) => (
              <div
                key={product._id}
                className="product-card"
                onClick={() => navigate(`/products/${product._id}`)}
              >
                <div className="product-image">
                  <img
                    src={product.image_url || 'https://placehold.co/300x200?text=No+Image'}
                    alt={product.name}
                    onError={(e) => { e.target.src = 'https://placehold.co/300x200?text=No+Image' }}
                  />
                </div>
                <div className="product-info">
                  <span className="category">{product.category}</span>
                  <h3>{product.name}</h3>
                  <p className="price">{product.price.toLocaleString('vi-VN')} ₫</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Gợi ý cá nhân (nếu đã đăng nhập) ── */}
      {user && token ? (
        <RecommendSection
          type="for-you"
          token={token}
          title={`Gợi ý cho bạn, ${user.username} ✨`}
          limit={8}
        />
      ) : (
        <RecommendSection
          type="popular"
          title="Sản phẩm phổ biến 🔥"
          limit={8}
        />
      )}

      {/* ── Luôn hiển thị popular ở cuối nếu đã login ── */}
      {user && (
        <RecommendSection
          type="popular"
          title="Được yêu thích nhiều nhất 🔥"
          limit={8}
        />
      )}
    </div>
  )
}
