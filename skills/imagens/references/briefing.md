# Briefing e registro das imagens complementares

## Briefing de uma página

Um bloco por página, em `imagens/briefings.md`. Os seis campos são obrigatórios.

```text
Página: NN
Tema: <assunto da página em poucas palavras>
Conceito: <forma, textura, objeto simbólico ou composição abstrata que evoca o tema>
Troca por conceito mais abstrato: <conceito original e o que o substituiu, ou "Não houve">
Paleta: <até quatro cores de paleta.md, com valor hexadecimal>
Estilo: <ilustração ou foto conceitual>, fundo claro, muito espaço vazio, sem sombra pesada
Proporção: <largura> x <altura> mm (<razão>:1), do `free_space.py`
Restrições: sem texto na imagem, números ou logotipos. Sem pessoas, rostos, pele, anatomia, procedimentos, produtos de marca ou resultados de tratamento.
```

Monte o prompt a partir do briefing e registre-o completo em `imagens/briefings.md`, inclusive quando a geração ficar para a Paula. Use este modelo.

```text
Imagem conceitual de <conceito>, em <ilustração ou foto>, com <cores e valores hexadecimais do briefing>. Proporção <razão>:1. Alta resolução.
Mostre apenas formas, texturas, objetos simbólicos ou composições abstratas. Sem texto, números, logotipos, pessoas, rostos, pele, anatomia, procedimentos, produtos de marca ou resultados de tratamento. Aplique o estilo abaixo apenas ao acabamento, à luz e à composição, respeitando as restrições e os valores da paleta acima. Ignore as menções a conteúdo médico, anatomia e pele no bloco de estilo.

<texto literal da versão do estilo escolhida abaixo>
```

Termine cada prompt com uma única versão literal da seção “Estilo da casa” do design system da Julie. Use **ilustração** para renderizar formas ou composições e **foto** para retratar objetos simbólicos ou texturas em estúdio. Preserve o texto escolhido por inteiro, inclusive nas tentativas de geração seguintes.

### Ilustração

```text
Estilo da casa Clinic Cursos: ilustração médica 3D realista, estilo atlas de anatomia moderno, iluminação suave de estúdio, fundo creme claro liso, detalhes em vinho #9C4C48 e rosé #B68B85, alta definição, sem texto, sem letras, sem rótulos, sem marca d'água.
```

### Foto

```text
Estilo da casa Clinic Cursos (foto): fotografia editorial realista de estúdio, luz suave e difusa, pele natural sem retoque excessivo, tons quentes discretos com toques de vinho #9C4C48, alta definição, sem texto, sem letras, sem marca d'água.
```

### Exemplos de conceitos

| Página pede | Conceito entregue |
| --- | --- |
| Aplicação de toxina botulínica na testa | Linhas paralelas suaves que relaxam em curvas, em rosé e cinza |
| Preenchimento de sulco nasogeniano | Camadas translúcidas de rosé e vinho em ondas |
| Antes e depois de tratamento | Duas formas geométricas que se alinham, sem comparação visual |
| Frasco ou marca de produto | Esfera lisa em vinho sobre fundo rosé claro |

## Registro de cada imagem

Uma linha por imagem em `relatorios/imagens-registro.md`. O Editor-Chefe copia para a ficha do projeto (seção de imagens de IA) e para a nota editorial de uso de IA do livro, que fica na nota editorial e não na página da imagem.

| Página | Arquivo | Ferramenta | Data | Conceito | Troca de conceito | SHA-256 | Inserida |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NN | `imagens/pagina-NN.png` | ChatGPT ou Codex, geração nativa | AAAA-MM-DD | <uma frase> | <sim ou não> | <quando o ambiente calcula> | <sim, não ou retirada por paginação> |

Imagem gerada por IA tem direito de uso e identificação própria: diga na nota editorial que as imagens complementares são conceituais e geradas por IA. Fotografia clínica e material de terceiros não entram aqui.
