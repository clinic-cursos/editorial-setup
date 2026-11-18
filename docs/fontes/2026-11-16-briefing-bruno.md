# BRIEFING EXECUTIVO — AGENTE EDITOR-CHEFE DA CLINIC EDITORA
**Destinatário:** Alify  
**Data:** 16/11/2026  
**Objetivo:** Desenvolvimento do cérebro central da Clinic Editora

## 1. O QUE QUEREMOS CONSTRUIR

Queremos criar um **Editor-Chefe sênior de uma editora científica**, responsável exclusivamente pela Clinic Editora.

Não queremos um chatbot que apenas responde perguntas ou escreve textos. Queremos um agente com capacidade de gestão, planejamento, delegação, supervisão e controle de qualidade.

Ele deve pensar como o responsável por uma editora profissional: conhecer os livros, entender o processo editorial, coordenar especialistas, identificar problemas, solicitar correções e acompanhar cada obra até sua aprovação para impressão.

O agente será o cérebro central de uma operação multiagente, com memória institucional e processos padronizados.

**Princípio central:** o Editor-Chefe gerencia a produção dos livros, enquanto o Board Científico mantém a autoridade sobre o conteúdo técnico.

## 2. COMO FUNCIONA A CLINIC EDITORA HOJE

A Clinic possui um Board Científico composto por:

- **Paula Caroline Garcia:** CEO técnica, coordenação, padrões editoriais e aprovação final.
- **Julie Heejoo Bae:** professora, participa da criação dos conteúdos e utiliza um Design System para melhorar os slides.
- **João Matheus Sobral Pena:** professor, participa do Board e realiza a revisão técnica dos manuscritos ampliados.

O processo atual é:

1. O Board produz os slides, a apostila, os conteúdos das aulas e imagens com IA.
2. Julie utiliza seu Design System para aprimorar as apresentações.
3. Paula envia os materiais ao ChatGPT, com as diretrizes do manual técnico da Clinic Editora.
4. A IA desenvolve conteúdo complementar para transformar a apostila em um livro mais extenso, geralmente com meta inicial próxima de 80 páginas.
5. A IA pesquisa literatura científica, desenvolve textos e adiciona referências.
6. João analisa tecnicamente o manuscrito.
7. O material revisado volta ao ChatGPT para diagramação.
8. Paula revisa o resultado editorial e visual.
9. Paula providencia o ISBN e encaminha à gráfica.
10. A gráfica produz uma prova física; Paula avalia e autoriza a produção geral.

**Principal problema:** Paula e João executam ou coordenam muitas atividades operacionais que deveriam ser antecipadas, organizadas e filtradas por agentes especializados.

## 3. MISSÃO DO EDITOR-CHEFE

O Editor-Chefe deverá assumir a coordenação operacional desse processo.

Suas responsabilidades principais:

- Receber os materiais produzidos pelo Board.
- Criar e organizar projetos editoriais.
- Ler e aplicar o manual técnico da Clinic Editora.
- Identificar lacunas no conteúdo original.
- Planejar a ampliação científica e pedagógica.
- Acionar pesquisadores, escritores e revisores especializados.
- Verificar a qualidade dos entregáveis.
- Controlar referências e versões.
- Preservar a fidelidade entre curso, slides e livro.
- Coordenar a diagramação.
- Acionar o agente externo de Arte e Vídeo.
- Preparar as revisões humanas de João e Paula.
- Organizar pendências.
- Preparar os documentos necessários à publicação.
- Controlar o histórico de cada livro.

O Editor-Chefe deverá atuar de forma proativa, propondo correções e próximos passos, sem depender de instruções humanas para cada pequena tarefa.

## 4. REGRA MAIS IMPORTANTE: O LIVRO É A EXTENSÃO DO CURSO

Os livros da Clinic são entregues aos participantes dos próprios cursos.

Portanto, **aquilo que é apresentado nos slides e ensinado durante a aula deve estar refletido no livro**.

O livro deve ser mais completo do que a apostila, mas não pode descaracterizar ou eliminar o conteúdo original do Board.

O sistema deverá distinguir três fontes:

**A. Conteúdo original:** slides, apostila, imagens e protocolos do Board.

**B. Conteúdo efetivamente ministrado:** explicações orais, notas, roteiros e transcrições, quando fornecidos.

**C. Complementação editorial:** fundamentação científica, aprofundamentos, estudos, explicações, referências e recursos didáticos produzidos pela IA.

Quando houver conflito entre o material original e a literatura científica, o agente deverá sinalizar a divergência para avaliação humana, e não alterar silenciosamente a informação.

## 5. SINCRONIZAÇÃO ENTRE SLIDES E LIVROS

Criar um módulo chamado **Sincronizador Curso–Livro**.

O Editor-Chefe deverá saber quais slides correspondem a cada capítulo ou seção do livro.

Esse módulo deverá:

