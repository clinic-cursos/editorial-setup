INSTRUÇÃO OFICIAL PARA ALIFY — CLINIC EDITORA

Atualização da arquitetura, responsabilidades e prioridades de implementação

Alify, definimos a arquitetura e a ordem de desenvolvimento do sistema de agentes da Clinic Editora. Quero que você utilize as instruções abaixo para atualizar o setup que estamos construindo no Claude Code.

1. Arquitetura oficial

A Clinic Editora terá um Agente Mestre Orquestrador, quatro subagentes internos e uma integração com nosso agente externo de Arte e Vídeo.

Agente Mestre — Editor-Chefe Orquestrador

É o cérebro central da Clinic Editora e o responsável por coordenar toda a operação.

Suas responsabilidades são:

* Receber demandas e arquivos do Board Científico.
* Criar, planejar e administrar projetos editoriais.
* Delegar tarefas aos subagentes.
* Supervisionar a execução e verificar entregáveis.
* Gerenciar dependências e prioridades.
* Controlar arquivos, memória, versões, custos e histórico.
* Identificar erros e determinar as correções necessárias.
* Coordenar a integração com o agente externo de Arte e Vídeo.
* Garantir a correspondência entre slides, apostilas e livros.
* Controlar aprovações humanas.
* Acompanhar cada livro até a produção gráfica.

O Agente Mestre deve ser um orquestrador efetivo, e não apenas um assistente que responde perguntas.

Todos os subagentes deverão reportar suas entregas e pendências ao Agente Mestre.

A autoridade científica continuará com o Board Científico. João realizará a revisão técnica humana e Paula manterá a aprovação editorial e a liberação para impressão.

2. Os quatro subagentes internos

Subagente 1 — Diagramador

Responsável pela produção editorial e visual dos livros.

Deve:

* Receber manuscritos aprovados.
* Aplicar a identidade visual da Clinic Editora.
* Utilizar templates editoriais padronizados.
* Diagramar livros em formato A4.
* Organizar títulos, subtítulos, capítulos, tabelas e imagens.
* Inserir legendas, referências, QR codes e elementos editoriais.
* Gerar sumário e paginação.
* Produzir PDF para revisão e arquivo-fonte editável.
* Preparar exportações conforme as especificações da gráfica.
* Executar verificações técnicas iniciais de layout.

Não deve alterar conteúdo científico aprovado sem autorização.

Não é responsável por criar ilustrações anatômicas ou imagens com IA.

Subagente 2 — Editor Científico-Didático

Unifica as funções anteriormente previstas para Pesquisador Científico, Escritor Técnico-Didático e Preparador de Originais.

Deve:

* Analisar os slides e apostilas produzidos pelo Board.
* Identificar conteúdos que precisam de aprofundamento.
* Preservar a sequência didática e o conteúdo original.
* Pesquisar literatura científica confiável.
* Verificar a existência e os metadados das referências.
* Desenvolver capítulos, explicações e aprofundamentos.
* Produzir linguagem técnica, clara e adequada ao ensino.
* Padronizar terminologia, gramática e organização textual.
* Preservar a correspondência entre slides e livro.
* Entregar manuscrito estruturado, com referências rastreáveis.

Não pode inventar referências nem modificar silenciosamente decisões clínicas do Board.

Subagente 3 — Auditor Científico

Responsável pela revisão independente do trabalho do Editor Científico-Didático.

Deve:

* Verificar afirmações científicas.
* Conferir DOI, PMID e dados bibliográficos.
* Avaliar se as fontes realmente sustentam as afirmações.
* Identificar divergências científicas.
* Identificar possíveis erros e extrapolações.
* Conferir a coerência com os materiais originais do Board.
* Identificar informações clínicas ou regulatórias que exijam atualização.
* Produzir relatórios objetivos de não conformidades.

Não deve reescrever integralmente o manuscrito.

Deve encaminhar ao Agente Mestre os problemas encontrados, com localização, evidências e recomendações.

A aprovação científica humana continuará sendo responsabilidade de João.

Subagente 4 — Auditor Gráfico

Responsável pela auditoria independente do material diagramado.

Deve:

