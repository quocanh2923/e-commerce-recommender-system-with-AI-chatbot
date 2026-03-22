import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../../context/AuthContext'

export default function AdminUsers() {
  const { authFetch } = useAuth()
  const [data, setData]   = useState({ users: [], total: 0 })
  const [loading, setLoading] = useState(true)
  const [page, setPage]   = useState(1)
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [toggling, setToggling] = useState(null)

  const fetchUsers = useCallback(async () => {
    setLoading(true)
    const params = new URLSearchParams({ page, limit: 20, ...(search ? { search } : {}) })
    const res = await authFetch(`http://127.0.0.1:8000/admin/users?${params}`)
    if (res.ok) setData(await res.json())
    setLoading(false)
  }, [page, search])

  useEffect(() => { fetchUsers() }, [fetchUsers])

  const handleSearch = (e) => {
    e.preventDefault()
    setPage(1)
    setSearch(searchInput.trim())
  }

  const handleToggleBlock = async (userId, currentBlocked) => {
    setToggling(userId)
    const res = await authFetch(`http://127.0.0.1:8000/admin/users/${userId}/block`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_blocked: !currentBlocked }),
    })
    if (res.ok) {
      setData(prev => ({
        ...prev,
        users: prev.users.map(u => u._id === userId ? { ...u, is_blocked: !currentBlocked } : u),
      }))
    }
    setToggling(null)
  }

  const totalPages = Math.ceil(data.total / 20)

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <h1 className="admin-page-title">Quản lý người dùng <span className="admin-count">({data.total})</span></h1>
      </div>

      {/* Search */}
      <div className="admin-toolbar">
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: 8 }}>
          <input
            className="admin-input"
            type="text"
            placeholder="Tìm theo tên, email..."
            value={searchInput}
            onChange={e => setSearchInput(e.target.value)}
            style={{ minWidth: 260 }}
          />
          <button type="submit" className="admin-btn primary">Tìm</button>
          {search && (
            <button type="button" className="admin-btn outline" onClick={() => { setSearchInput(''); setSearch(''); setPage(1) }}>Xoá lọc</button>
          )}
        </form>
      </div>

      {loading ? <div className="admin-loading">Đang tải...</div> : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Username</th>
                <th>Email</th>
                <th>Họ tên</th>
                <th>Vai trò</th>
                <th>Trạng thái</th>
                <th>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {data.users.map((u, i) => {
                const blocked = u.is_blocked
                return (
                  <tr key={u._id} className={blocked ? 'row-blocked' : ''}>
                    <td>{(page - 1) * 20 + i + 1}</td>
                    <td><strong>{u.username}</strong></td>
                    <td>{u.email}</td>
                    <td>{u.full_name || '—'}</td>
                    <td>
                      <span className={`role-badge ${u.role === 'admin' ? 'admin' : 'user'}`}>
                        {u.role === 'admin' ? 'Admin' : 'User'}
                      </span>
                    </td>
                    <td>
                      <span className={`status-badge-sm ${blocked ? 'blocked' : 'active'}`}>
                        {blocked ? '🔒 Đã khoá' : '✅ Hoạt động'}
                      </span>
                    </td>
                    <td>
                      {u.role !== 'admin' && (
                        <button
                          className={`admin-btn sm ${blocked ? 'success' : 'danger'}`}
                          disabled={toggling === u._id}
                          onClick={() => handleToggleBlock(u._id, blocked)}
                        >
                          {toggling === u._id ? '...' : blocked ? 'Mở khoá' : 'Khoá'}
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="admin-pagination">
          <button disabled={page === 1} onClick={() => setPage(p => p - 1)}>‹</button>
          <span>Trang {page} / {totalPages}</span>
          <button disabled={page === totalPages} onClick={() => setPage(p => p + 1)}>›</button>
        </div>
      )}
    </div>
  )
}
