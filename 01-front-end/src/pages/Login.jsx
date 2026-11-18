import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { entrar } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState('')

  async function enviar(e) {
    e.preventDefault()
    setErro('')
    try {
      await entrar(email, senha)
      navigate(location.state?.de ?? '/', { replace: true })
    } catch (err) {
      setErro(err.message)
    }
  }

  return (
    <main className="tela-acesso" id="conteudo">
      <div className="cartao acesso">
        <h1>Cidade em Ordem</h1>
        <p className="subtitulo">A cidade encontra o problema antes de você precisar reclamar.</p>
        <form onSubmit={enviar} noValidate>
          <label htmlFor="email">E-mail</label>
          <input id="email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          <label htmlFor="senha">Senha</label>
          <input id="senha" type="password" autoComplete="current-password" required value={senha} onChange={(e) => setSenha(e.target.value)} />
          {erro && <p role="alert" className="erro">{erro}</p>}
          <button type="submit">Entrar</button>
        </form>
        <p>
          Não tem conta? <Link to="/cadastro">Criar conta</Link>
        </p>
      </div>
    </main>
  )
}
