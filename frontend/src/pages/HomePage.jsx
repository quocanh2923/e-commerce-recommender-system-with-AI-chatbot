import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import API_URL from '../config'
import RecommendSection from '../components/RecommendSection'
import '../App.css'

export default function HomePage() {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()
  const { user, token } = useAuth()

  useEffect(() => {
    fetch(`${API_URL}/products/?limit=8&sort_by=newest`)
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
          <h1>Discover Fashion with <span className="hero-highlight">AI</span></h1>
          <p>Smart product recommendations tailored for you</p>
          <Link to="/products" className="hero-btn">Shop Now →</Link>
        </div>
      </div>

      {/* ── Sản phẩm mới nhất ── */}
      <div className="container">
        <div className="section-header">
          <h2>Latest Products</h2>
          <Link to="/products" className="view-all-link">View All →</Link>
        </div>

        {loading ? (
          <p className="status-msg">Loading...</p>
        ) : error ? (
          <p className="status-msg error">Error: {error}</p>
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
          title={`For you, ${user.username} ✨`}
          limit={8}
        />
      ) : (
        <RecommendSection
          type="popular"
          title="Popular Products 🔥"
          limit={8}
        />
      )}

      {/* ── Luôn hiển thị popular ở cuối nếu đã login ── */}
      {user && (
        <RecommendSection
          type="popular"
          title="Most Loved 🔥"
          limit={8}
        />
      )}
    </div>
  )
}
