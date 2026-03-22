import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import './ChatWidget.css'

const API_URL = 'http://127.0.0.1:8000'

const QUICK_QUESTIONS = [
  'Gợi ý áo cho tôi',
  'Có giày thể thao không?',
  'Sản phẩm nào đang hot?',
  'Chính sách đổi trả?',
]

export default function ChatWidget() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Xin chào! Tôi là ShopBot 🤖\nTôi có thể giúp bạn tìm sản phẩm, tư vấn thời trang, và giải đáp thắc mắc. Hãy hỏi tôi nhé!' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)
  const navigate = useNavigate()

  // Auto-scroll khi có tin nhắn mới
  useEffect(() => {
    if (open) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, open])

  // Focus vào input khi mở
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [open])

  const sendMessage = async (text) => {
    const trimmed = (text || input).trim()
    if (!trimmed || loading) return

    const userMsg = { role: 'user', content: trimmed }
    const newMessages = [...messages, userMsg]
    setMessages(newMessages)
    setInput('')
    setLoading(true)

    // Giu toi da 10 tin nhan cu lam lich su (khong tinh tin nhan chao dau)
    const history = newMessages.slice(1).slice(-10).map(m => ({
      role: m.role,
      content: m.content
    }))

    try {
      const res = await fetch(`${API_URL}/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, history: history.slice(0, -1) })
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || `HTTP ${res.status}`)
      }

      const data = await res.json()
      const assistantMsg = {
        role: 'assistant',
        content: data.reply,
        products: data.products || []
      }
      setMessages(prev => [...prev, assistantMsg])
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Xin lỗi, có lỗi xảy ra: ${err.message}. Vui lòng thử lại sau.`
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <>
      {/* ── Cửa sổ chat ── */}
      {open && (
        <div className="chat-window">
          <div className="chat-header">
            <div className="chat-header-info">
              <div className="chat-avatar">🤖</div>
              <div>
                <div className="chat-title">ShopBot</div>
                <div className="chat-subtitle">Trợ lý mua sắm AI</div>
              </div>
            </div>
            <button className="chat-close-btn" onClick={() => setOpen(false)}>✕</button>
          </div>

          <div className="chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-msg chat-msg--${msg.role}`}>
                <div className="chat-bubble">
                  {msg.content.split('\n').map((line, j) => (
                    <span key={j}>{line}{j < msg.content.split('\n').length - 1 && <br />}</span>
                  ))}
                </div>

                {/* Sản phẩm gợi ý đính kèm */}
                {msg.products && msg.products.length > 0 && (
                  <div className="chat-products">
                    <p className="chat-products-label">Sản phẩm liên quan:</p>
                    <div className="chat-products-list">
                      {msg.products.slice(0, 3).map((p) => (
                        <div
                          key={p._id}
                          className="chat-product-card"
                          onClick={() => { navigate(`/products/${p._id}`); setOpen(false) }}
                        >
                          {p.image_url && (
                            <img
                              src={p.image_url}
                              alt={p.name}
                              className="chat-product-img"
                              onError={(e) => { e.target.style.display = 'none' }}
                            />
                          )}
                          <div className="chat-product-info">
                            <p className="chat-product-name">{p.name}</p>
                            <p className="chat-product-price">{p.price?.toLocaleString('vi-VN')}đ</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="chat-msg chat-msg--assistant">
                <div className="chat-bubble chat-bubble--typing">
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Câu hỏi nhanh */}
          {messages.length <= 2 && (
            <div className="chat-quick">
              {QUICK_QUESTIONS.map((q) => (
                <button key={q} className="chat-quick-btn" onClick={() => sendMessage(q)}>
                  {q}
                </button>
              ))}
            </div>
          )}

          <div className="chat-input-area">
            <textarea
              ref={inputRef}
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Nhập tin nhắn... (Enter để gửi)"
              rows={1}
              disabled={loading}
            />
            <button
              className="chat-send-btn"
              onClick={() => sendMessage()}
              disabled={!input.trim() || loading}
            >
              ➤
            </button>
          </div>
        </div>
      )}

      {/* ── Nút nổi ── */}
      <button
        className={`chat-fab ${open ? 'chat-fab--open' : ''}`}
        onClick={() => setOpen(!open)}
        aria-label="Mở chatbot"
      >
        {open ? '✕' : '💬'}
      </button>
    </>
  )
}
