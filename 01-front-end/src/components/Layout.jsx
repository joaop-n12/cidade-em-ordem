import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

export default function Layout() {
  const { usuario, sair } = useAuth()
  const navigate = useNavigate()
  const [fonteGrande, setFonteGrande] = useState(false)

  return (
    <div className={fonteGrande ? 'app fonte-grande' : 'app'}>
      <a href="#conteudo" className="pular-link">Pular para o conteúdo</a>
      <header className="topo">
        <div className="marca">
          <span aria-hidden="true" className="marca-icone">◆</span>
          <span>Cidade em Ordem</span>
        </div>
        <nav aria-label="Navegação principal">
          <ul className="menu">
            <li><NavLink to="/" end>Painel</NavLink></li>
            <li><NavLink to="/ocorrencias">Ocorrências</NavLink></li>
            <li><NavLink to="/ocorrencias/nova">Registrar</NavLink></li>
            <li><NavLink to="/assistente">Assistente</NavLink></li>
            {usuario?.perfil === 'gestor' && <li><NavLink to="/importar">Importar detecções</NavLink></li>}
            <li><NavLink to="/sobre">Sobre / LGPD</NavLink></li>
          </ul>
        </nav>
        <div className="usuario">
          <button
            type="button"
            className="botao-secundario"
            aria-pressed={fonteGrande}
            onClick={() => setFonteGrande((v) => !v)}
          >
            A+ <span className="sr-only">aumentar fonte</span>
          </button>
          <span>
            {usuario?.nome} <small>({usuario?.perfil === 'gestor' ? 'Gestor' : 'Cidadão'})</small>
          </span>
          <button
            type="button"
            className="botao-secundario"
            onClick={() => {
              sair()
              navigate('/login')
            }}
          >
            Sair
          </button>
        </div>
      </header>
      <main id="conteudo" tabIndex={-1}>
        <Outlet />
      </main>
      <footer className="rodape">
        Global Solution 2026.2 · CitizenTech · ODS 9 e 11 · Protótipo acadêmico com dados sintéticos
      </footer>
    </div>
  )
}