- Relacionar slides com trechos do livro.
- Preservar imagens importantes.
- Comparar versões de apresentações.
- Identificar alterações textuais e visuais.
- Apontar conteúdos ausentes no livro.
- Identificar quais capítulos precisam ser atualizados.
- Encaminhar modificações científicas para revisão.
- Manter histórico de versões.

O Design System utilizado pela Julie deverá ser integrado quando sua tecnologia e interfaces forem identificadas.

Não presumir que já existe uma API disponível.

## 6. SUBAGENTES COORDENADOS PELO EDITOR-CHEFE

A arquitetura deverá prever os seguintes especialistas:

| Agente | Função |
|---|---|
| Editor de Projetos | Receber, classificar e organizar materiais |
| Editor de Desenvolvimento | Planejar a ampliação do conteúdo |
| Pesquisador Científico | Buscar e organizar literatura confiável |
| Escritor Técnico-Didático | Desenvolver os conteúdos complementares |
| Auditor Científico | Verificar afirmações, fontes e divergências |
| Revisor de Originais | Revisão linguística e padronização |
| Diagramador | Criar e ajustar o miolo |
| Diretor de Arte Editorial | Coordenar as necessidades visuais |
| Produção Gráfica | Preparar metadados e arquivos de impressão |
| Marketing Editorial | Produzir sinopses e materiais comerciais |

Não é necessário desenvolver todos imediatamente.

A primeira versão deverá priorizar os agentes que permitem transformar materiais do Board em um manuscrito ampliado e cientificamente auditado.

## 7. INTEGRAÇÃO COM O AGENTE DE ARTE E VÍDEO

Estamos desenvolvendo outro agente, paralelamente, especializado em produção visual e audiovisual.

O Editor-Chefe deverá poder acioná-lo como serviço especializado.

Exemplos de solicitações:

- Criar uma ilustração anatômica.
- Melhorar uma imagem didática.
- Desenvolver um infográfico.
- Criar uma representação de mecanismo fisiológico.
- Adaptar uma imagem dos slides para o livro.
- Preparar ilustrações de capítulos.
- Produzir vídeos ou animações educacionais.

A comunicação deverá funcionar por tarefas estruturadas.

**Entrada:** projeto, capítulo, objetivo pedagógico, briefing científico, referências visuais, restrições e formato.

**Saída:** imagem ou vídeo, descrição, metadados, versão, identificação de uso de IA, limitações e status de validação.

O agente visual não poderá aprovar sua própria representação científica.

A integração deve ser modular e não depender de ambos os agentes estarem na mesma conversa do ChatGPT.

## 8. PADRÕES EDITORIAIS DA CLINIC

O sistema deverá possuir memória institucional contendo os padrões aprovados da Clinic Editora.

Referências iniciais:

- Livros didáticos de saúde e estética.
- Formato A4.
- Identidade bordô, branco e cinza.
- Estética científica e profissional.
- Estrutura de Estudo e Prática.
- Leitura e Aprofundamento.
- Aplicação Clínica.
- Ponto-chave.
- Atenção.
- Evidência.
- Perguntas frequentes.
- Referências bibliográficas.
- Legendas e notas editoriais padronizadas.
- Preservação das imagens originais e dos direitos autorais.

O manual anexado de padrões visuais e o livro de Toxina Botulínica são referências iniciais.

O sistema precisa permitir atualizar esses padrões após aprovação de Paula, preservando as versões anteriores.

## 9. QUALIDADE CIENTÍFICA

Todo conteúdo complementar deverá possuir rastreabilidade.

Sempre que aplicável, registrar:

- Afirmação científica.
- Fonte que a sustenta.
- DOI ou PMID.
- Tipo de estudo.
- Data de consulta.
- Limitações.
- Trecho do livro em que foi utilizada.
- Status de revisão.

Integrar, conforme viabilidade, fontes como PubMed, Crossref, OpenAlex e bases oficiais.

**Proibições:** referências inventadas, afirmações clínicas sem sustentação apresentadas como fatos, alterações não autorizadas de protocolos e recomendações regulatórias desatualizadas tratadas como vigentes.

João permanece como responsável pela revisão técnica humana.

## 10. QUALIDADE DA DIAGRAMAÇÃO

O sistema deverá produzir arquivos editoriais utilizáveis e executar verificações automáticas antes de enviar o livro para Paula.

É obrigatório detectar:

- Sobreposição de textos.
- Duplicação de parágrafos.
- Cortes de conteúdo.
- Problemas de margens.
- Imagens distorcidas.
- Imagens com resolução insuficiente.
- Sumário inconsistente.
- Falhas de paginação.
- Legendas ausentes.
- Problemas de hierarquia visual.

Isso é especialmente importante porque o PDF de referência de Toxina Botulínica apresenta erros de repetição e sobreposição em diversas páginas.

**Exportar um PDF não significa que a diagramação esteja aprovada.**

O sistema deverá renderizar, inspecionar, corrigir e validar antes da revisão humana.

## 11. GOVERNANÇA E APROVAÇÕES

O Editor-Chefe pode decidir, delegar e supervisionar tarefas operacionais.

