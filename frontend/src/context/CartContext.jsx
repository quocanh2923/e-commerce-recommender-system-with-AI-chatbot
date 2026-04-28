import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react'
import { useAuth } from './AuthContext'
import API_URL from '../config'

const CartContext = createContext(null)

export function CartProvider({ children }) {
  const { user, token, authFetch } = useAuth()
  const [cart, setCart] = useState({ items: [] })
  const [loading, setLoading] = useState(false)
  const [cartToast, setCartToast] = useState(null)
  const toastTimer = useRef(null)

  const showCartToast = (message) => {
    if (toastTimer.current) clearTimeout(toastTimer.current)
    setCartToast(message)
    toastTimer.current = setTimeout(() => setCartToast(null), 2500)
  }

  const fetchCart = useCallback(async () => {
    if (!token) { setCart({ items: [] }); return }
    setLoading(true)
    try {
      const res = await authFetch(`${API_URL}/cart/`)
      if (res.ok) setCart(await res.json())
    } finally {
      setLoading(false)
    }
  }, [token, authFetch])

  // Load giỏ khi user đăng nhập / đăng xuất
  useEffect(() => { fetchCart() }, [fetchCart])

  const addToCart = async (product) => {
    if (!token) return false
    const res = await authFetch(`${API_URL}/cart/items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        product_id: product._id,
        name: product.name,
        price: product.price,
        quantity: 1,
        image_url: product.image_url || null,
      }),
    })
    if (res.ok) {
      setCart(await res.json())
      showCartToast('Đã thêm vào giỏ hàng')
      return true
    }
    return false
  }

  const updateQuantity = async (productId, quantity) => {
    const res = await authFetch(
      `${API_URL}/cart/items/${productId}?quantity=${quantity}`,
      { method: 'PUT' }
    )
    if (res.ok) setCart(await res.json())
  }

  const removeItem = async (productId) => {
    const res = await authFetch(`${API_URL}/cart/items/${productId}`, {
      method: 'DELETE',
    })
    if (res.ok) setCart(await res.json())
  }

  const totalItems = cart.items?.reduce((sum, i) => sum + i.quantity, 0) ?? 0
  const subtotal = cart.items?.reduce((sum, i) => sum + i.price * i.quantity, 0) ?? 0

  return (
    <CartContext.Provider value={{ cart, loading, addToCart, updateQuantity, removeItem, fetchCart, totalItems, subtotal }}>
      {children}
      {cartToast && (
        <div className="cart-toast-popup">
          <span className="cart-toast-icon">✓</span> {cartToast}
        </div>
      )}
    </CartContext.Provider>
  )
}

export function useCart() {
  return useContext(CartContext)
}
