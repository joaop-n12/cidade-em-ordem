import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import RotaProtegida from './components/RotaProtegida'
import { AuthProvider } from './context/AuthContext'
import Assistente from './pages/Assistente'
import Cadastro from './pages/Cadastro'
import DetalheOcorrencia from './pages/DetalheOcorrencia'
import Importar from './pages/Importar'
import Login from './pages/Login'
import NovaOcorrencia from './pages/NovaOcorrencia'
import Ocorrencias from './pages/Ocorrencias'
import Painel from './pages/Painel'
import Sobre from './pages/Sobre'

function NaoEncontrada() {
  return (
    <section>
      <h1>Página não encontrada</h1>
      <Link to="/">Voltar ao painel</Link>
    </section>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/cadastro" element={<Cadastro />} />
          <Route
            element={
              <RotaProtegida>
                <Layout />
              </RotaProtegida>
            }
          >
            <Route index element={<Painel />} />
            <Route path="ocorrencias" element={<Ocorrencias />} />
            <Route path="ocorrencias/nova" element={<NovaOcorrencia />} />
            <Route path="ocorrencias/:id" element={<DetalheOcorrencia />} />
            <Route path="assistente" element={<Assistente />} />
            <Route
              path="importar"
              element={
                <RotaProtegida perfil="gestor">
                  <Importar />
                </RotaProtegida>
              }
            />
            <Route path="sobre" element={<Sobre />} />
            <Route path="*" element={<NaoEncontrada />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
