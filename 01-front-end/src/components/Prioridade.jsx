export const CORES_PRIORIDADE = {
  Crítica: '#b42318',
  Alta: '#c4320a',
  Média: '#a15c07',
  Baixa: '#027a48',
}

export default function Prioridade({ valor }) {
  return (
    <span className="selo" style={{ borderColor: CORES_PRIORIDADE[valor], color: CORES_PRIORIDADE[valor] }}>
      Prioridade {valor}
    </span>
  )
}
