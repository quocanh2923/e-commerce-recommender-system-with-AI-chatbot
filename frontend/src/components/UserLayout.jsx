import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'
import ChatWidget from './ChatWidget'

export default function UserLayout() {
  return (
    <>
      <Navbar />
      <Outlet />
      <ChatWidget />
    </>
  )
}
