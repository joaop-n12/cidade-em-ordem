import { createContext, useContext, useState } from 'react'
import { gravar, hashSenha, ler, novoId, remover } from '../services/storage'

// Login local: usuários ficam no localStorage do próprio navegador, com senha
// em hash SHA-256 + sal. Nenhum dado sai do dispositivo (LGPD: minimização).

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(() => ler('sessao', null))

  async function cadastrar({ nome, email, senha, perfil, consentimento }) {
    if (!consentimento) throw new Error('É necessário aceitar o uso dos dados para criar a conta.')
    if (senha.length < 6) throw new Error('A senha deve ter pelo menos 6 caracteres.')
    const usuarios = ler('usuarios', [])
    const emailNorm = email.trim().toLowerCase()
    if (usuarios.some((u) => u.email === emailNorm)) throw new Error('Já existe uma conta com este e-mail.')
    const sal = novoId('sal')
    const novo = {
      id: novoId('usr'),
      nome: nome.trim(),
      email: emailNorm,
      perfil,
      sal,
      senhaHash: await hashSenha(senha, sal),
      consentimentoEm: new Date().toISOString(),
    }
    gravar('usuarios', [...usuarios, novo])
    return entrarComo(novo)
  }

  async function entrar(email, senha) {
    const usuarios = ler('usuarios', [])
    const u = usuarios.find((x) => x.email === email.trim().toLowerCase())
    // Mensagem genérica: não revela se o e-mail existe.
    if (!u || (await hashSenha(senha, u.sal)) !== u.senhaHash) throw new Error('E-mail ou senha inválidos.')
    return entrarComo(u)
  }

  function entrarComo(u) {
    const sessao = { id: u.id, nome: u.nome, email: u.email, perfil: u.perfil }
    gravar('sessao', sessao)
    setUsuario(sessao)
    return sessao
  }

  function sair() {
    remover('sessao')
    setUsuario(null)
  }

  // Direito de eliminação (LGPD, art. 18): apaga a conta do navegador.
  function excluirConta() {
    if (!usuario) return
    gravar('usuarios', ler('usuarios', []).filter((u) => u.id !== usuario.id))
    sair()
  }

  return (
    <AuthContext.Provider value={{ usuario, cadastrar, entrar, sair, excluirConta }}>{children}</AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  return useContext(AuthContext)
}