* Inspecionar PDFs renderizados.
* Identificar sobreposição e duplicação de textos.
* Detectar elementos cortados.
* Conferir margens e paginação.
* Verificar a legibilidade das páginas.
* Detectar imagens distorcidas ou em resolução inadequada.
* Conferir posicionamento de legendas.
* Avaliar consistência visual.
* Verificar problemas em tabelas, gráficos e QR codes.
* Produzir relatório de erros e pendências.

O Auditor Gráfico não gera nem edita imagens.

Quando encontrar problemas, deverá comunicar ao Agente Mestre.

O Agente Mestre decidirá se a correção deve ser encaminhada ao Diagramador ou ao agente externo de Arte e Vídeo.

A validação científica de imagens anatômicas ficará sob responsabilidade do processo de auditoria científica e das autoridades humanas competentes.

3. Agente externo de Arte e Vídeo

Estamos desenvolvendo paralelamente um agente especializado em produção visual e audiovisual.

Esse agente deverá utilizar os recursos nativos de geração de imagens do ChatGPT, priorizando os modelos mais recentes efetivamente disponíveis e compatíveis com o ambiente.

Não fixar permanentemente o projeto em uma versão específica do modelo de geração de imagens.

A arquitetura deverá prever atualização de modelos e identificação da versão efetivamente utilizada, quando essa informação estiver disponível.

O agente externo será responsável por:

* Gerar ilustrações anatômicas.
* Produzir imagens didáticas.
* Criar infográficos.
* Desenvolver imagens conceituais.
* Adaptar e editar recursos visuais.
* Produzir materiais audiovisuais conforme suas capacidades.
* Corrigir imagens mediante solicitações.

O Agente Mestre será responsável por coordenar as solicitações visuais, coletar os resultados e encaminhar as validações necessárias.

Importante: antes de implementar chamadas automáticas, verificar se existe um mecanismo autorizado e funcional para o sistema desenvolvido no Claude Code acionar a geração nativa do ChatGPT.

Não presumir que o acesso às imagens na interface do ChatGPT equivale à disponibilidade de uma API com os mesmos recursos.

4. Nova ordem obrigatória de desenvolvimento

A implementação deve seguir nossas maiores dores operacionais.

FASE 1 — AGENTE MESTRE

Prioridade máxima.

Desenvolver primeiro o núcleo de orquestração.

Entregáveis:

* Agente Mestre funcional.
* Estrutura de delegação.
* Cadastro de projetos.
* Gestão de tarefas.
* Memória institucional persistente.
* Controle de arquivos e versões.
* Histórico de execução.
* Controle de aprovações.
* Capacidade de registrar e monitorar subagentes.
* Estrutura de integração com serviços externos.

Critério de aceite: o Agente Mestre consegue criar um projeto, delegar uma tarefa a um executor de teste, receber um resultado e registrar o histórico completo.

FASE 2 — DIAGRAMADOR

Primeiro subagente a ser desenvolvido.

Nossa maior dor operacional imediata é produzir livros bem diagramados, com consistência visual e sem erros de layout.

Entregáveis:

* Templates da Clinic Editora.
* Motor de diagramação.
* Organização de capítulos.
* Inserção de imagens.
* Geração de DOCX ou outro formato editável definido tecnicamente.
* Exportação de PDF.
* Verificações automáticas de layout.
* Controle das versões diagramadas.

Utilizar o livro de Toxina Botulínica como referência e caso inicial de teste, preservando os originais.

Não aguardar o desenvolvimento do Editor Científico-Didático para testar o Diagramador.

Os manuscritos já revisados poderão ser utilizados como entrada.

Mesmo antes do Auditor Gráfico estar concluído, o Diagramador deverá executar verificações técnicas básicas de sobreposição, corte, fontes, paginação e resolução de imagens.

FASE 3 — EDITOR CIENTÍFICO-DIDÁTICO

Desenvolver o subagente responsável pela transformação de apostilas e slides em livros científicos ampliados.

Entregáveis:

* Análise dos materiais originais.
* Plano de ampliação.
* Pesquisa bibliográfica.
* Redação técnico-didática.
* Padronização textual.
* Manuscrito estruturado.
* Referências rastreáveis.
* Correspondência entre slides e capítulos.

