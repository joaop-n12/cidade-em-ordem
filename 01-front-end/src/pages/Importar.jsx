import { useState } from 'react'
import { importarDeteccoes, restaurarExemplo } from '../services/ocorrencias'

export default function Importar() {
  const [resultado, setResultado] = useState(null)
  const [erro, setErro] = useState('')

  async function lerArquivo(e) {
    setErro('')
    setResultado(null)
    const arquivo = e.target.files?.[0]
    if (!arquivo) return
    try {
      const dados = JSON.parse(await arquivo.text())
      setResultado(importarDeteccoes(dados))
    } catch (err) {
      setErro(err instanceof SyntaxError ? 'O arquivo não é um JSON válido.' : err.message)
    }
  }

  return (
    <section aria-labelledby="titulo-importar">
      <h1 id="titulo-importar">Importar detecções automáticas</h1>
      <p className="subtitulo">
        Envie o arquivo <code>ordens_servico.json</code> gerado pelo robô RPA (pasta <code>06-rpa/saida</code>). Ele junta as
        detecções da câmera (visão computacional) e do sensor IoT do caminhão. Registros já importados são ignorados.
      </p>
      <div className="cartao">
        <label htmlFor="arquivo">Arquivo JSON</label>
        <input id="arquivo" type="file" accept="application/json,.json" onChange={lerArquivo} />
        {erro && <p role="alert" className="erro">{erro}</p>}
        {resultado && (
          <div role="status" className="sucesso">
            <p>{resultado.importadas} ocorrência(s) importada(s), {resultado.ignoradas} já existiam.</p>
            {resultado.erros.length > 0 && (
              <ul>{resultado.erros.map((x) => <li key={x}>{x}</li>)}</ul>
            )}
          </div>
        )}
      </div>
      <button type="button" className="botao-secundario" onClick={() => { restaurarExemplo(); setResultado(null) }}>
        Restaurar dados de exemplo
      </button>
    </section>
  )
}
