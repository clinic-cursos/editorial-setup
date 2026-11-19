# Diagnóstico: `extract_pdf.py` não termina no livro de Toxina

## Relato
- Onde: `skills/diagramador/scripts/extract_pdf.py`, chamado pelo `scripts/run_sample.py` no ensaio 3.8 (`docs/medicoes/2026-11-ensaio-toxina-diagramacao.md`).
- O que aconteceu: no Toxina (80 páginas, 36 MB) a extração passou de 30 min de CPU sem terminar; o traceback do faulthandler parava no `Jpeg2KImagePlugin` do Pillow.
- Esperado: terminar na ordem do Preenchedores (117 páginas, 4,8 MB, 5 s).
- Hipótese do ensaio: o pypdf recodifica imagens JPEG 2000 grandes. **Não confirmada**: o Toxina não tem nenhuma imagem JPX (inventário abaixo). O JPEG 2000 é o formato de saída que o pypdf escolhe para JPEG com máscara suave (`/SMask`); cada recodificação custa de 0,01 a 0,3 s. O tempo vem do número de recodificações.

## Reprodução
Ambiente: worktree do ensaio 3.8, pypdf 7.1.1, pdfplumber 0.11.10, Pillow 13.0.0 (OpenJPEG 2.5.4), Python 3.12.

Inventário do Toxina sem decodificar nada: 71 imagens (45 DCT, 22 Flate, 4 ASCII85+Flate), nenhuma JPX. O pdfplumber vê 188 imagens desenhadas no livro todo; o `page.images` do pypdf lista 21.820 entradas.

| Página | Entradas no `page.images` do pypdf | Imagens distintas | Desenhadas (pdfplumber) | `list(page.images)` medido |
|---|---|---|---|---|
| 10 | 1 | 1 | 1 | 0,4 s |
| 11 | 4 | 2 | 4 | 1,4 s |
| 47 | 1.144 | 44 | 1 | 55,4 s |
| 21 | 2.288 | 44 | 2 | 123,3 s |

Páginas com 2.288 entradas: 21, 22, 37, 38, 44, 49, 68, 69. Com 1.144: 47, 52, 56. O resto tem de 1 a 8.

Execução completa do script original (timeout 3600 s): ver «Medição completa» no fim.

## Causa raiz
`skills/diagramador/scripts/extract_pdf.py:107`:

```python
reader_images = list(figures["reader"].pages[number - 1].images)
```

1. As páginas do Toxina desenham Forms `/fzFrm*` (gerados pelo MuPDF) aninhados até 30 níveis, e 52 Forms da página partilham o mesmo dicionário `/XObject` com 44 imagens. O `PageObject._get_ids_image` do pypdf visita cada Form uma vez e devolve as 44 imagens de cada um, sem tirar repetidas: 52 x 44 = 2.288 caminhos na página 21, onde só 2 imagens estão desenhadas.
2. `list(...)` itera o `VirtualListImages`, e cada item chama `_xobj_to_image`, que decodifica a imagem e a recodifica com `Image.save` (JPEG com `/SMask` vira JPEG 2000 sem perdas, daí o `Jpeg2KImagePlugin` no traceback). Não há cache: a mesma imagem é convertida uma vez por caminho.
3. No livro: 21.820 conversões para 188 imagens desenhadas (63 distintas). O dedupe por `idnum` em `figures["saved"]` (linha 118) só evita gravar de novo, depois de tudo convertido.

Defeito irmão, no mesmo trecho (`extract_pdf.py:108` e `:111`): `named` casa a imagem desenhada com a do pypdf pelo nome do XObject, mas o nome só é único dentro de um dicionário de recursos. Forms com recursos próprios repetem `/Im1` e `/fzImg0` para imagens diferentes. No Toxina, 10 páginas têm esse conflito (11, 14, 20, 25, 26, 30, 43, 48, 50, 54); na 25 a foto 1122x1402 e o ícone 94x94 se chamam `/Im1`, e o dicionário fica com o último. Resultado: figura errada no manuscrito e `origem.json` com pixels que não são os do arquivo gravado (o `check_images` procura a origem pelos pixels e erra a severidade).

## Chamadores
Comandos: `git grep -n "page_items\|render(" -- '*.py'`, `git grep -n "extract_pdf"`, `git grep -n "from pypdf\|import pypdf\|\.images\b" -- '*.py'`, `git grep -n "origem.json\|--inherited\|origins"`.

| Chamador | Sofre do defeito? |
|---|---|
| `extract_pdf.py:142` `render()` chama `page_items` por página | Sim, é o caminho do bug. |
| `extract_pdf.py:242` `main()` chama `render` | Sim, via `render`. |
| `scripts/run_sample.py:132` roda o script no ensaio | Sim: travou o ensaio do Toxina. |
| `skills/diagramador/SKILL.md:22` manda a Paula rodar o script | Sim, mesmo caminho. |
| `tests/test_extract_pdf.py` (17 testes) | Não exercitam Form XObject; passam antes e depois da correção. |
| `check_layout.py:23-36` lê `origem.json` (pixels e ppi) e `lib/pdfcheck/checks.py:158-180` (`check_images`, cópias em `skills/*/scripts/pdfcheck/`) | Consumidores. Recebem pixels errados no conflito de nome; a correção os deixa certos. Pixels e ppi continuam vindo do pdfplumber (`srcsize` e caixa da imagem desenhada), sem mudança. |
| `build_book.py:56-61` embute o arquivo da figura | Consumidor. Formatos de saída inalterados (`.jpg`, `.png`, `.jp2`); o protótipo compôs o Toxina (297 páginas) com os `.jp2`. |
| `insert_images.py` | Não usa o que o `extract_pdf.py` grava (lê `pagina-NN.png` do papel imagens). |
| Outro uso do `page.images` do pypdf | Nenhum: só `extract_pdf.py:107`. |

