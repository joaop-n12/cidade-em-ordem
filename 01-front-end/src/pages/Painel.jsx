import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import MapaOcorrencias from '../components/MapaOcorrencias'
import Prioridade from '../components/Prioridade'
import { listarOcorrencias } from '../services/ocorrencias'

const PESO = { Crítica: 4, Alta: 3, Média: 2, Baixa: 1 }

export default function Painel() {
  const ocorrencias = useMemo(() => listarOcorrencias(), [])
  const abertas = ocorrencias.filter((o) => o.status !== 'Concluída')
  const automaticas = ocorrencias.filter((o) => o.fonte !== 'cidadao').length
  const criticas = abertas.filter((o) => o.ia.prioridade === 'Crítica').length
  const revisao = abertas.filter((o) => o.ia.precisaRevisao).length

  // Fila de atendimento: maior prioridade primeiro, depois maior escore.
  const fila = [...abertas]
    .sort((a, b) => PESO[b.ia.prioridade] - PESO[a.ia.prioridade] || b.ia.escore - a.ia.escore)
    .slice(0, 5)

  return (
    <section aria-labelledby="titulo-painel">
      <h1 id="titulo-painel">Painel da cidade</h1>
      <p className="subtitulo">
        Ocorrências detectadas automaticamente pela câmera e pelo sensor dos caminhões de coleta, além dos registros feitos por cidadãos.
      </p>

      <div className="indicadores">
        <div className="cartao indicador"><span className="numero">{abertas.length}</span> ocorrências em aberto</div>
        <div className="cartao indicador"><span className="numero">{criticas}</span> com prioridade crítica</div>
        <div className="cartao indicador">
          <span className="numero">{ocorrencias.length ? Math.round((automaticas / ocorrencias.length) * 100) : 0}%</span>
          encontradas sem precisar de reclamação
        </div>
        <div className="cartao indicador"><span className="numero">{revisao}</span> aguardando revisão humana</div>
      </div>

      <MapaOcorrencias ocorrencias={ocorrencias} />

      <h2>Fila de atendimento sugerida pela IA</h2>
      <ol className="lista-fila">
        {fila.map((o) => (
          <li key={o.id} className="cartao">
            <div>
              <Link to={`/ocorrencias/${o.id}`}><strong>{o.ia.tipoRotulo}</strong></Link> · {o.endereco}
              <p className="detalhe">{o.ia.acao}</p>
            </div>
            <Prioridade valor={o.ia.prioridade} />
          </li>
        ))}
      </ol>
    </section>
  )
}