Entretanto:

- João aprova o conteúdo técnico.
- Paula aprova a versão editorial final.
- Paula mantém a responsabilidade pelo ISBN.
- Paula aprova a prova física antes da impressão geral.

Essas são etapas obrigatórias de aprovação.

O agente deverá registrar quem aprovou, qual versão foi aprovada e quando ocorreu a decisão.

Alterações posteriores deverão gerar uma nova versão.

## 12. MEMÓRIA INSTITUCIONAL

A memória deverá existir fora das conversas e permanecer disponível entre projetos.

Armazenar:

- Manual editorial.
- Templates.
- Decisões.
- Livros anteriores.
- Arquivos originais.
- Manuscritos.
- Referências.
- Imagens.
- Revisões.
- Aprovações.
- ISBN.
- Arquivos finais.

Cada livro deverá possuir um dossiê completo e versionado.

O Editor-Chefe deverá conseguir responder perguntas como:

"Qual foi a última versão aprovada?"

"O que João solicitou corrigir?"

"Quais imagens ainda dependem de validação?"

"Quais livros estão aguardando Paula?"

"Quais capítulos foram afetados pela atualização dos slides?"

## 13. INTERFACE DO EDITOR-CHEFE

Precisamos de uma interface web que permita:

- Conversar com o Editor-Chefe.
- Criar projetos.
- Enviar arquivos.
- Visualizar o andamento dos livros.
- Ver tarefas dos subagentes.
- Consultar pendências.
- Revisar manuscritos.
- Aprovar ou rejeitar entregas.
- Comparar versões.
- Visualizar arquivos e PDFs.
- Acompanhar custos e execução.

O Editor-Chefe deverá executar ações concretas, não apenas responder com orientações textuais.

## 14. TECNOLOGIA

Avaliar principalmente:

- **LangGraph:** orquestração de agentes e fluxos.
- **Paperclip:** possível gestão organizacional dos agentes.
- **CrewAI:** alternativa de colaboração multiagente.
- **PostgreSQL:** dados estruturados e histórico.
- **Armazenamento documental:** arquivos e versões.
- **Busca vetorial:** recuperação de conhecimento quando necessária.
- **APIs:** comunicação com sistemas externos.

Essas ferramentas são candidatas, não decisões técnicas fechadas.

Alify deverá examinar licenças, manutenção, segurança, complexidade e adequação real antes de escolher.

Evitar instalar vários frameworks com funções sobrepostas sem justificativa.

## 15. PRIMEIRO MVP

O primeiro produto funcional deverá conseguir:

1. Receber slides e apostila de um curso.
2. Criar o projeto editorial.
3. Aplicar os padrões da Clinic.
4. Analisar o material original.
5. Identificar lacunas.
6. Elaborar um plano de ampliação.
7. Pesquisar fontes científicas.
8. Desenvolver conteúdo complementar.
9. Auditar o texto produzido.
10. Gerar manuscrito para revisão de João.
11. Registrar decisões e versões.
12. Permitir retomar o trabalho sem perder contexto.

A diagramação automatizada, a sincronização avançada dos slides e a integração visual deverão ser adicionadas progressivamente.

## 16. TESTE COM MATERIAL REAL

Usar o livro de **Toxina Botulínica — Fundamentos, técnicas e aplicações clínicas** como referência para desenvolvimento e testes.

O objetivo não é reescrever automaticamente o livro aprovado.

É verificar se o sistema consegue reproduzir o processo editorial, preservar os materiais originais, identificar problemas e melhorar a qualidade das entregas.

Utilizar cópias e manter os arquivos originais intactos.

## 17. O QUE ALIFY DEVE ENTREGAR

Solicitamos inicialmente:

**1. Arquitetura técnica do Editor-Chefe.** Como ele funcionará, quais tecnologias utilizará e como coordenará os especialistas.

**2. Definição da memória institucional.** Onde serão armazenadas informações, decisões e arquivos.

**3. Modelo de comunicação entre agentes.** Como delegar tarefas, receber resultados e verificar conclusões.

**4. Modelo de governança.** Como funcionam aprovações, permissões e bloqueios.

**5. Backlog priorizado.** O que precisa ser construído primeiro, dependências e critérios de aceite.

**6. MVP funcional.** Um Editor-Chefe capaz de abrir e conduzir um projeto real de transformação de apostila em manuscrito científico.

---

# DIRETRIZ FINAL

A Clinic Editora não precisa de muitos agentes que conversem entre si sem controle.

Precisa de um **Editor-Chefe inteligente, confiável, com autonomia operacional, memória institucional, especialistas acionáveis e processos auditáveis**.

Ele deve reduzir o trabalho de Paula e João, preservar a autoridade do Board Científico e entregar livros com qualidade científica e editorial profissional.

**O sucesso do projeto será medido pela capacidade de transformar o material original de um curso em um livro completo, fiel às aulas, cientificamente fundamentado e pronto para validação humana, com menos retrabalho, menor custo e maior padronização.**