## Correção sugerida
No `page_items`, onde todos os chamadores passam: listar só os caminhos (`images.keys()`, sem converter), achar o número do objeto de cada caminho descendo pelos `/Resources` (barato) e converter só a imagem desenhada, achada pelo `objid` que o pdfplumber dá em `placed["stream"]`. Converter só quando a chave ainda não está em `figures["saved"]`. Inline, ou imagem direta sem número, continua casando na ordem da página.

```diff
-    # pypdf nomeia a imagem como o XObject mais a extensão; o nome é a identidade do recurso.
-    # Imagem inline não tem XObject nem referência indireta: casa com as inline do pypdf, na ordem da página.
-    reader_images = list(figures["reader"].pages[number - 1].images)
-    named = {Path(i.name).with_suffix("").name: i for i in reader_images if i.indirect_reference}
-    inline = iter([i for i in reader_images if not i.indirect_reference])
+    # O pypdf converte (decodifica e recodifica) cada imagem pedida e lista a mesma imagem uma vez por Form que
+    # a alcança: só se pede a desenhada, achada pelo número do objeto, porque o nome se repete entre Forms.
+    # Imagem inline (ou direta) não tem número: casa com as inline do pypdf, na ordem da página.
+    source = figures["reader"].pages[number - 1]
+    by_object, inline = {}, []
+    for path in source.images.keys():
+        xobject = None
+        if path[0] != "~":
+            xobject = source
+            for name in [path] if isinstance(path, str) else path:
+                xobject = xobject["/Resources"]["/XObject"][name]
+        if xobject is None or xobject.indirect_reference is None:
+            inline.append(path)
+        else:
+            by_object.setdefault(xobject.indirect_reference.idnum, path)
+    inline = iter(inline)
     for placed in page.images:
-        image = named.get(placed["name"]) or next(inline, None)
-        if image is None:
+        objid = placed["stream"].objid
+        path = by_object.get(objid) if objid is not None else next(inline, None)
+        if path is None:
             warnings.append(f"página {number}: imagem sem dados extraíveis ignorada")
             continue
         figures["count"] += 1
         fig_id = f"fig-{figures['count']}"
-        key = image.indirect_reference.idnum if image.indirect_reference else (number, placed["name"])
-        if key not in figures["saved"]:  # imagem reutilizada é gravada uma vez só
+        key = objid if objid is not None else (number, placed["name"])
+        if key not in figures["saved"]:  # imagem reutilizada é convertida e gravada uma vez só
+            image = source.images[path]
             filename = images_dir / f"{fig_id}{Path(image.name).suffix or '.png'}"
```

Protótipo fora do git (cópia do script em `/var/tmp`), com estes números:
- Toxina: 29,6 s de parede (28,3 s de CPU de usuário), 63 imagens gravadas (23 `.jp2`, 15 `.jpg`, 25 `.png`, 27 MB), `origem.json` com 63 entradas e 0 divergências entre os pixels declarados e os do arquivo. Perfil: a maior parte do tempo restante é o pdfplumber (`body_size` lê o layout de todas as páginas); as 63 conversões somam cerca de um terço.
- Preenchedores: 5,3 s (original 6,0 s), saída byte a byte idêntica à do original (`diff -r` vazio).
- `tests/test_extract_pdf.py` e o teste novo: 19 passam com o protótipo aplicado.
- `build_book.py` compôs o manuscrito do protótipo (297 páginas, 19,5 s).

Não sugerido: gravar o fluxo JPX original ou reduzir ao tamanho exibido. Não há JPX no livro, e reduzir mudaria os pixels que o `origem.json` e o `check_images` usam.

## Critério de aceite do cartão
- `uv run --locked pytest tests/test_extract_pdf_forms.py tests/test_extract_pdf.py -q`: tudo passa (hoje os 2 testes novos falham, com 110 conversões para 1 imagem desenhada e com `fig-2.png` ausente do `origem.json`).
- Toxina pelo `run_sample.py`: `extract_pdf.py` termina em menos de 60 s nesta máquina.

## Medição completa
- Script original no Toxina, rodando sozinho: 10 min 08 s de CPU sem terminar (RSS de 1,6 GB). Foi interrompido pelo PID ao fim do limite de turnos do diagnóstico. Estimativa pelas páginas medidas: 8 x 123 s + 3 x 55 s, cerca de 19 min só nas conversões do pypdf.
- Protótipo: 29,6 s.
- Sem conferir: o `check_layout.py` sobre o livro composto pelo protótipo (passou de 3 min e foi interrompido pelo PID; essa lentidão é outro caminho, não entrou neste diagnóstico) e a saída completa do original, para comparar figura a figura nas 10 páginas com conflito de nome.
