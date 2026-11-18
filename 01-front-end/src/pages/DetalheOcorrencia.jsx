import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import MapaOcorrencias from '../components/MapaOcorrencias'
import Prioridade from '../components/Prioridade'
import { useAuth } from '../context/AuthContext'
import { STATUS, atualizarStatus, buscarOcorrencia } from '../services/ocorrencias'

export default function DetalheOcorrencia() {
  const { id } = useParams()
  const { usuario } = useAuth()
  const [o, setO] = useState(() => buscarOcorrencia(id))

  if (!o) {
    return (
      <section>
        <h1>Ocorrência não encontrada</h1>
        <Link to="/ocorrencias">Voltar para a lista</Link>
      </section>
    )
  }

  function mudarStatus(e) {
    atualizarStatus(o.id, e.target.value, usuario)
    setO(buscarOcorrencia(o.id))
  }

  return (
    <section aria-labelledby="titulo-detalhe">
      <Link to="/ocorrencias">← Voltar</Link>
      <h1 id="titulo-detalhe">{o.ia.tipoRotulo}</h1>
      <p className="subtitulo">{o.endereco}</p>
      <Prioridade valor={o.ia.prioridade} />

      <div className="duas-colunas">
        <div className="cartao">
          <h2>Evidências</h2>
          <dl className="dados">
            <dt>Origem</dt><dd>{o.fonte}</dd>
            <dt>Confiança da câmera</dt><dd>{o.confianca != null ? `${Math.round(o.confianca * 100)}%` : 'Sem imagem'}</dd>
            <dt>Impacto no sensor</dt><dd>{o.impactoG != null ? `${o.impactoG} g` : 'Sem leitura'}</dd>
            <dt>Profundidade</dt><dd>{o.profundidadeCm != null ? `${o.profundidadeCm} cm` : 'Sem leitura'}</dd>
            <dt>Detecções no mesmo ponto</dt><dd>{o.reincidencias}</dd>
            <dt>Descrição</dt><dd>{o.descricao || '—'}</dd>
          </dl>

          <h2>Decisão da IA</h2>
          <p>Escore {o.ia.escore}/100 · prazo {o.ia.prazo} · {o.ia.secretaria}</p>
          <p><strong>Ação:</strong> {o.ia.acao}</p>
          <ul>
            {o.ia.fatores.map((f) => <li key={f.motivo}>{f.motivo} <small>(+{f.pontos})</small></li>)}
          </ul>

          <label htmlFor="status">Status</label>
          {usuario?.perfil === 'gestor' ? (
            <select id="status" value={o.status} onChange={mudarStatus}>
              {STATUS.map((s) => <option key={s}>{s}</option>)}
            </select>
          ) : (
            <p id="status">{o.status}</p>
          )}
        </div>

        <div>
          <MapaOcorrencias ocorrencias={[o]} altura={260} />
          <div className="cartao">
            <h2>Histórico</h2>
            <ol className="historico">
              {o.historico.map((h, i) => (
                <li key={i}><time dateTime={h.quando}>{new Date(h.quando).toLocaleString('pt-BR')}</time> — {h.evento}</li>
              ))}
            </ol>
          </div>
        </div>
      </div>
    </section>
  )
}
