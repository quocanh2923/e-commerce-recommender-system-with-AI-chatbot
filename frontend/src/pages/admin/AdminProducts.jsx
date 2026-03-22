import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../../context/AuthContext'

const EMPTY_FORM = { name: '', price: '', category: '', description: '', image_url: '', stock: '', rating: '' }

export default function AdminProducts() {
  const { authFetch } = useAuth()
  const [data, setData]       = useState({ products: [], total: 0, page: 1 })
  const [loading, setLoading] = useState(true)
  const [search, setSearch]   = useState('')
  const [page, setPage]       = useState(1)
  const [modal, setModal]     = useState(null)   // null | 'add' | 'edit'
  const [editProduct, setEditProduct] = useState(null)
  const [form, setForm]       = useState(EMPTY_FORM)
  const [saving, setSaving]   = useState(false)
  const [deleteId, setDeleteId] = useState(null)

  const fetchProducts = useCallback(async () => {
    setLoading(true)
    const params = new URLSearchParams({ page, limit: 20, ...(search ? { search } : {}) })
    const res = await authFetch(`http://127.0.0.1:8000/admin/products?${params}`)
    if (res.ok) setData(await res.json())
    setLoading(false)
  }, [page, search])

  useEffect(() => { fetchProducts() }, [fetchProducts])

  const openAdd = () => { setForm(EMPTY_FORM); setEditProduct(null); setModal('add') }
  const openEdit = (p) => {
    setForm({ name: p.name, price: p.price, category: p.category, description: p.description || '', image_url: p.image_url || '', stock: p.stock ?? 0, rating: p.rating ?? 0 })
    setEditProduct(p)
    setModal('edit')
  }

  const handleSave = async () => {
    if (!form.name || !form.price || !form.category) return alert('Vui lòng điền đủ Tên, Giá, Danh mục')
    setSaving(true)
    const payload = { name: form.name, price: Number(form.price), category: form.category, description: form.description, image_url: form.image_url, stock: Number(form.stock) || 0, rating: Number(form.rating) || 0 }
    const url    = modal === 'edit' ? `http://127.0.0.1:8000/admin/products/${editProduct._id}` : 'http://127.0.0.1:8000/admin/products'
    const method = modal === 'edit' ? 'PUT' : 'POST'
    const res = await authFetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
    if (res.ok) { setModal(null); fetchProducts() }
    else { const e = await res.json(); alert(e.detail || 'Lỗi lưu sản phẩm') }
    setSaving(false)
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Xoá sản phẩm này?')) return
    const res = await authFetch(`http://127.0.0.1:8000/admin/products/${id}`, { method: 'DELETE' })
    if (res.ok || res.status === 204) fetchProducts()
    else alert('Xoá thất bại')
  }

  const totalPages = Math.ceil(data.total / 20)

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <h1 className="admin-page-title">Quản lý sản phẩm <span className="admin-count">({data.total})</span></h1>
        <button className="admin-btn primary" onClick={openAdd}>+ Thêm sản phẩm</button>
      </div>

      {/* Search */}
      <div className="admin-toolbar">
        <input
          className="admin-search-input"
          placeholder="Tìm tên sản phẩm..."
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1) }}
        />
      </div>

      {/* Table */}
      {loading ? <div className="admin-loading">Đang tải...</div> : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Ảnh</th>
                <th>Tên sản phẩm</th>
                <th>Danh mục</th>
                <th>Giá</th>
                <th>Tồn kho</th>
                <th>Đánh giá</th>
                <th>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {data.products.map(p => (
                <tr key={p._id}>
                  <td>
                    <img src={p.image_url || 'https://placehold.co/48x48?text=...'} alt={p.name}
                      className="admin-product-img"
                      onError={e => { e.target.src = 'https://placehold.co/48x48?text=...' }} />
                  </td>
                  <td className="product-name-cell">{p.name}</td>
                  <td><span className="category-tag">{p.category}</span></td>
                  <td>{Number(p.price).toLocaleString('vi-VN')} ₫</td>
                  <td>{p.stock ?? 0}</td>
                  <td>⭐ {p.rating ?? 0}</td>
                  <td>
                    <div className="action-btns">
                      <button className="admin-btn sm outline" onClick={() => openEdit(p)}>Sửa</button>
                      <button className="admin-btn sm danger"   onClick={() => handleDelete(p._id)}>Xoá</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="admin-pagination">
          <button disabled={page === 1} onClick={() => setPage(p => p - 1)}>‹</button>
          <span>Trang {page} / {totalPages}</span>
          <button disabled={page === totalPages} onClick={() => setPage(p => p + 1)}>›</button>
        </div>
      )}

      {/* Modal */}
      {modal && (
        <div className="admin-modal-overlay" onClick={() => setModal(null)}>
          <div className="admin-modal" onClick={e => e.stopPropagation()}>
            <h2>{modal === 'edit' ? 'Sửa sản phẩm' : 'Thêm sản phẩm mới'}</h2>
            <div className="admin-form-grid">
              {[
                { key: 'name',        label: 'Tên sản phẩm *',  type: 'text' },
                { key: 'price',       label: 'Giá (₫) *',        type: 'number' },
                { key: 'category',    label: 'Danh mục *',        type: 'text' },
                { key: 'stock',       label: 'Tồn kho',           type: 'number' },
                { key: 'rating',      label: 'Đánh giá (0-5)',    type: 'number' },
                { key: 'image_url',   label: 'URL ảnh',           type: 'text' },
              ].map(f => (
                <label key={f.key} className="admin-form-label">
                  {f.label}
                  <input
                    type={f.type}
                    className="admin-input"
                    value={form[f.key]}
                    onChange={e => setForm(prev => ({ ...prev, [f.key]: e.target.value }))}
                  />
                </label>
              ))}
              <label className="admin-form-label full-width">
                Mô tả
                <textarea
                  className="admin-input"
                  rows={3}
                  value={form.description}
                  onChange={e => setForm(prev => ({ ...prev, description: e.target.value }))}
                />
              </label>
            </div>
            <div className="modal-actions">
              <button className="admin-btn outline" onClick={() => setModal(null)}>Huỷ</button>
              <button className="admin-btn primary" onClick={handleSave} disabled={saving}>
                {saving ? 'Đang lưu...' : 'Lưu'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
