import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './NotificationBell.css'

export default function NotificationBell({ isAdmin = false }) {
  const { user, authFetch } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [data, setData] = useState({ notifications: [], unread: 0 })
  const ref = useRef()

  const apiBase = isAdmin
    ? 'http://127.0.0.1:8000/notifications/admin?limit=15'
    : 'http://127.0.0.1:8000/notifications/?limit=15'

  const fetchNotifications = async () => {
    if (!user) return
    try {
      const res = await authFetch(apiBase)
      if (res.ok) setData(await res.json())
    } catch {}
  }

  useEffect(() => {
    fetchNotifications()
    const timer = setInterval(fetchNotifications, 30000)
    return () => clearInterval(timer)
  }, [user])

  // Close on outside click
  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleOpen = () => {
    setOpen(prev => !prev)
  }

  const handleMarkAllRead = async () => {
    await authFetch('http://127.0.0.1:8000/notifications/read-all', { method: 'PUT' })
    setData(prev => ({
      ...prev,
      unread: 0,
      notifications: prev.notifications.map(n => ({ ...n, is_read: true })),
    }))
  }

  const handleClick = async (noti) => {
    if (!noti.is_read) {
      await authFetch(`http://127.0.0.1:8000/notifications/${noti._id}/read`, { method: 'PUT' })
      setData(prev => ({
        ...prev,
        unread: Math.max(0, prev.unread - 1),
        notifications: prev.notifications.map(n => n._id === noti._id ? { ...n, is_read: true } : n),
      }))
    }
    setOpen(false)
    if (noti.link) navigate(noti.link)
  }

  const timeAgo = (dateStr) => {
    // Ensure UTC parsing — backend stores UTC but may omit timezone suffix
    const utcStr = dateStr && !dateStr.endsWith('Z') && !dateStr.includes('+') ? dateStr + 'Z' : dateStr
    const diff = Date.now() - new Date(utcStr).getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return 'Just now'
    if (mins < 60) return `${mins} minutes ago`
    const hours = Math.floor(mins / 60)
    if (hours < 24) return `${hours} hours ago`
    const days = Math.floor(hours / 24)
    return `${days} days ago`
  }

  if (!user) return null

  return (
    <div className="noti-bell-wrap" ref={ref}>
      <button className="noti-bell-btn" onClick={handleOpen}>
        🔔
        {data.unread > 0 && <span className="noti-badge">{data.unread > 9 ? '9+' : data.unread}</span>}
      </button>

      {open && (
        <div className="noti-dropdown">
          <div className="noti-dropdown-header">
            <span className="noti-dropdown-title">Notifications</span>
            {data.unread > 0 && (
              <button className="noti-mark-all" onClick={handleMarkAllRead}>Mark all read</button>
            )}
          </div>

          <div className="noti-dropdown-list">
            {data.notifications.length === 0 ? (
              <div className="noti-empty">No notifications</div>
            ) : (
              data.notifications.map(noti => (
                <div
                  key={noti._id}
                  className={`noti-item ${!noti.is_read ? 'unread' : ''}`}
                  onClick={() => handleClick(noti)}
                >
                  <div className="noti-item-icon">
                    {noti.type === 'order' ? '📦' : noti.type === 'review' ? '⭐' : '🔔'}
                  </div>
                  <div className="noti-item-content">
                    <div className="noti-item-title">{noti.title}</div>
                    <div className="noti-item-msg">{noti.message}</div>
                    <div className="noti-item-time">{timeAgo(noti.created_at)}</div>
                  </div>
                  {!noti.is_read && <span className="noti-item-dot" />}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
