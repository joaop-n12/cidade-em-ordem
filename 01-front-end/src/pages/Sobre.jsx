import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Sobre() {
  const { excluirConta } = useAuth()
  const navigate = useNavigate()

  return (
    <section aria-labelledby="titulo-sobre" className="texto">
      <h1 id="titulo-sobre">Sobre o Cidade em Ordem</h1>

      <h2>O problema</h2>
      <p>
        Hoje, para um buraco ser consertado, alguém precisa reclamar no aplicativo ou na central da prefeitura. Muitos problemas
        ficam meses sem registro, causam acidentes com motos e bicicletas, danificam veículos e dificultam a vida de pedestres,
        idosos e pessoas com deficiência.
      </p>

      <h2>A solução</h2>
      <p>
        Os caminhões de coleta de lixo já passam por todas as ruas várias vezes por semana. Com uma câmera e um sensor de baixo
        custo, eles passam a detectar buracos e lixo acumulado automaticamente. Um robô junta as detecções, elimina repetições,
        calcula a prioridade e abre a ordem de serviço. O cidadão acompanha tudo e tira dúvidas com o assistente.
      </p>

      <h2>Objetivos de Desenvolvimento Sustentável</h2>
      <ul>
        <li><strong>ODS 11 – Cidades e comunidades sustentáveis:</strong> vias e calçadas seguras e acessíveis para todos (meta 11.2).</li>
        <li><strong>ODS 9 – Indústria, inovação e infraestrutura:</strong> infraestrutura de qualidade e resiliente, mantida com apoio de tecnologia (meta 9.1).</li>
        <li><strong>ODS 10 – Redução das desigualdades:</strong> bairros que reclamam menos deixam de ser esquecidos, pois a detecção é igual em todas as ruas.</li>
      </ul>

      <h2>Proteção de dados (LGPD)</h2>
      <ul>
        <li>Pedimos apenas nome e e-mail. Não coletamos CPF, telefone nem endereço do cidadão.</li>
        <li>A senha é guardada como hash SHA-256 com sal, nunca em texto puro.</li>
        <li>Todos os dados ficam somente neste navegador (localStorage).</li>
        <li>As imagens das câmeras são usadas só para detectar o problema na via; rostos e placas não são armazenados.</li>
        <li>Você pode apagar sua conta a qualquer momento (direito de eliminação, art. 18 da LGPD).</li>
      </ul>
      <button
        type="button"
        className="botao-perigo"
        onClick={() => {
          if (window.confirm('Apagar sua conta deste navegador? Esta ação não pode ser desfeita.')) {
            excluirConta()
            navigate('/login')
          }
        }}
      >
        Apagar minha conta
      </button>
    </section>
  )
}
