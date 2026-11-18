import { classificarOcorrencia } from '../ia/classificador'
import { OCORRENCIAS_INICIAIS } from '../data/seed'
import { gravar, ler, novoId } from './storage'

export const STATUS = ['Aberta', 'Em vistoria', 'Em execução', 'Concluída']

function montar(dados, autor) {
  const ia = classificarOcorrencia(dados)
  const agora = new Date()
  const criadaEm = dados.criadaEm ?? new Date(agora.getTime() - (dados.diasAtras ?? 0) * 86400000).toISOString()
  return {
    id: dados.id ?? novoId('oc'),
    tipo: ia.tipo,
    fonte: dados.fonte ?? 'cidadao',
    lat: Number(dados.lat),
    lng: Number(dados.lng),
    endereco: dados.endereco ?? '',
    via: dados.via ?? 'local',
    confianca: dados.confianca ?? null,
    impactoG: dados.impactoG ?? null,
    profundidadeCm: dados.profundidadeCm ?? null,
    reincidencias: dados.reincidencias ?? 0,
    chovendo: Boolean(dados.chovendo),
    descricao: dados.descricao ?? '',
    status: dados.status ?? (ia.precisaRevisao ? 'Em vistoria' : 'Aberta'),
    criadaEm,
    autorId: autor?.id ?? null,
    ia,
    historico: dados.historico ?? [{ quando: criadaEm, evento: `Registrada (${dados.fonte ?? 'cidadão'})` }],
  }
}

export function listarOcorrencias() {
  let lista = ler('ocorrencias', null)
  if (!lista) {
    lista = OCORRENCIAS_INICIAIS.map((o) => montar(o))
    gravar('ocorrencias', lista)
  }
  return lista
}

export function buscarOcorrencia(id) {
  return listarOcorrencias().find((o) => o.id === id) ?? null
}

export function criarOcorrencia(dados, autor) {
  const nova = montar(dados, autor)
  gravar('ocorrencias', [nova, ...listarOcorrencias()])
  return nova
}

export function atualizarStatus(id, status, autor) {
  const lista = listarOcorrencias().map((o) =>
    o.id === id
      ? {
          ...o,
          status,
          historico: [...o.historico, { quando: new Date().toISOString(), evento: `Status alterado para "${status}" por ${autor?.nome ?? 'sistema'}` }],
        }
      : o,
  )
  gravar('ocorrencias', lista)
}

// Importa o arquivo gerado pelo robô RPA (06-rpa/saida/ordens_servico.json).
// Ignora IDs já existentes (idempotência) e devolve um resumo da importação.
export function importarDeteccoes(itens) {
  if (!Array.isArray(itens)) throw new Error('O arquivo deve conter uma lista JSON de ocorrências.')
  const atual = listarOcorrencias()
  const ids = new Set(atual.map((o) => o.id))
  const novas = []
  const erros = []
  itens.forEach((item, i) => {
    if (item.id && ids.has(item.id)) return
    if (Number.isNaN(Number(item.lat)) || Number.isNaN(Number(item.lng ?? item.lon))) {
      erros.push(`Item ${i + 1}: coordenadas inválidas`)
      return
    }
    novas.push(montar({ ...item, lng: item.lng ?? item.lon, fonte: item.fonte ?? 'robô RPA' }))
  })
  gravar('ocorrencias', [...novas, ...atual])
  return { importadas: novas.length, ignoradas: itens.length - novas.length - erros.length, erros }
}

export function restaurarExemplo() {
  gravar('ocorrencias', OCORRENCIAS_INICIAIS.map((o) => montar(o)))
}
