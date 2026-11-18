// Assistente do cidadão (versão embarcada no front-end).
// Funciona sem internet: busca a resposta mais relevante numa base de
// conhecimento curta, montada a partir dos mesmos documentos públicos usados
// no módulo de NLP e no RAG de Generative AI. Quando o RAG completo
// (pasta 05-generative-ai) estiver rodando, o front pode chamá-lo pela URL
// configurada em VITE_RAG_URL; se a chamada falhar, cai nesta versão local.

const BASE = [
  {
    id: 'indenizacao',
    termos: ['indenização', 'indenizacao', 'pneu', 'roda', 'carro', 'estragou', 'danificou', 'prejuízo', 'prejuizo', 'ressarcimento'],
    resposta:
      'Se o seu veículo foi danificado por um buraco em via pública, a Constituição (art. 37, § 6º) prevê que o poder público responde pelos danos causados. ' +
      'Em São Paulo, o pedido é gratuito pelo Portal 156, no serviço "Reparação de Danos - Solicitar indenização por danos materiais". ' +
      'Tire fotos do buraco, do veículo e da via, anote endereço, data e horário, e junte a nota fiscal do conserto ou três orçamentos. ' +
      'Se você usar o seguro do carro, a prefeitura cobre apenas a franquia. Se o pedido for negado, procure o Juizado Especial da Fazenda Pública ou a Defensoria Pública.',
    fonte: 'Constituição Federal, art. 37, § 6º; Portal SP156 - Reparação de Danos',
  },
  {
    id: 'prazo',
    termos: ['quando', 'prazo', 'demora', 'arrumar', 'consertar', 'conserto', 'status', 'minha rua'],
    resposta:
      'Cada ocorrência recebe uma prioridade calculada pela IA: Crítica (24 h), Alta (72 h), Média (7 dias) ou Baixa (15 dias). ' +
      'Você pode acompanhar o status na tela "Ocorrências". Os prazos são metas de atendimento do protótipo e dependem da equipe da subprefeitura.',
    fonte: 'Regras de priorização do Cidade em Ordem',
  },
  {
    id: 'calcada',
    termos: ['calçada', 'calcada', 'passeio', 'responsável', 'responsavel', 'dono', 'quem conserta'],
    resposta:
      'Em São Paulo, a conservação da calçada é responsabilidade do proprietário do imóvel em frente, conforme a legislação municipal. ' +
      'A prefeitura fiscaliza e cuida das calçadas de próprios públicos. Calçadas devem ter faixa livre para circulação de pedestres, sem degraus ou obstáculos.',
    fonte: 'Cartilha "Conheça as regras para arrumar a sua calçada" (Prefeitura de São Paulo)',
  },
  {
    id: 'lixo',
    termos: ['lixo', 'entulho', 'descarte', 'sofá', 'sofa', 'móveis', 'moveis', 'ecoponto', 'cata-bagulho'],
    resposta:
      'Entulho e objetos grandes (móveis, colchões) não podem ser deixados na rua. Leve até um Ecoponto ou agende a coleta do Cata-Bagulho da sua região. ' +
      'Descarte irregular entope bueiros e aumenta o risco de alagamentos e de doenças como a dengue.',
    fonte: 'Orientações de limpeza urbana da Prefeitura de São Paulo',
  },
  {
    id: 'acessibilidade',
    termos: ['cadeirante', 'acessibilidade', 'deficiência', 'deficiencia', 'rampa', 'cego', 'idoso'],
    resposta:
      'A Lei Brasileira de Inclusão (Lei 13.146/2015) garante o direito à acessibilidade em vias e espaços públicos. ' +
      'Rampas e calçadas obstruídas ou danificadas recebem pontuação extra de prioridade no Cidade em Ordem.',
    fonte: 'Lei 13.146/2015 (Lei Brasileira de Inclusão)',
  },
  {
    id: 'como-funciona',
    termos: ['como funciona', 'câmera', 'camera', 'sensor', 'caminhão', 'caminhao', 'automático', 'automatico'],
    resposta:
      'Os caminhões de coleta de lixo, que já passam em todas as ruas, levam uma câmera e um sensor. A câmera detecta buracos e lixo acumulado; ' +
      'o sensor mede o impacto quando o caminhão passa por um buraco. Um robô junta essas informações, elimina repetições e abre a ordem de serviço. ' +
      'Assim, o problema é encontrado antes de alguém precisar reclamar.',
    fonte: 'Documentação do Cidade em Ordem',
  },
  {
    id: 'dados',
    termos: ['dados', 'privacidade', 'lgpd', 'rosto', 'placa do carro', 'imagem', 'foto'],
    resposta:
      'O sistema não guarda rostos nem placas de veículos: as imagens são usadas só para detectar o problema na via e o registro salvo contém apenas o tipo, ' +
      'a localização e a confiança. Seus dados de cadastro ficam apenas no seu navegador e podem ser apagados na tela "Sobre".',
    fonte: 'Política de dados do protótipo (LGPD - Lei 13.709/2018)',
  },
  {
    id: 'emergencia',
    termos: ['acidente', 'ferido', 'emergência', 'emergencia', 'socorro', 'samu', 'bombeiro', 'desabou', 'cratera'],
    resposta:
      'Se houver pessoa ferida ou risco imediato (cratera, desabamento, fios caídos), ligue agora: SAMU 192, Bombeiros 193 ou Defesa Civil 199. ' +
      'O assistente não substitui o atendimento de emergência.',
    fonte: 'Telefones oficiais de emergência',
  },
]

const FORA_DO_TEMA =
  'Posso ajudar com buracos, calçadas, lixo nas ruas, sinalização, iluminação e seus direitos sobre esses problemas. ' +
  'Para outros assuntos, procure a Central 156 da prefeitura.'

export function responderLocal(pergunta) {
  const p = pergunta.toLowerCase()
  let melhor = null
  let melhorPontos = 0
  for (const item of BASE) {
    const pontos = item.termos.filter((t) => p.includes(t)).length
    if (pontos > melhorPontos) {
      melhor = item
      melhorPontos = pontos
    }
  }
  if (!melhor) return { resposta: FORA_DO_TEMA, fonte: null, modo: 'local' }
  return { resposta: melhor.resposta, fonte: melhor.fonte, modo: 'local' }
}

export async function perguntarAssistente(pergunta) {
  const url = import.meta.env.VITE_RAG_URL
  if (url) {
    try {
      const ctrl = new AbortController()
      const timer = setTimeout(() => ctrl.abort(), 15000)
      const r = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pergunta }),
        signal: ctrl.signal,
      })
      clearTimeout(timer)
      if (r.ok) {
        const dados = await r.json()
        if (dados?.resposta) return { resposta: dados.resposta, fonte: dados.fontes?.join('; ') ?? null, modo: 'rag' }
      }
    } catch {
      // Caminho seguro: se o RAG estiver fora do ar, usa a base local.
    }
  }
  return responderLocal(pergunta)
}
