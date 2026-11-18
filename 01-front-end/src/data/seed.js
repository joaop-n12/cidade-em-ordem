// Ocorrências sintéticas (nenhum dado pessoal real) para a primeira execução.
// Simulam detecções feitas pelo caminhão de coleta na região do Tatuapé (SP).

export const OCORRENCIAS_INICIAIS = [
  {
    tipo: 'buraco', fonte: 'camera+sensor', lat: -23.5402, lng: -46.5763,
    endereco: 'R. Tuiuti, 1200 - Tatuapé', via: 'coletora',
    confianca: 0.91, impactoG: 3.2, profundidadeCm: 12, reincidencias: 3,
    descricao: 'Buraco grande perto de escola, motos desviando.', status: 'Em execução', diasAtras: 2,
  },
  {
    tipo: 'buraco', fonte: 'camera', lat: -23.5431, lng: -46.5712,
    endereco: 'Av. Celso Garcia, 4100 - Tatuapé', via: 'arterial',
    confianca: 0.78, impactoG: null, profundidadeCm: null, reincidencias: 1,
    descricao: '', status: 'Aberta', diasAtras: 1,
  },
  {
    tipo: 'lixo', fonte: 'camera', lat: -23.5378, lng: -46.5801,
    endereco: 'R. Itapura, 300 - Tatuapé', via: 'local',
    confianca: 0.86, impactoG: null, profundidadeCm: null, reincidencias: 2,
    descricao: 'Entulho e sofá ao lado do bueiro.', status: 'Aberta', diasAtras: 3,
  },
  {
    tipo: 'buraco', fonte: 'sensor', lat: -23.5455, lng: -46.5788,
    endereco: 'R. Serra de Bragança, 800 - Vila Gomes Cardim', via: 'local',
    confianca: null, impactoG: 2.4, profundidadeCm: 6, reincidencias: 0,
    descricao: '', status: 'Em vistoria', diasAtras: 1,
  },
  {
    tipo: 'calcada', fonte: 'cidadao', lat: -23.5419, lng: -46.5741,
    endereco: 'R. Apucarana, 150 - Tatuapé', via: 'local',
    confianca: null, impactoG: null, profundidadeCm: null, reincidencias: 0,
    descricao: 'Calçada quebrada, cadeirante não consegue passar.', status: 'Concluída', diasAtras: 9,
  },
  {
    tipo: 'buraco', fonte: 'camera', lat: -23.5389, lng: -46.5729,
    endereco: 'R. Emília Marengo, 500 - Tatuapé', via: 'local',
    confianca: 0.42, impactoG: null, profundidadeCm: null, reincidencias: 0,
    descricao: '', status: 'Em vistoria', diasAtras: 0,
  },
]
