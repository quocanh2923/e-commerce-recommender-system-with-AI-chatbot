import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'
import RecommendSection from '../components/RecommendSection'
import './ProductDetailPage.css'

export default function ProductDetailPage() {
  const { id } = useParams()
  const { user, token } = useAuth()
  const { addToCart } = useCart()
  const navigate = useNavigate()

  const [product, setProduct] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [addedToCart, setAddedToCart] = useState(false)

  useEffect(() => {
    setLoading(true)
    fetch(`http://127.0.0.1:8000/products/${id}`)
      .then(res => {
        if (!res.ok) throw new Error('Không tìm thấy sản phẩm')
        return res.json()
      })
      .then(data => { setProduct(data); setLoading(false) })
      .catch(err => { setError(err.message); setLoading(false) })
  }, [id])

  // Ghi interaction "view"
  useEffect(() => {
    if (!product || !user || !token) return
    fetch(`http://127.0.0.1:8000/interactions/?product_id=${product._id}&action_type=view`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    }).catch(() => {})
  }, [product, user, token])

  const handleAddToCart = async () => {
    if (!user) { navigate('/login'); return }
    const ok = await addToCart(product)
    if (ok) {
      setAddedToCart(true)
      setTimeout(() => setAddedToCart(false), 2000)
    }
  }

  if (loading) return <div className="detail-loading">Đang tải...</div>
  if (error) return <div className="detail-loading error">{error}</div>
  if (!product) return null

  return (
    <div className="detail-wrapper">
      <button className="back-btn" onClick={() => navigate(-1)}>← Quay lại</button>

      <div className="detail-main">
        {/* Ảnh sản phẩm */}
        <div className="detail-image-section">
          <div className="detail-image-main">
            <img
              src={product.image_url || 'https://placehold.co/500x400?text=No+Image'}
              alt={product.name}
              onError={(e) => { e.target.src = 'https://placehold.co/500x400?text=No+Image' }}
            />
          </div>
        </div>

        {/* Thông tin sản phẩm */}
        <div className="detail-info-section">
          <span className="detail-category">{product.category}</span>
          <h1 className="detail-name">{product.name}</h1>
          <p className="detail-price">{product.price.toLocaleString('vi-VN')} ₫</p>

          {product.description && (
            <div className="detail-description">
              <h4>Mô tả sản phẩm</h4>
              <p>{product.description}</p>
            </div>
          )}

          <button
            className={`add-to-cart-btn ${addedToCart ? 'added' : ''}`}
            onClick={handleAddToCart}
          >
            {addedToCart ? '✓ Đã thêm vào giỏ!' : 'Thêm vào giỏ hàng'}
          </button>

          {!user && (
            <p className="login-hint">
              <a href="/login">Đăng nhập</a> để thêm vào giỏ hàng
            </p>
          )}
        </div>
      </div>

      {/* ── Sản phẩm tương tự ── */}
      <RecommendSection
        type="similar"
        productId={id}
        title="Sản phẩm tương tự"
        limit={8}
      />
    </div>
  )
}
