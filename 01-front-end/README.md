# Cidade em Ordem: Front End (React + Vite)

Disciplina: **Front End & Mobile Development** · Global Solution 2026.2 · CitizenTech

## Integrantes
| Nome | RM |
|---|---|
| João Pedro de Souza Nunes | RM567318 |
| Guilherme Nakamura | RM567460 |

## Problema escolhido
Buracos, calçadas quebradas e lixo acumulado só são consertados depois que alguém reclama na prefeitura.
Muitos problemas ficam meses sem registro e causam acidentes com motos e bicicletas, danos a veículos e
dificuldades para pedestres, idosos e pessoas com deficiência. Bairros onde as pessoas reclamam menos
acabam esquecidos.

## Público afetado
- **Cidadãos** que circulam pelas ruas: motoristas, motociclistas, ciclistas, pedestres, pessoas com deficiência.
- **Gestores da prefeitura/subprefeitura**, que precisam decidir o que consertar primeiro com equipes limitadas.

## Solução
Os caminhões de coleta de lixo, que já passam por todas as ruas, levam câmera e sensor. As detecções chegam
automaticamente, a IA calcula a prioridade e o sistema gera a ação (ordem de serviço ou vistoria). Este
front-end é a interface de todo o projeto: painel com mapa, cadastro e consulta de ocorrências, triagem
com IA e assistente do cidadão.

## Funcionalidades exigidas
| Requisito | Onde está |
|---|---|
| Componentes, props e estado | `src/components/*` (`Prioridade`, `MapaOcorrencias`, `Layout`), estado com `useState`/`useMemo` em todas as páginas |
| Rotas de navegação | `src/App.jsx` com `react-router-dom` (rotas públicas, protegidas e restritas ao perfil gestor) |
| Login local | `src/context/AuthContext.jsx`: cadastro e login no navegador, senha em hash SHA-256 com sal |
| Cadastro e consulta com dados persistidos | `NovaOcorrencia.jsx` e `Ocorrencias.jsx` (filtros), salvos no `localStorage` (`src/services/storage.js`) |
| Processamento inteligente e resposta/ação | `src/ia/classificador.js`: escore de gravidade explicável, prioridade, prazo, secretaria e ação gerada. `src/ia/assistente.js`: assistente que responde com base em leis e cartilhas, com integração opcional ao RAG |

## Acessibilidade
- HTML semântico (`header`, `nav`, `main`, `table` com `caption` e `scope`), idioma `pt-BR`.
- Link "Pular para o conteúdo", foco visível em todos os elementos, navegação por teclado.
- Todos os campos com `label`; mensagens de erro com `role="alert"`; resultados com `aria-live`.
- Botão **A+** para aumentar a fonte; cores com contraste adequado; o mapa tem a mesma informação em lista.

## Proteção de dados (LGPD)
- Minimização: só nome e e-mail. Sem CPF, telefone ou endereço do cidadão.
- Consentimento explícito no cadastro.
- Senha nunca é salva em texto puro (hash SHA-256 + sal).
- Dados ficam apenas no navegador. Botão "Apagar minha conta" (direito de eliminação, art. 18).
- Aviso para não incluir nomes, telefones ou placas na descrição.

## ODS
- **ODS 11** (meta 11.2): vias e calçadas seguras e acessíveis.
- **ODS 9** (meta 9.1): infraestrutura de qualidade mantida com apoio de tecnologia.
- **ODS 10**: a detecção é igual em todas as ruas, sem depender de quem reclama mais.

## Como executar
```bash
cd 01-front-end
npm install
npm run dev
```
Abra o endereço mostrado (normalmente http://localhost:5173), crie uma conta (perfil **Gestor** para ver
todas as telas) e explore. O app já começa com ocorrências de exemplo (dados sintéticos).

Opcional: para o assistente usar o RAG da pasta `05-generative-ai`, crie um arquivo `.env` com
`VITE_RAG_URL=http://localhost:8000/perguntar`. Se o RAG estiver fora do ar, o assistente usa a base local.

## Integração com as outras disciplinas
- **Visão Computacional e IoT**: as detecções da câmera e do sensor chegam pela tela **Importar detecções**
  (arquivo gerado pelo robô RPA) e aparecem no mapa.
- **RPA**: gera o `ordens_servico.json` que é importado aqui.
- **Generative AI / NLP**: o assistente usa os mesmos documentos do corpus e do RAG.
