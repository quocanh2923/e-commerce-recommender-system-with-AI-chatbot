import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute, AdminRoute } from './components/ProtectedRoute'
import Navbar from './components/Navbar'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Navbar />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          {/* Các trang sẽ bổ sung sau */}
          {/* <Route path="/products/:id" element={<ProductDetailPage />} /> */}
          {/* <Route path="/cart" element={<ProtectedRoute><CartPage /></ProtectedRoute>} /> */}
          {/* <Route path="/admin" element={<AdminRoute><AdminDashboard /></AdminRoute>} /> */}
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App

