// Camada fina sobre o localStorage. Todo acesso passa por try/catch porque o
// navegador pode bloquear o armazenamento (aba anônima, cota cheia etc.).

const PREFIXO = 'cidade-em-ordem:'

export function ler(chave, padrao) {
  try {
    const bruto = localStorage.getItem(PREFIXO + chave)
    return bruto ? JSON.parse(bruto) : padrao
  } catch {
    return padrao
  }
}

export function gravar(chave, valor) {
  try {
    localStorage.setItem(PREFIXO + chave, JSON.stringify(valor))
    return true
  } catch {
    return false
  }
}

export function remover(chave) {
  try {
    localStorage.removeItem(PREFIXO + chave)
  } catch {
    /* ignora */
  }
}

// Hash SHA-256 da senha: a senha em texto puro nunca é salva no navegador.
export async function hashSenha(senha, sal) {
  const dados = new TextEncoder().encode(`${sal}:${senha}`)
  const digest = await crypto.subtle.digest('SHA-256', dados)
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
}

export function novoId(prefixo = 'id') {
  return `${prefixo}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`
}
