import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function RotaProtegida({ children, perfil }) {
  const { usuario } = useAuth()
  const location = useLocation()
  if (!usuario) return <Navigate to="/login" replace state={{ de: location.pathname }} />
  if (perfil && usuario.perfil !== perfil) return <Navigate to="/" replace />
  return children
}
