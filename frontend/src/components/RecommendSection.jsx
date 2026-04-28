import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCart } from '../context/CartContext'
import API_URL from '../config'
import './RecommendSection.css'

function StarRating({ rating = 0 }) {
  return (
    <span className="rec-stars">
      {[1, 2, 3, 4, 5].map((s) => (
        <span key={s} className={s <= Math.round(rating) ? 'rec-star filled' : 'rec-star'}>★</span>
      ))}
    </span>
  )
}

/**
 * Props:
 *  - type: 'popular' | 'for-you' | 'similar'
 *  - productId: string (chi dung khi type='similar')
 *  - token: string | null (chi dung khi type='for-you')
 *  - title: string
 *  - limit: number
 */
export default function RecommendSection({ type, productId, token, title, limit = 8 }) {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()
  const { addToCart } = useCart()

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        let url = ''
        const headers = {}

        if (type === 'popular') {
          url = `${API_URL}/recommend/popular?limit=${limit}`
        } else if (type === 'for-you') {
          if (!token) { setLoading(false); return }
          url = `${API_URL}/recommend/for-you?limit=${limit}`
          headers['Authorization'] = `Bearer ${token}`
        } else if (type === 'similar') {
          if (!productId) { setLoading(false); return }
          url = `${API_URL}/recommend/similar/${productId}?limit=${limit}`
        }

        const res = await fetch(url, { headers })
        const data = await res.json()
        setProducts(Array.isArray(data) ? data : [])
      } catch {
        setProducts([])
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [type, productId, token, limit])

  if (loading) return (
    <div className="rec-section">
      <h2 className="rec-title">{title}</h2>
      <div className="rec-loading">
        <span className="rec-spinner" />
      </div>
    </div>
  )

  if (!products.length) return null

  return (
    <section className="rec-section">
      <h2 className="rec-title">{title}</h2>
      <div className="rec-grid">
        {products.map((p) => (
          <div
            key={p._id}
            className="rec-card"
            onClick={() => navigate(`/products/${p._id}`)}
          >
            <div className="rec-img-wrap">
              {p.image_url ? (
                <img src={p.image_url} alt={p.name} className="rec-img" />
              ) : (
                <div className="rec-img-placeholder">No Image</div>
              )}
            </div>
            <div className="rec-info">
              <span className="rec-category">{p.category}</span>
              <p className="rec-name">{p.name}</p>
              <StarRating rating={p.rating || 0} />
              <div className="rec-footer">
                <span className="rec-price">{p.price.toLocaleString('vi-VN')}đ</span>
                <button
                  className="rec-cart-btn"
                  onClick={(e) => { e.stopPropagation(); addToCart(p) }}
                >
                  + Giỏ
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