FASE 4 — AUDITOR CIENTÍFICO

Desenvolver o subagente independente responsável pela verificação do manuscrito.

Entregáveis:

* Verificação das referências.
* Auditoria das afirmações científicas.
* Identificação de divergências.
* Relatório de pendências.
* Encaminhamento para correções.
* Preparação para revisão humana de João.

Evitar que o auditor simplesmente confirme as conclusões do agente que escreveu o texto.

FASE 5 — AUDITOR GRÁFICO

A arquitetura e os testes essenciais deverão ser previstos desde a implementação do Diagramador.

Entretanto, a configuração completa do Auditor Gráfico será finalizada quando o agente externo de Arte e Vídeo estiver pronto para integração.

Entregáveis:

* Inspeção independente de páginas.
* Relatórios automatizados de não conformidades.
* Validação de imagens e elementos gráficos.
* Integração com o fluxo de solicitação de correções.
* Reinspeção após ajustes.
* Relatório final para revisão editorial de Paula.

Essa dependência não deverá impedir que o Diagramador execute verificações técnicas básicas desde a Fase 2.

5. Fluxo de produção visual

Quando uma imagem for necessária:

1. O Editor Científico-Didático ou Diagramador identifica a necessidade.
2. Encaminha uma solicitação ao Agente Mestre.
3. O Agente Mestre prepara ou consolida o briefing.
4. O agente externo de Arte e Vídeo produz o recurso.
5. O conteúdo técnico da imagem é encaminhado para validação científica, quando aplicável.
6. O Diagramador insere a imagem aprovada no livro.
7. O Auditor Gráfico verifica a qualidade visual e a integração da imagem à página.
8. O Agente Mestre coordena eventuais correções.

O agente de Arte e Vídeo não poderá aprovar sozinho a correção científica de ilustrações anatômicas.

6. Regras para o Claude Code

Não reconstruir o projeto do zero.

Antes de modificar o setup existente:

1. Inspecionar os arquivos e configurações atuais.
2. Identificar agentes já criados.
3. Comparar a estrutura existente com esta especificação.
4. Identificar redundâncias e configurações obsoletas.
5. Preservar componentes funcionais.
6. Atualizar os prompts e as responsabilidades.
7. Ajustar a estrutura de orquestração.
8. Criar testes de funcionamento.
9. Implementar as alterações por fases.
10. Documentar o que foi modificado.

Não criar agentes adicionais sem justificativa técnica e aprovação.

Não manter subagentes executando permanentemente quando não houver tarefas.

Priorizar o uso eficiente de contexto, modelos e tokens, sem comprometer a qualidade das entregas.

7. Governança inegociável

O Board Científico é a origem intelectual dos livros.

O conteúdo dos slides deve estar representado no material didático final.

João realiza a revisão técnica humana.

Paula realiza a aprovação editorial e gráfica final.

Versões aprovadas não podem ser alteradas silenciosamente.

O sistema deve preservar referências, decisões, arquivos e históricos.

Nenhum agente poderá liberar impressão sem a aprovação humana necessária.

8. Primeira entrega solicitada

Alify, antes de iniciar novas implementações extensas, quero que você apresente:

1. Diagnóstico do setup atual.
2. Estrutura definitiva do Agente Mestre e dos quatro subagentes.
3. O que já está implementado.
4. O que precisa ser modificado.
5. Quais redundâncias serão eliminadas.
6. Como será feita a comunicação e a delegação entre agentes.
7. Como será implementada a memória persistente.
8. Plano de execução priorizando Agente Mestre e Diagramador.
9. Critérios de teste e aceite para essas duas primeiras fases.
10. Dependências e limitações da futura integração com o ChatGPT para geração nativa de imagens.

Objetivo final: desenvolver uma operação editorial coordenada por um único Agente Mestre, com quatro subagentes especializados, integração externa de Arte e Vídeo, qualidade científica, diagramação profissional e o menor retrabalho operacional possível.

Ordem oficial: Agente Mestre → Diagramador → Editor Científico-Didático → Auditor Científico → Auditor Gráfico.
