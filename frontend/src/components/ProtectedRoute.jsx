import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

// Bảo vệ route cần đăng nhập
export function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  return children
}

// Bảo vệ route chỉ dành cho admin
export function AdminRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  if (user.role !== 'admin') return <Navigate to="/" replace />
  return children
}
