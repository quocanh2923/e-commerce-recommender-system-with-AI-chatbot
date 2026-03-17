import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import '../App.css'

export default function HomePage() {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    fetch('http://127.0.0.1:8000/products/')
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then(data => { setProducts(data); setLoading(false) })
      .catch(err => { setError(err.message); setLoading(false) })
  }, [])

  if (loading) return <div className="container"><p className="status-msg">Đang tải sản phẩm...</p></div>
  if (error) return <div className="container"><p className="status-msg error">Lỗi: {error}</p></div>

  return (
    <div className="container">
      <h1>Sản phẩm nổi bật</h1>
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
              {product.description && <p className="description">{product.description}</p>}
              <p className="price">{product.price.toLocaleString('vi-VN')} ₫</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
