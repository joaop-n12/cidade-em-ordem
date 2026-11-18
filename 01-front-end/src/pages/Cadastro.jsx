import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Cadastro() {
  const { cadastrar } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ nome: '', email: '', senha: '', perfil: 'cidadao', consentimento: false })
  const [erro, setErro] = useState('')

  const mudar = (campo) => (e) =>
    setForm((f) => ({ ...f, [campo]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }))

  async function enviar(e) {
    e.preventDefault()
    setErro('')
    if (!form.nome.trim() || !form.email.includes('@')) {
      setErro('Preencha nome e um e-mail válido.')
      return
    }
    try {
      await cadastrar(form)
      navigate('/', { replace: true })
    } catch (err) {
      setErro(err.message)
    }
  }

  return (
    <main className="tela-acesso" id="conteudo">
      <div className="cartao acesso">
        <h1>Criar conta</h1>
        <form onSubmit={enviar} noValidate>
          <label htmlFor="nome">Nome</label>
          <input id="nome" autoComplete="name" required value={form.nome} onChange={mudar('nome')} />

          <label htmlFor="email">E-mail</label>
          <input id="email" type="email" autoComplete="email" required value={form.email} onChange={mudar('email')} />

          <label htmlFor="senha">Senha (mínimo 6 caracteres)</label>
          <input id="senha" type="password" autoComplete="new-password" required minLength={6} value={form.senha} onChange={mudar('senha')} />

          <fieldset>
            <legend>Perfil</legend>
            <label className="opcao">
              <input type="radio" name="perfil" value="cidadao" checked={form.perfil === 'cidadao'} onChange={mudar('perfil')} />
              Cidadão: acompanho as ocorrências e tiro dúvidas
            </label>
            <label className="opcao">
              <input type="radio" name="perfil" value="gestor" checked={form.perfil === 'gestor'} onChange={mudar('perfil')} />
              Gestor da prefeitura: atualizo status e importo detecções
            </label>
          </fieldset>

          <label className="opcao consentimento">
            <input type="checkbox" checked={form.consentimento} onChange={mudar('consentimento')} />
            Concordo que meu nome e e-mail fiquem salvos apenas neste navegador para acessar o sistema. Não pedimos CPF,
            telefone ou endereço, e posso apagar minha conta a qualquer momento (LGPD).
          </label>

          {erro && <p role="alert" className="erro">{erro}</p>}
          <button type="submit">Criar conta</button>
        </form>
        <p>
          Já tem conta? <Link to="/login">Entrar</Link>
        </p>
      </div>
    </main>
  )
}
