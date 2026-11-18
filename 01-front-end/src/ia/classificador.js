// Módulo de "processamento inteligente" da ocorrência.
// Combina três fontes de evidência (câmera/visão computacional, sensor IoT
// e texto livre) em um escore de gravidade explicável. Cada fator que soma
// pontos é devolvido na lista `fatores`, para que o gestor entenda a decisão
// (a IA apoia a triagem, não substitui a vistoria presencial).

export const TIPOS = {
  buraco: { rotulo: 'Buraco na via', secretaria: 'Subprefeitura - Manutenção Viária', pesoBase: 35 },
  lixo: { rotulo: 'Descarte irregular de lixo/entulho', secretaria: 'Limpeza Urbana', pesoBase: 25 },
  calcada: { rotulo: 'Calçada danificada / obstruída', secretaria: 'Subprefeitura - Fiscalização de Calçadas', pesoBase: 25 },
  sinalizacao: { rotulo: 'Placa de trânsito danificada', secretaria: 'Engenharia de Tráfego - Sinalização', pesoBase: 30 },
  iluminacao: { rotulo: 'Iluminação pública apagada', secretaria: 'Departamento de Iluminação Pública', pesoBase: 20 },
}

// Palavras-chave usadas para inferir o tipo quando só existe descrição em texto.
const PALAVRAS_TIPO = {
  buraco: ['buraco', 'cratera', 'asfalto', 'pavimento', 'afundamento', 'erosão', 'erosao'],
  lixo: ['lixo', 'entulho', 'descarte', 'sacos', 'sofá', 'sofa', 'resíduo', 'residuo', 'caçamba'],
  calcada: ['calçada', 'calcada', 'rampa', 'passeio', 'pedestre', 'cadeirante'],
  sinalizacao: ['placa', 'sinalização', 'sinalizacao', 'semáforo', 'semaforo', 'pare'],
  iluminacao: ['poste', 'lâmpada', 'lampada', 'escuro', 'iluminação', 'iluminacao'],
}

const PALAVRAS_RISCO = [
  { termos: ['acidente', 'caiu', 'queda', 'ferido', 'machucou'], pontos: 20, motivo: 'Relato de acidente ou queda' },
  { termos: ['moto', 'bicicleta', 'ciclista', 'motociclista'], pontos: 10, motivo: 'Risco para motos e bicicletas' },
  { termos: ['escola', 'creche', 'hospital', 'ubs', 'posto de saúde'], pontos: 10, motivo: 'Próximo a escola/hospital' },
  { termos: ['idoso', 'cadeirante', 'deficiente', 'criança', 'crianca'], pontos: 10, motivo: 'Afeta pessoas vulneráveis' },
  { termos: ['rato', 'mosquito', 'dengue', 'cheiro', 'bueiro'], pontos: 10, motivo: 'Risco sanitário / entupimento de bueiro' },
  { termos: ['grande', 'enorme', 'profundo', 'cratera'], pontos: 8, motivo: 'Descrito como grande/profundo' },
]

function normalizar(texto = '') {
  return texto.toLowerCase()
}

export function inferirTipo(descricao) {
  const t = normalizar(descricao)
  let melhor = null
  let melhorQtd = 0
  for (const [tipo, termos] of Object.entries(PALAVRAS_TIPO)) {
    const qtd = termos.filter((p) => t.includes(p)).length
    if (qtd > melhorQtd) {
      melhor = tipo
      melhorQtd = qtd
    }
  }
  return melhor
}

/**
 * Classifica uma ocorrência.
 * @param {object} o - { tipo, descricao, confianca (0-1), impactoG, profundidadeCm, via, chovendo, reincidencias }
 */
export function classificarOcorrencia(o) {
  const fatores = []
  const tipo = o.tipo || inferirTipo(o.descricao) || 'buraco'
  const info = TIPOS[tipo] ?? TIPOS.buraco
  let escore = info.pesoBase
  fatores.push({ motivo: `Tipo: ${info.rotulo}`, pontos: info.pesoBase })

  // Evidência da visão computacional
  const conf = Number(o.confianca)
  if (!Number.isNaN(conf) && conf > 0) {
    const pts = Math.round(conf * 15)
    escore += pts
    fatores.push({ motivo: `Câmera detectou com ${(conf * 100).toFixed(0)}% de confiança`, pontos: pts })
  }

  // Evidência do sensor IoT (acelerômetro do caminhão)
  const g = Number(o.impactoG)
  if (!Number.isNaN(g) && g >= 1.5) {
    const pts = g >= 3 ? 20 : g >= 2.2 ? 12 : 6
    escore += pts
    fatores.push({ motivo: `Impacto de ${g.toFixed(1)} g medido pelo sensor do veículo`, pontos: pts })
  }

  const prof = Number(o.profundidadeCm)
  if (!Number.isNaN(prof) && prof > 0) {
    const pts = prof >= 10 ? 15 : prof >= 5 ? 8 : 3
    escore += pts
    fatores.push({ motivo: `Profundidade estimada de ${prof} cm`, pontos: pts })
  }

  // Contexto da via
  if (o.via === 'arterial') {
    escore += 10
    fatores.push({ motivo: 'Via arterial (alto fluxo)', pontos: 10 })
  } else if (o.via === 'coletora') {
    escore += 5
    fatores.push({ motivo: 'Via coletora (fluxo médio)', pontos: 5 })
  }

  if (o.chovendo) {
    escore += 8
    fatores.push({ motivo: 'Chuva prevista: buraco fica escondido pela água / lixo entope bueiro', pontos: 8 })
  }

  const reinc = Number(o.reincidencias) || 0
  if (reinc > 0) {
    const pts = Math.min(reinc * 4, 16)
    escore += pts
    fatores.push({ motivo: `${reinc} detecção(ões) anteriores no mesmo ponto`, pontos: pts })
  }

  // Análise do texto livre
  const t = normalizar(o.descricao)
  for (const regra of PALAVRAS_RISCO) {
    if (regra.termos.some((p) => t.includes(p))) {
      escore += regra.pontos
      fatores.push({ motivo: regra.motivo, pontos: regra.pontos })
    }
  }

  escore = Math.max(0, Math.min(100, escore))

  let prioridade, prazo
  if (escore >= 80) [prioridade, prazo] = ['Crítica', '24 horas']
  else if (escore >= 60) [prioridade, prazo] = ['Alta', '72 horas']
  else if (escore >= 40) [prioridade, prazo] = ['Média', '7 dias']
  else [prioridade, prazo] = ['Baixa', '15 dias']

  // Quando a evidência é fraca, o sistema pede vistoria humana em vez de decidir sozinho.
  const temCamera = !Number.isNaN(conf) && conf > 0
  const precisaRevisao = (temCamera && conf < 0.5) || (!temCamera && !(g >= 1.5) && !o.descricao)

  const acao = precisaRevisao
    ? `Encaminhar para vistoria de um fiscal antes de abrir ordem de serviço (evidência insuficiente).`
    : `Abrir ordem de serviço para ${info.secretaria} com prazo de ${prazo}.`

  return {
    tipo,
    tipoRotulo: info.rotulo,
    secretaria: info.secretaria,
    escore,
    prioridade,
    prazo,
    acao,
    precisaRevisao,
    fatores,
  }
}
