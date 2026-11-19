# Ficha do projeto

Use um arquivo `ficha.md` na pasta de cada projeto. Copie o modelo abaixo e preencha todos os campos. Campo sem dado recebe `Nenhum` ou `Não informado`, nunca é apagado. Versão aprovada não muda: mudança gera versão nova.

Onde fica: nos arquivos do Projeto (ChatGPT e claude.ai; a Paula substitui o arquivo pela versão nova entregue no fim de cada fase) ou em `<pasta de trabalho>/projetos/<projeto>/ficha.md` (Claude Code e Codex), com `originais/`, `versoes/` e `relatorios/`.

```markdown
# Ficha: <projeto>

## Identificação
- Título:
- Curso:
- Autores:
- Data de abertura:
- Fase atual: <0 a 6> e estado (em andamento, aguardando João, aguardando Paula, voltando a <papel>)

## Materiais recebidos
| Material | Versão | Data | Origem (Board, aula, outro) |
| --- | --- | --- | --- |

## Fases
| Fase | Estado | Quem fez | Volta | Nota | Quem deu a nota | Pendências |
| --- | --- | --- | --- | --- | --- | --- |
Nota da fase 3 com o manual ausente: "NN, provisória: manual ausente".

## Aprovações humanas
| Quem | O que aprovou | Versão (arquivo) | SHA-256 | Data e hora |
| --- | --- | --- | --- | --- |
aprovado: <caminho do arquivo da versão aprovada>   (uma linha por versão aprovada)

## Decisões e divergências levadas ao Board
| Data | Localização | Trecho original | Evidência | Decisão | Quem decidiu |
| --- | --- | --- | --- | --- | --- |

## Imagens geradas por IA
| Página | Briefing | Modelo (quando disponível) | Estado de validação |
| --- | --- | --- | --- |
Alimenta a nota editorial de uso de IA do livro.

## Custos (quando o ambiente mostra)
| Fase | Imagens geradas | Tokens ou mensagens | Tempo |
| --- | --- | --- | --- |

## Histórico
- <AAAA-MM-DD HH:MM> | <papel ou pessoa> | <evento em uma linha>
```

## Regras
- A linha `aprovado:` é lida pela trava do plugin do Claude Code, que nega escrita nesse arquivo. Escreva o caminho exato.
- Registre uma linha de histórico por evento, sempre com data e hora no formato `AAAA-MM-DD HH:MM`. Registre pedidos enviados, retornos recebidos, notas de cada volta, pacotes entregues, aprovações e divergências.
- Custos: preencha só o que o ambiente mostra; nunca estime.
