import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import Prioridade from '../components/Prioridade'
import { TIPOS } from '../ia/classificador'
import { STATUS, listarOcorrencias } from '../services/ocorrencias'

const FONTES = { camera: 'Câmera', sensor: 'Sensor IoT', 'camera+sensor': 'Câmera + sensor', cidadao: 'Cidadão', 'robô RPA': 'Robô RPA' }

export default function Ocorrencias() {
  const todas = useMemo(() => listarOcorrencias(), [])
  const [busca, setBusca] = useState('')
  const [tipo, setTipo] = useState('')
  const [status, setStatus] = useState('')

  const filtradas = todas.filter(
    (o) =>
      (!tipo || o.tipo === tipo) &&
      (!status || o.status === status) &&
      (!busca || o.endereco.toLowerCase().includes(busca.toLowerCase())),
  )

  return (
    <section aria-labelledby="titulo-lista">
      <h1 id="titulo-lista">Consultar ocorrências</h1>

      <form className="filtros" onSubmit={(e) => e.preventDefault()} role="search">
        <div>
          <label htmlFor="busca">Buscar por endereço</label>
          <input id="busca" value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Ex.: Tuiuti" />
        </div>
        <div>
          <label htmlFor="tipo">Tipo</label>
          <select id="tipo" value={tipo} onChange={(e) => setTipo(e.target.value)}>
            <option value="">Todos</option>
            {Object.entries(TIPOS).map(([k, v]) => <option key={k} value={k}>{v.rotulo}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="status">Status</label>
          <select id="status" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">Todos</option>
            {STATUS.map((s) => <option key={s}>{s}</option>)}
          </select>
        </div>
      </form>

      <p aria-live="polite">{filtradas.length} ocorrência(s) encontrada(s).</p>

      <div className="tabela-rolagem">
        <table>
          <caption className="sr-only">Lista de ocorrências</caption>
          <thead>
            <tr>
              <th scope="col">Tipo</th>
              <th scope="col">Endereço</th>
              <th scope="col">Origem</th>
              <th scope="col">Prioridade</th>
              <th scope="col">Status</th>
              <th scope="col">Registro</th>
            </tr>
          </thead>
          <tbody>
            {filtradas.map((o) => (
              <tr key={o.id}>
                <td><Link to={`/ocorrencias/${o.id}`}>{o.ia.tipoRotulo}</Link></td>
                <td>{o.endereco}</td>
                <td>{FONTES[o.fonte] ?? o.fonte}</td>
                <td><Prioridade valor={o.ia.prioridade} /></td>
                <td>{o.status}</td>
                <td>{new Date(o.criadaEm).toLocaleDateString('pt-BR')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
