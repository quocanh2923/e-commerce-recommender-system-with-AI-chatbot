import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { useAuth } from './AuthContext'

const CartContext = createContext(null)

export function CartProvider({ children }) {
  const { user, token } = useAuth()
  const [cart, setCart] = useState({ items: [] })
  const [loading, setLoading] = useState(false)

  const fetchCart = useCallback(async () => {
    if (!token) { setCart({ items: [] }); return }
    setLoading(true)
    try {
      const res = await fetch('http://127.0.0.1:8000/cart/', {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) setCart(await res.json())
    } finally {
      setLoading(false)
    }
  }, [token])

  // Load giỏ khi user đăng nhập / đăng xuất
  useEffect(() => { fetchCart() }, [fetchCart])

  const addToCart = async (product) => {
    if (!token) return false
    const res = await fetch('http://127.0.0.1:8000/cart/items', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        product_id: product._id,
        name: product.name,
        price: product.price,
        quantity: 1,
        image_url: product.image_url || null,
      }),
    })
    if (res.ok) { setCart(await res.json()); return true }
    return false
  }

  const updateQuantity = async (productId, quantity) => {
    const res = await fetch(
      `http://127.0.0.1:8000/cart/items/${productId}?quantity=${quantity}`,
      { method: 'PUT', headers: { Authorization: `Bearer ${token}` } }
    )
    if (res.ok) setCart(await res.json())
  }

  const removeItem = async (productId) => {
    const res = await fetch(`http://127.0.0.1:8000/cart/items/${productId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    })
    if (res.ok) setCart(await res.json())
  }

  const totalItems = cart.items?.reduce((sum, i) => sum + i.quantity, 0) ?? 0
  const subtotal = cart.items?.reduce((sum, i) => sum + i.price * i.quantity, 0) ?? 0

  return (
    <CartContext.Provider value={{ cart, loading, addToCart, updateQuantity, removeItem, fetchCart, totalItems, subtotal }}>
      {children}
    </CartContext.Provider>
  )
}

export function useCart() {
  return useContext(CartContext)
}
