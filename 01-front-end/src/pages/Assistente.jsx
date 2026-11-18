import { useRef, useState } from 'react'
import { perguntarAssistente } from '../ia/assistente'

const SUGESTOES = [
  'Meu pneu estourou num buraco, tenho direito a indenização?',
  'Quando vão arrumar minha rua?',
  'Quem é responsável pela calçada?',
  'Onde descarto entulho?',
  'Como o sistema encontra os buracos?',
]

export default function Assistente() {
  const [mensagens, setMensagens] = useState([
    { de: 'assistente', texto: 'Olá! Tire dúvidas sobre buracos, calçadas, lixo nas ruas e seus direitos.' },
  ])
  const [pergunta, setPergunta] = useState('')
  const [carregando, setCarregando] = useState(false)
  const campo = useRef(null)

  async function enviar(texto) {
    const t = texto.trim()
    if (!t || carregando) return
    setMensagens((m) => [...m, { de: 'cidadao', texto: t }])
    setPergunta('')
    setCarregando(true)
    const r = await perguntarAssistente(t)
    setMensagens((m) => [...m, { de: 'assistente', texto: r.resposta, fonte: r.fonte, modo: r.modo }])
    setCarregando(false)
    campo.current?.focus()
  }

  return (
    <section aria-labelledby="titulo-assistente">
      <h1 id="titulo-assistente">Assistente do cidadão</h1>
      <p className="subtitulo">As respostas são baseadas em leis e cartilhas públicas. O assistente informa, mas não substitui um advogado ou o atendimento da prefeitura.</p>

      <div className="chat cartao" aria-live="polite">
        {mensagens.map((m, i) => (
          <div key={i} className={`balao ${m.de}`}>
            <span className="sr-only">{m.de === 'cidadao' ? 'Você disse:' : 'Assistente:'}</span>
            <p>{m.texto}</p>
            {m.fonte && <small>Fonte: {m.fonte}{m.modo === 'rag' ? ' (RAG)' : ''}</small>}
          </div>
        ))}
        {carregando && <p className="balao assistente">Consultando as fontes…</p>}
      </div>

      <div className="sugestoes" aria-label="Perguntas sugeridas">
        {SUGESTOES.map((s) => (
          <button key={s} type="button" className="botao-secundario" onClick={() => enviar(s)}>{s}</button>
        ))}
      </div>

      <form className="linha-chat" onSubmit={(e) => { e.preventDefault(); enviar(pergunta) }}>
        <label htmlFor="pergunta" className="sr-only">Sua pergunta</label>
        <input id="pergunta" ref={campo} value={pergunta} onChange={(e) => setPergunta(e.target.value)} placeholder="Digite sua pergunta" />
        <button type="submit" disabled={carregando}>Enviar</button>
      </form>
    </section>
  )
}
