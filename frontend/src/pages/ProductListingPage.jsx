import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useCart } from '../context/CartContext'
import './ProductListingPage.css'

const API_URL = 'http://127.0.0.1:8000'

const CATEGORIES = ['Áo', 'Quần', 'Giày', 'Túi', 'Phụ kiện', 'Váy', 'Đồng hồ', 'Đồ lót', 'Đồ bơi', 'Vớ']
const SORT_OPTIONS = [
  { value: 'newest', label: 'Mới nhất' },
  { value: 'price_asc', label: 'Giá: Thấp → Cao' },
  { value: 'price_desc', label: 'Giá: Cao → Thấp' },
  { value: 'rating', label: 'Đánh giá cao nhất' },
]

function StarRating({ rating = 0 }) {
  return (
    <span className="star-rating">
      {[1, 2, 3, 4, 5].map((s) => (
        <span key={s} className={s <= Math.round(rating) ? 'star filled' : 'star'}>★</span>
      ))}
      <span className="rating-value">({rating.toFixed(1)})</span>
    </span>
  )
}

export default function ProductListingPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { addToCart } = useCart()

  // --- State đồng bộ với URL ---
  const [searchInput, setSearchInput] = useState(searchParams.get('search') || '')
  const [selectedCategory, setSelectedCategory] = useState(searchParams.get('category') || '')
  const [minPrice, setMinPrice] = useState(searchParams.get('min_price') || '')
  const [maxPrice, setMaxPrice] = useState(searchParams.get('max_price') || '')
  const [sortBy, setSortBy] = useState(searchParams.get('sort_by') || 'newest')

  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const LIMIT = 12

  // --- Gọi API ---
  const fetchProducts = useCallback(async (params, pageNum = 0) => {
    setLoading(true)
    try {
      const query = new URLSearchParams()
      if (params.search) query.set('search', params.search)
      if (params.category) query.set('category', params.category)
      if (params.min_price) query.set('min_price', params.min_price)
      if (params.max_price) query.set('max_price', params.max_price)
      query.set('sort_by', params.sort_by || 'newest')
      query.set('limit', LIMIT)
      query.set('skip', pageNum * LIMIT)

      const res = await fetch(`${API_URL}/products/?${query.toString()}`)
      const data = await res.json()
      if (pageNum === 0) {
        setProducts(data)
      } else {
        setProducts((prev) => [...prev, ...data])
      }
      setTotal((pageNum + 1) * LIMIT + (data.length === LIMIT ? 1 : 0))
    } catch {
      // silently fail
    } finally {
      setLoading(false)
    }
  }, [])

  // Khi URL params thay đổi → fetch lại
  useEffect(() => {
    const params = {
      search: searchParams.get('search') || '',
      category: searchParams.get('category') || '',
      min_price: searchParams.get('min_price') || '',
      max_price: searchParams.get('max_price') || '',
      sort_by: searchParams.get('sort_by') || 'newest',
    }
    setSearchInput(params.search)
    setSelectedCategory(params.category)
    setMinPrice(params.min_price)
    setMaxPrice(params.max_price)
    setSortBy(params.sort_by)
    setPage(0)
    fetchProducts(params, 0)
  }, [searchParams, fetchProducts])

  // --- Helper: cập nhật URL giữ nguyên các param khác ---
  const updateParams = useCallback((overrides) => {
    const current = Object.fromEntries(searchParams.entries())
    const merged = { ...current, ...overrides }
    // Xoá key rỗng
    Object.keys(merged).forEach((k) => { if (!merged[k]) delete merged[k] })
    if (!merged.sort_by) merged.sort_by = 'newest'
    setSearchParams(merged)
  }, [searchParams, setSearchParams])

  // --- Debounce search: gõ xong 400ms mới search ---
  const searchTimer = useRef(null)
  const handleSearchChange = (value) => {
    setSearchInput(value)
    clearTimeout(searchTimer.current)
    searchTimer.current = setTimeout(() => {
      updateParams({ search: value.trim(), skip: undefined })
    }, 400)
  }

  // --- Category: click thẳng → filter ngay ---
  const handleCategoryClick = (cat) => {
    const next = cat === selectedCategory ? '' : cat
    setSelectedCategory(next)
    updateParams({ category: next })
  }

  // --- Áp dụng chỉ cho khoảng giá ---
  const applyPriceFilter = () => {
    updateParams({ min_price: minPrice, max_price: maxPrice })
  }

  const clearFilters = () => {
    setSearchInput('')
    setSelectedCategory('')
    setMinPrice('')
    setMaxPrice('')
    setSortBy('newest')
    setSearchParams({ sort_by: 'newest' })
  }

  const handleSortChange = (value) => {
    setSortBy(value)
    const params = Object.fromEntries(searchParams.entries())
    params.sort_by = value
    setSearchParams(params)
  }

  const handleLoadMore = () => {
    const nextPage = page + 1
    setPage(nextPage)
    const params = {
      search: searchParams.get('search') || '',
      category: searchParams.get('category') || '',
      min_price: searchParams.get('min_price') || '',
      max_price: searchParams.get('max_price') || '',
      sort_by: searchParams.get('sort_by') || 'newest',
    }
    fetchProducts(params, nextPage)
  }

  const hasActiveFilter =
    searchParams.get('search') ||
    searchParams.get('category') ||
    searchParams.get('min_price') ||
    searchParams.get('max_price')

  return (
    <div className="listing-container">
      {/* ===== SIDEBAR ===== */}
      <aside className="listing-sidebar">
        <h3 className="sidebar-title">Bộ lọc</h3>

        {/* Tìm kiếm */}
        <div className="sidebar-section">
          <label className="sidebar-label">Tìm kiếm</label>
          <input
            type="text"
            className="sidebar-input"
            placeholder="Tên sản phẩm..."
            value={searchInput}
            onChange={(e) => handleSearchChange(e.target.value)}
          />
        </div>

        {/* Danh mục */}
        <div className="sidebar-section">
          <label className="sidebar-label">Danh mục</label>
          <div className="category-list">
            <button
              className={`category-btn ${selectedCategory === '' ? 'active' : ''}`}
              onClick={() => handleCategoryClick('')}
            >
              Tất cả
            </button>
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                className={`category-btn ${selectedCategory === cat ? 'active' : ''}`}
                onClick={() => handleCategoryClick(cat)}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Khoảng giá */}
        <div className="sidebar-section">
          <label className="sidebar-label">Khoảng giá (VNĐ)</label>
          <div className="price-range">
            <input
              type="number"
              className="sidebar-input price-input"
              placeholder="Từ"
              value={minPrice}
              onChange={(e) => setMinPrice(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && applyPriceFilter()}
              min={0}
            />
            <span className="price-dash">–</span>
            <input
              type="number"
              className="sidebar-input price-input"
              placeholder="Đến"
              value={maxPrice}
              onChange={(e) => setMaxPrice(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && applyPriceFilter()}
              min={0}
            />
          </div>
        </div>

        <button className="filter-apply-btn" onClick={applyPriceFilter}>
          Áp dụng giá
        </button>
        {hasActiveFilter && (
          <button className="filter-clear-btn" onClick={clearFilters}>
            Xóa bộ lọc
          </button>
        )}
      </aside>

      {/* ===== MAIN CONTENT ===== */}
      <main className="listing-main">
        {/* Toolbar */}
        <div className="listing-toolbar">
          <span className="listing-count">
            {products.length} sản phẩm
            {hasActiveFilter && <span className="filter-tag"> (đã lọc)</span>}
          </span>
          <div className="sort-wrapper">
            <label>Sắp xếp: </label>
            <select value={sortBy} onChange={(e) => handleSortChange(e.target.value)}>
              {SORT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Grid */}
        {loading && products.length === 0 ? (
          <div className="listing-loading">
            <span className="spinner" />
            <p>Đang tải sản phẩm...</p>
          </div>
        ) : products.length === 0 ? (
          <div className="listing-empty">
            <p>Không tìm thấy sản phẩm nào.</p>
            <button className="filter-clear-btn" onClick={clearFilters}>Xóa bộ lọc</button>
          </div>
        ) : (
          <>
            <div className="product-grid">
              {products.map((p) => (
                <div
                  key={p._id}
                  className="product-card"
                  onClick={() => navigate(`/products/${p._id}`)}
                >
                  <div className="product-img-wrap">
                    {p.image_url ? (
                      <img src={p.image_url} alt={p.name} className="product-img" />
                    ) : (
                      <div className="product-img-placeholder">No Image</div>
                    )}
                  </div>
                  <div className="product-info">
                    <span className="product-category-badge">{p.category}</span>
                    <h4 className="product-name">{p.name}</h4>
                    <StarRating rating={p.rating || 0} />
                    <div className="product-footer">
                      <span className="product-price">
                        {p.price.toLocaleString('vi-VN')}đ
                      </span>
                      <button
                        className="add-cart-btn"
                        onClick={(e) => {
                          e.stopPropagation()
                          addToCart(p)
                        }}
                      >
                        + Giỏ hàng
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Load more */}
            {products.length % LIMIT === 0 && (
              <div className="load-more-wrap">
                <button
                  className="load-more-btn"
                  onClick={handleLoadMore}
                  disabled={loading}
                >
                  {loading ? 'Đang tải...' : 'Xem thêm'}
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}
