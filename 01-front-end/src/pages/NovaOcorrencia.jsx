import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import Prioridade from '../components/Prioridade'
import { useAuth } from '../context/AuthContext'
import { TIPOS, classificarOcorrencia } from '../ia/classificador'
import { criarOcorrencia } from '../services/ocorrencias'

const VAZIO = {
  tipo: '', descricao: '', endereco: '', lat: '-23.5405', lng: '-46.5762', via: 'local',
  fonte: 'cidadao', confianca: '', impactoG: '', profundidadeCm: '', chovendo: false,
}

export default function NovaOcorrencia() {
  const { usuario } = useAuth()
  const [form, setForm] = useState(VAZIO)
  const [salva, setSalva] = useState(null)
  const [erro, setErro] = useState('')

  const mudar = (campo) => (e) =>
    setForm((f) => ({ ...f, [campo]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }))

  const dadosNumericos = {
    ...form,
    confianca: form.confianca === '' ? null : Number(form.confianca) / 100,
    impactoG: form.impactoG === '' ? null : Number(form.impactoG),
    profundidadeCm: form.profundidadeCm === '' ? null : Number(form.profundidadeCm),
  }

  // Prévia ao vivo: o resultado da IA muda conforme o usuário preenche.
  const previa = useMemo(() => classificarOcorrencia(dadosNumericos), [form]) // eslint-disable-line react-hooks/exhaustive-deps

  function usarMinhaLocalizacao() {
    if (!navigator.geolocation) return setErro('Seu navegador não permite obter a localização.')
    navigator.geolocation.getCurrentPosition(
      (p) => setForm((f) => ({ ...f, lat: p.coords.latitude.toFixed(5), lng: p.coords.longitude.toFixed(5) })),
      () => setErro('Não foi possível obter a localização. Informe o endereço manualmente.'),
    )
  }

  function enviar(e) {
    e.preventDefault()
    setErro('')
    if (!form.endereco.trim()) return setErro('Informe o endereço ou ponto de referência.')
    if (!form.tipo && !form.descricao.trim()) return setErro('Escolha o tipo ou descreva o problema.')
    if (dadosNumericos.confianca !== null && (dadosNumericos.confianca < 0 || dadosNumericos.confianca > 1))
      return setErro('A confiança da câmera deve estar entre 0 e 100.')
    setSalva(criarOcorrencia(dadosNumericos, usuario))
    setForm(VAZIO)
  }

  return (
    <section aria-labelledby="titulo-nova">
      <h1 id="titulo-nova">Registrar ocorrência</h1>
      <p className="subtitulo">
        A maior parte das ocorrências chega sozinha pelos caminhões. Use este formulário para um registro manual
        (cidadão ou fiscal) ou para simular uma leitura da câmera e do sensor.
      </p>

      <div className="duas-colunas">
        <form onSubmit={enviar} className="cartao" noValidate>
          <label htmlFor="tipo">Tipo de problema</label>
          <select id="tipo" value={form.tipo} onChange={mudar('tipo')}>
            <option value="">Deixar a IA identificar pela descrição</option>
            {Object.entries(TIPOS).map(([k, v]) => <option key={k} value={k}>{v.rotulo}</option>)}
          </select>

          <label htmlFor="descricao">Descrição</label>
          <textarea id="descricao" rows={3} value={form.descricao} onChange={mudar('descricao')}
            placeholder="Ex.: buraco grande na frente da escola, motos desviando" />

          <label htmlFor="endereco">Endereço ou referência</label>
          <input id="endereco" value={form.endereco} onChange={mudar('endereco')} required />

          <div className="linha">
            <div>
              <label htmlFor="lat">Latitude</label>
              <input id="lat" inputMode="decimal" value={form.lat} onChange={mudar('lat')} />
            </div>
            <div>
              <label htmlFor="lng">Longitude</label>
              <input id="lng" inputMode="decimal" value={form.lng} onChange={mudar('lng')} />
            </div>
          </div>
          <button type="button" className="botao-secundario" onClick={usarMinhaLocalizacao}>Usar minha localização</button>

          <label htmlFor="via">Tipo de via</label>
          <select id="via" value={form.via} onChange={mudar('via')}>
            <option value="local">Local (rua de bairro)</option>
            <option value="coletora">Coletora</option>
            <option value="arterial">Arterial (avenida movimentada)</option>
          </select>

          <details>
            <summary>Dados da câmera e do sensor (simulação)</summary>
            <label htmlFor="fonte">Origem</label>
            <select id="fonte" value={form.fonte} onChange={mudar('fonte')}>
              <option value="cidadao">Cidadão</option>
              <option value="camera">Câmera do caminhão</option>
              <option value="sensor">Sensor IoT do caminhão</option>
              <option value="camera+sensor">Câmera + sensor</option>
            </select>
            <label htmlFor="confianca">Confiança da visão computacional (%)</label>
            <input id="confianca" type="number" min="0" max="100" value={form.confianca} onChange={mudar('confianca')} />
            <label htmlFor="impactoG">Impacto no acelerômetro (g)</label>
            <input id="impactoG" type="number" step="0.1" min="0" value={form.impactoG} onChange={mudar('impactoG')} />
            <label htmlFor="profundidadeCm">Profundidade pelo sensor ultrassônico (cm)</label>
            <input id="profundidadeCm" type="number" min="0" value={form.profundidadeCm} onChange={mudar('profundidadeCm')} />
          </details>

          <label className="opcao">
            <input type="checkbox" checked={form.chovendo} onChange={mudar('chovendo')} /> Chuva prevista para a região
          </label>

          <p className="aviso">Não inclua nomes, telefones ou placas de veículos na descrição.</p>
          {erro && <p role="alert" className="erro">{erro}</p>}
          <button type="submit">Registrar</button>
        </form>

        <aside className="cartao" aria-labelledby="titulo-ia" aria-live="polite">
          <h2 id="titulo-ia">Análise da IA</h2>
          <p><strong>{previa.tipoRotulo}</strong></p>
          <Prioridade valor={previa.prioridade} />
          <p>Escore de gravidade: <strong>{previa.escore}/100</strong></p>
          <div className="barra" aria-hidden="true"><div style={{ width: `${previa.escore}%` }} /></div>
          <p><strong>Ação gerada:</strong> {previa.acao}</p>
          <h3>Por que essa prioridade?</h3>
          <ul>
            {previa.fatores.map((f) => <li key={f.motivo}>{f.motivo} <small>(+{f.pontos})</small></li>)}
          </ul>
          <p className="aviso">A IA apoia a triagem. A gravidade real é confirmada pela vistoria da equipe.</p>
        </aside>
      </div>

      {salva && (
        <div className="cartao sucesso" role="status">
          Ocorrência registrada com prioridade {salva.ia.prioridade}. {salva.ia.acao}{' '}
          <Link to={`/ocorrencias/${salva.id}`}>Ver ocorrência</Link>
        </div>
      )}
    </section>
  )
}
