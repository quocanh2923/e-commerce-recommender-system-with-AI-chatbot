import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../../context/AuthContext'

export default function AdminUsers() {
  const { authFetch } = useAuth()
  const [data, setData]   = useState({ users: [], total: 0 })
  const [loading, setLoading] = useState(true)
  const [page, setPage]   = useState(1)

  const fetchUsers = useCallback(async () => {
    setLoading(true)
    const params = new URLSearchParams({ page, limit: 20 })
    const res = await authFetch(`http://127.0.0.1:8000/admin/users?${params}`)
    if (res.ok) setData(await res.json())
    setLoading(false)
  }, [page])

  useEffect(() => { fetchUsers() }, [fetchUsers])

  const totalPages = Math.ceil(data.total / 20)

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <h1 className="admin-page-title">Quản lý người dùng <span className="admin-count">({data.total})</span></h1>
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
              </tr>
            </thead>
            <tbody>
              {data.users.map((u, i) => (
                <tr key={u._id}>
                  <td>{(page - 1) * 20 + i + 1}</td>
                  <td><strong>{u.username}</strong></td>
                  <td>{u.email}</td>
                  <td>{u.full_name || '—'}</td>
                  <td>
                    <span className={`role-badge ${u.role === 'admin' ? 'admin' : 'user'}`}>
                      {u.role === 'admin' ? 'Admin' : 'User'}
                    </span>
                  </td>
                </tr>
              ))}
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
