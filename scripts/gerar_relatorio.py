"""
Gerador automatizado do Relatorio de Aula Pratica (LOJABD / MySQL 5.6 / SQL Fiddle)
a partir do modelo institucional DOCX (`Modelo de Atividade Textual (1).docx`) e normas ABNT.

Uso:
    python scripts/gerar_relatorio.py --atualizar-word
    python scripts/gerar_relatorio.py --modo-teste --atualizar-word --saida-dir <DIR_SCRATCH>
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


RAIZ = Path(__file__).resolve().parent.parent
ARQ_MODELO = RAIZ / "Modelo de Atividade Textual (1).docx"
ARQ_DADOS = RAIZ / "dados_relatorio.json"
DIR_SQL = RAIZ / "sql"
DIR_EVIDENCIAS = RAIZ / "evidencias"

IMAGENS_ESPERADAS = {
    "fig1": ("01_ddl_dml_schema.png", "Execução dos scripts DDL e DML no SQL Fiddle (MySQL 5.6) em tela inteira"),
    "fig2": ("02_consulta1_join_vendas.png", "Execução da Consulta 1 (INNER JOIN de vendas, clientes e produtos) no SQL Fiddle em tela inteira"),
    "fig3": ("03_consulta2_left_join_clientes.png", "Execução da Consulta 2 (LEFT JOIN exibindo código NULL para cliente sem compra) no SQL Fiddle em tela inteira"),
    "fig4": ("04_consulta3_join_antes_data_atual.png", "Execução da Consulta 3 (INNER JOIN com DISTINCT antes da data atual) no SQL Fiddle em tela inteira"),
}

EXTENSOES_IMAGEM = (".png", ".jpg", ".jpeg", ".bmp", ".webp")


def carregar_dados(modo_teste: bool) -> dict[str, str]:
    """Carrega os metadados de `dados_relatorio.json` e valida campos pendentes."""
    if not ARQ_DADOS.exists():
        raise FileNotFoundError(f"Arquivo de dados nao encontrado: {ARQ_DADOS}")

    dados = json.loads(ARQ_DADOS.read_text(encoding="utf-8"))
    if modo_teste:
        substitutos = {
            "instituicao": "UNIVERSIDADE PITÁGORAS UNOPAR ANHANGUERA (EXEMPLO DE TESTE)",
            "curso": "ANÁLISE E DESENVOLVIMENTO DE SISTEMAS",
            "orientador": "Orientadora: Profª [Nome da Orientadora — Teste]",
            "cidade": "São Paulo - SP",
        }
        for k, v in substitutos.items():
            if "[INFORMAR" in dados.get(k, ""):
                dados[k] = v
        return dados

    pendentes = [k for k, v in dados.items() if isinstance(v, str) and "[INFORMAR" in v]
    if pendentes:
        raise ValueError(
            "Preencha os campos pendentes em dados_relatorio.json antes de gerar o relatorio final: "
            + ", ".join(pendentes)
        )
    return dados


def localizar_evidencias(modo_teste: bool, dir_teste: Path | None) -> dict[str, Path]:
    """Localiza as 4 capturas reais em `evidencias/` ou cria placeholders em `--modo-teste`."""
    if modo_teste:
        if dir_teste is None:
            raise ValueError("dir_teste obrigatorio no modo de teste.")
        from PIL import Image, ImageDraw

        pasta_img = dir_teste / "_evidencias_teste"
        pasta_img.mkdir(parents=True, exist_ok=True)
        mapa: dict[str, Path] = {}
        cores = {
            "fig1": ("SQL Fiddle | MySQL 5.6 | Schema DDL + DML (Build Schema OK)", "#1E3A5F"),
            "fig2": ("SQL Fiddle | MySQL 5.6 | Consulta 1: INNER JOIN (10 vendas)", "#1F4E3D"),
            "fig3": ("SQL Fiddle | MySQL 5.6 | Consulta 2: LEFT JOIN (Rian -> NULL)", "#4A2C5A"),
            "fig4": ("SQL Fiddle | MySQL 5.6 | Consulta 3: DISTINCT antes da data atual", "#5C3A1E"),
        }
        for chave, (nome_padrao, _) in IMAGENS_ESPERADAS.items():
            destino = pasta_img / nome_padrao
            img = Image.new("RGB", (1366, 768), color="#F4F6F9")
            draw = ImageDraw.Draw(img)
            titulo, cor = cores[chave]
            draw.rectangle([0, 0, 1366, 52], fill="#2B2D42")
            draw.text((20, 18), "http://sqlfiddle.com/   [MySQL 5.6]", fill="#FFFFFF")
            draw.rectangle([20, 72, 1346, 132], fill=cor)
            draw.text((36, 94), f"[IMAGEM DE TESTE PARA VALIDACAO TECNICA] {titulo}", fill="#FFFFFF")
            draw.rectangle([20, 150, 670, 680], outline="#B0BEC5", width=2, fill="#FFFFFF")
            draw.text((40, 170), "Painel Esquerdo: Schema DDL / DML (LOJABD)", fill="#263238")
            draw.rectangle([690, 150, 1346, 680], outline="#B0BEC5", width=2, fill="#FFFFFF")
            draw.text((710, 170), "Painel Direito: Run SQL / Results Grid", fill="#263238")
            draw.rectangle([0, 720, 1366, 768], fill="#1C1E26")
            draw.text((20, 738), "Windows Taskbar | 22/11/2026 22:00", fill="#E0E0E0")
            img.save(destino, format="PNG")
            mapa[chave] = destino
        return mapa

    mapa_real: dict[str, Path] = {}
    faltando: list[str] = []
    for chave, (nome_padrao, _) in IMAGENS_ESPERADAS.items():
        stem = Path(nome_padrao).stem
        encontrado = None
        for ext in EXTENSOES_IMAGEM:
            candidato = DIR_EVIDENCIAS / f"{stem}{ext}"
            if candidato.exists():
                encontrado = candidato
                break
        if encontrado is None:
            faltando.append(nome_padrao)
        else:
            mapa_real[chave] = encontrado

    if faltando:
        raise FileNotFoundError(
            "Capturas obrigatorias ausentes em evidencias/: " + ", ".join(faltando)
        )
    return mapa_real


def _texto_txbx(txbx_el) -> str:
    return "".join(t.text or "" for t in txbx_el.findall(f".//{qn('w:t')}"))


def _preencher_txbx_content(txbx_el, linhas: list[tuple[str, str]]) -> None:
    """Substitui os paragrafos de um `<w:txbxContent>` preservando os estilos."""
    for child in list(txbx_el):
        txbx_el.remove(child)

    for estilo, texto in linhas:
        p = OxmlElement("w:p")
        if estilo:
            pPr = OxmlElement("w:pPr")
            pStyle = OxmlElement("w:pStyle")
            pStyle.set(qn("w:val"), estilo)
            pPr.append(pStyle)
            p.append(pPr)
        if texto:
            r = OxmlElement("w:r")
            t = OxmlElement("w:t")
            t.set(qn("xml:space"), "preserve")
            t.text = texto
            r.append(t)
            p.append(r)
        txbx_el.append(p)


def _ajustar_caixa_topo_capa(p_el) -> None:
    """Ajusta posicao vertical e altura da caixa do topo da capa para Instituicao + Curso."""
    # Choice (DrawingML)
    for anchor in p_el.findall(f".//{qn('wp:anchor')}"):
        posV = anchor.find(qn("wp:positionV"))
        if posV is not None:
            off = posV.find(qn("wp:posOffset"))
            if off is not None:
                off.text = "1260000"  # ~3.5 cm (acima do campo Autor em 2784475)
        ext = anchor.find(qn("wp:extent"))
        if ext is not None:
            ext.set("cy", "1250000")
        for a_ext in anchor.findall(f".//{qn('a:xfrm')}/{qn('a:ext')}"):
            a_ext.set("cy", "1250000")

    # Fallback (VML)
    for shape in p_el.findall(".//{urn:schemas-microsoft-com:vml}shape"):
        style = shape.get("style", "")
        style = re.sub(r"margin-top:[^;]+", "margin-top:99.2pt", style)
        style = re.sub(r"height:[^;]+", "height:98.45pt", style)
        shape.set("style", style)


def atualizar_capa_e_folha_rosto(doc: Document, dados: dict[str, str]) -> None:
    """Preenche todas as caixas de texto da Capa e da Folha de Rosto do modelo."""
    ocorrencias = {"autor": 0, "titulo": 0, "cidade": 0}
    preenchidas = set()

    for p in doc._body._body.findall(qn("w:p")):
        txbxs = p.findall(f".//{qn('w:txbxContent')}")
        if not txbxs:
            continue
        conteudo = _texto_txbx(txbxs[0]).lower()

        if "nome do curso" in conteudo:
            linhas = [
                ("NomedoAutoreCurso", dados["instituicao"].upper()),
                ("NomedoAutoreCurso", dados["curso"].upper()),
            ]
            _ajustar_caixa_topo_capa(p)
            for tb in txbxs:
                _preencher_txbx_content(tb, linhas)
            preenchidas.add("curso")

        elif "nome do(s) autor(es)" in conteudo:
            ocorrencias["autor"] += 1
            linhas = [("NomedoAutoreCurso", dados["autor"].upper())]
            for tb in txbxs:
                _preencher_txbx_content(tb, linhas)
            preenchidas.add(f"autor_{ocorrencias['autor']}")

        elif "título do trabalho" in conteudo:
            ocorrencias["titulo"] += 1
            linhas = [
                ("TtulodoTrabalho", dados["titulo"]),
                ("SubttulodoTrabalho", dados["subtitulo"]),
            ]
            for tb in txbxs:
                _preencher_txbx_content(tb, linhas)
            preenchidas.add(f"titulo_{ocorrencias['titulo']}")

        elif "cidade" in conteudo and "ano" in conteudo:
            ocorrencias["cidade"] += 1
            linhas = [
                ("LocaleAnodeEntrega", dados["cidade"]),
                ("LocaleAnodeEntrega", dados["ano"]),
            ]
            for tb in txbxs:
                _preencher_txbx_content(tb, linhas)
            preenchidas.add(f"cidade_{ocorrencias['cidade']}")

        elif "trabalho textual apresentado" in conteudo:
            linhas = [
                ("NaturezadoTrabalho", dados["natureza_trabalho"]),
                ("NaturezadoTrabalho", ""),
                ("NaturezadoTrabalho", dados["orientador"]),
            ]
            for tb in txbxs:
                _preencher_txbx_content(tb, linhas)
            preenchidas.add("natureza")

    esperadas = {
        "curso",
        "autor_1",
        "autor_2",
        "titulo_1",
        "titulo_2",
        "cidade_1",
        "cidade_2",
        "natureza",
    }
    if preenchidas != esperadas:
        raise RuntimeError(
            f"Caixas de texto da Capa/Folha de Rosto divergentes. "
            f"Esperadas={esperadas}, Preenchidas={preenchidas}"
        )


def limpar_corpo_exemplo_preservando_sumario(doc: Document) -> None:
    """
    Preserva Capa, Folha de Rosto, Sumario automatico (ate o paragrafo que contem
    o `<w:sectPr>` de transicao pre-textual) e remove apenas os paragrafos de
    instrucoes/exemplos do modelo antes do `<w:sectPr>` final.
    """
    body = doc._body._body
    filhos = list(body)
    idx_transicao = None
    for idx, el in enumerate(filhos):
        if el.tag == qn("w:p") and el.find(f".//{qn('w:sectPr')}") is not None:
            idx_transicao = idx
            break

    if idx_transicao is None:
        raise RuntimeError("Paragrafo de quebra de secao apos o Sumario nao encontrado.")

    for el in filhos[idx_transicao + 1 :]:
        if el.tag != qn("w:sectPr"):
            body.remove(el)


def _set_cell_shading(cell, hex_color: str) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def _set_cell_margins(cell, top=80, bottom=80, left=120, right=120) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for lado, val in (("top", top), ("bottom", bottom), ("left", left), ("right", right)):
        node = OxmlElement(f"w:{lado}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def _set_table_borders(table, border_style: str = "abnt_tabela", color: str = "444444") -> None:
    """
    Aplica bordas conforme ABNT:
      - `abnt_tabela`: apenas linhas horizontais superior/inferior externas e
        linha horizontal sob o cabecalho (sem bordas verticais externas/internas);
      - `abnt_quadro`: grade completa (todas as bordas externas e internas);
      - `codigo`: caixa discreta fechada.
    """
    tblPr = table._tbl.tblPr
    for old in tblPr.findall(qn("w:tblBorders")):
        tblPr.remove(old)
    borders = OxmlElement("w:tblBorders")

    if border_style == "abnt_tabela":
        specs = {
            "top": ("single", "10", color),
            "bottom": ("single", "10", color),
            "left": ("none", "0", "auto"),
            "right": ("none", "0", "auto"),
            "insideH": ("single", "4", "CCCCCC"),
            "insideV": ("none", "0", "auto"),
        }
    elif border_style == "codigo":
        specs = {
            "top": ("single", "6", "B0BEC5"),
            "bottom": ("single", "6", "B0BEC5"),
            "left": ("single", "12", "37474F"),
            "right": ("single", "6", "B0BEC5"),
            "insideH": ("none", "0", "auto"),
            "insideV": ("none", "0", "auto"),
        }
    else:  # abnt_quadro
        specs = {
            "top": ("single", "8", color),
            "bottom": ("single", "8", color),
            "left": ("single", "8", color),
            "right": ("single", "8", color),
            "insideH": ("single", "4", "888888"),
            "insideV": ("single", "4", "888888"),
        }

    for nome, (val, sz, cor) in specs.items():
        b = OxmlElement(f"w:{nome}")
        b.set(qn("w:val"), val)
        if val != "none":
            b.set(qn("w:sz"), sz)
            b.set(qn("w:space"), "0")
            b.set(qn("w:color"), cor)
        borders.append(b)
    tblPr.append(borders)


def _set_row_bottom_border(row, sz: str = "8", color: str = "444444") -> None:
    for cell in row.cells:
        tcPr = cell._tc.get_or_add_tcPr()
        tcBorders = OxmlElement("w:tcBorders")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), sz)
        bottom.set(qn("w:space"), "0")
        bottom.set(qn("w:color"), color)
        tcBorders.append(bottom)
        tcPr.append(tcBorders)


def adicionar_titulo_nivel1(doc: Document, texto: str) -> None:
    doc.add_paragraph(texto, style="heading 1")


def adicionar_titulo_nivel2(doc: Document, texto: str) -> None:
    doc.add_paragraph(texto, style="heading 2")


def adicionar_paragrafo(doc: Document, texto: str) -> None:
    p = doc.add_paragraph(texto, style="Parágrafo")
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def adicionar_bloco_sql(doc: Document, titulo_bloco: str, codigo_sql: str) -> None:
    """Insere bloco de codigo SQL formatado em caixa monoespacada legivel."""
    p_rotulo = doc.add_paragraph(style="Normal")
    p_rotulo.paragraph_format.space_before = Pt(8)
    p_rotulo.paragraph_format.space_after = Pt(2)
    p_rotulo.paragraph_format.keep_with_next = True
    r = p_rotulo.add_run(titulo_bloco)
    r.bold = True
    r.font.size = Pt(10)

    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    if len(codigo_sql.splitlines()) <= 15:
        tbl.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
    cell = tbl.cell(0, 0)
    cell.width = Cm(16.0)
    _set_cell_shading(cell, "F5F7FA")
    _set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
    _set_table_borders(tbl, border_style="codigo")

    p = cell.paragraphs[0]
    p.style = doc.styles["Normal"]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.15
    run = p.add_run(codigo_sql.strip())
    run.font.name = "Consolas"
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)

    p_esp = doc.add_paragraph(style="Normal")
    p_esp.paragraph_format.space_before = Pt(0)
    p_esp.paragraph_format.space_after = Pt(6)


def adicionar_tabela_abnt(
    doc: Document,
    rotulo: str,
    titulo: str,
    colunas: list[str],
    linhas: list[list[str]],
    fonte: str,
    larguras_cm: list[float],
    eh_quadro: bool = False,
) -> None:
    """Adiciona Tabela ou Quadro conforme ABNT: titulo acima e fonte abaixo."""
    estilo_titulo = "Titulo de Quadro" if eh_quadro else "Titulo de Tabela"
    p_tit = doc.add_paragraph(style=estilo_titulo)
    p_tit.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_tit.paragraph_format.keep_together = True
    p_tit.paragraph_format.keep_with_next = True
    r_rot = p_tit.add_run(f"{rotulo} – ")
    r_rot.bold = True
    r_rot.font.size = Pt(10)
    r_tit = p_tit.add_run(titulo)
    r_tit.font.size = Pt(10)

    tbl = doc.add_table(rows=len(linhas) + 1, cols=len(colunas))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    _set_table_borders(tbl, border_style="abnt_quadro" if eh_quadro else "abnt_tabela")

    manter_tabela_junta = len(linhas) <= 12

    # Cabecalho
    hdr_cells = tbl.rows[0].cells
    trPr = tbl.rows[0]._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:tblHeader"))
    trPr.append(OxmlElement("w:cantSplit"))
    for i, col in enumerate(colunas):
        cell = hdr_cells[i]
        cell.width = Cm(larguras_cm[i])
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        _set_cell_shading(cell, "EAECEF")
        _set_cell_margins(cell, top=65, bottom=65, left=90, right=90)
        p = cell.paragraphs[0]
        p.style = doc.styles["Texto - Tabela e Quadro"]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.15
        if manter_tabela_junta:
            p.paragraph_format.keep_with_next = True
        run = p.add_run(col)
        run.bold = True
        run.font.size = Pt(10)
    if not eh_quadro:
        _set_row_bottom_border(tbl.rows[0], sz="8", color="444444")

    # Linhas de dados
    for r_idx, linha in enumerate(linhas, start=1):
        row = tbl.rows[r_idx]
        tr_pr = row._tr.get_or_add_trPr()
        tr_pr.append(OxmlElement("w:cantSplit"))
        eh_ultima = r_idx == len(linhas)
        for c_idx, val in enumerate(linha):
            cell = row.cells[c_idx]
            cell.width = Cm(larguras_cm[c_idx])
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            _set_cell_margins(cell, top=55, bottom=55, left=90, right=90)
            p = cell.paragraphs[0]
            p.style = doc.styles["Texto - Tabela e Quadro"]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.15
            if manter_tabela_junta or eh_ultima:
                p.paragraph_format.keep_with_next = True
            run = p.add_run(val)
            run.font.size = Pt(10)

    p_fnt = doc.add_paragraph(style="Fonte")
    p_fnt.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_fnt.paragraph_format.space_before = Pt(4)
    r_fnt = p_fnt.add_run(f"Fonte: {fonte}")
    r_fnt.font.size = Pt(10)


def adicionar_figura_abnt(
    doc: Document,
    rotulo: str,
    titulo: str,
    caminho_img: Path,
    fonte: str,
    largura_cm: float = 15.8,
) -> None:
    """Adiciona Figura ABNT com titulo acima, imagem centralizada e fonte abaixo."""
    p_tit = doc.add_paragraph(style="Título de Figura")
    p_tit.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tit.paragraph_format.keep_together = True
    p_tit.paragraph_format.keep_with_next = True
    r_rot = p_tit.add_run(f"{rotulo} – ")
    r_rot.bold = True
    r_rot.font.size = Pt(10)
    r_tit = p_tit.add_run(titulo)
    r_tit.font.size = Pt(10)

    p_img = doc.add_paragraph(style="Figura ou Gráfico")
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.keep_with_next = True
    p_img.paragraph_format.space_before = Pt(4)
    p_img.paragraph_format.space_after = Pt(4)
    run_img = p_img.add_run()
    run_img.add_picture(str(caminho_img), width=Cm(largura_cm))

    p_fnt = doc.add_paragraph(style="Fonte")
    p_fnt.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_fnt = p_fnt.add_run(f"Fonte: {fonte}")
    r_fnt.font.size = Pt(10)


def adicionar_referencias_abnt(doc: Document, data_acesso: str) -> None:
    """Adiciona a secao REFERENCIAS conforme ABNT NBR 6023:2018."""
    doc.add_paragraph("REFERÊNCIAS", style="heading 6")

    referencias = [
        [
            ("ELMASRI, Ramez; NAVATHE, Shamkant B. ", False),
            ("Sistemas de banco de dados", True),
            (". 7. ed. São Paulo: Pearson Education do Brasil, 2019.", False),
        ],
        [
            ("ORACLE CORPORATION. ", False),
            ("MySQL 5.6 Reference Manual", True),
            (
                f". Redwood Shores: Oracle, 2023. Disponível em: "
                f"<https://dev.mysql.com/doc/refman/5.6/en/>. Acesso em: {data_acesso}.",
                False,
            ),
        ],
        [
            ("SILBERSCHATZ, Abraham; KORTH, Henry F.; SUDARSHAN, S. ", False),
            ("Sistema de banco de dados", True),
            (". 7. ed. Rio de Janeiro: LTC, 2020.", False),
        ],
        [
            ("SQL FIDDLE. ", False),
            (
                "SQL Fiddle: a tool for easy online testing and sharing of database problems and their solutions",
                True,
            ),
            (
                f". 2026. Disponível em: <http://sqlfiddle.com/>. Acesso em: {data_acesso}.",
                False,
            ),
        ],
    ]

    for partes in referencias:
        p = doc.add_paragraph(style="Referências")
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(12)
        for texto, negrito in partes:
            r = p.add_run(texto)
            r.bold = negrito


def ler_blocos_sql() -> dict[str, str]:
    """Le os scripts SQL reais da pasta `sql/` para incorporacao fiel no relatorio."""
    arq_schema = DIR_SQL / "sqlfiddle_01_schema_ddl_dml.sql"
    arq_consultas = DIR_SQL / "sqlfiddle_02_consultas_join.sql"

    schema_txt = arq_schema.read_text(encoding="utf-8")
    idx_dml = schema_txt.find("-- ETAPA 2: DML")
    ddl_txt = schema_txt[:idx_dml].strip()
    dml_txt = schema_txt[idx_dml:].strip()

    consultas_txt = arq_consultas.read_text(encoding="utf-8")
    blocos_raw = [
        b.strip()
        for b in re.split(r"-- -+\r?\n-- (?:VERIFICACAO|CONSULTA \d).*?-- -+\r?\n", consultas_txt, flags=re.DOTALL)
        if b.strip()
    ]
    # Extrair apenas as instrucoes SELECT limpas
    selects = []
    for bloco in consultas_txt.split(";"):
        linhas = [l for l in bloco.splitlines() if l.strip() and not l.strip().startswith("--")]
        if linhas:
            selects.append("\n".join(linhas) + ";")

    if len(selects) != 4:
        raise RuntimeError(f"Esperados 4 blocos SELECT em {arq_consultas}, encontrados {len(selects)}")

    return {
        "ddl": ddl_txt,
        "dml": dml_txt,
        "verificacao": selects[0],
        "consulta1": selects[1],
        "consulta2": selects[2],
        "consulta3": selects[3],
    }


def construir_corpo_relatorio(
    doc: Document,
    dados: dict[str, str],
    evidencias: dict[str, Path],
) -> None:
    """Escreve Introducao, Desenvolvimento, Checklist, Conclusao e Referencias."""
    sqls = ler_blocos_sql()

    # =========================================================================
    # 1 INTRODUCAO
    # =========================================================================
    adicionar_titulo_nivel1(doc, "INTRODUÇÃO")
    adicionar_paragrafo(
        doc,
        "Os sistemas gerenciadores de bancos de dados relacionais (SGBDR) constituem a espinha "
        "dorsal das aplicações corporativas e de comércio eletrônico modernas, assegurando que "
        "informações críticas de clientes, catálogos de produtos e transações comerciais sejam "
        "armazenadas com persistência, consistência e integridade referencial (ELMASRI; NAVATHE, "
        "2019). Por meio da Linguagem de Consulta Estruturada (SQL), profissionais de tecnologia "
        "definem estruturas lógicas, manipulam registros e cruzam múltiplas entidades relacionadas "
        "de maneira declarativa e padronizada (SILBERSCHATZ; KORTH; SUDARSHAN, 2020).",
    )
    adicionar_paragrafo(
        doc,
        "A presente atividade prática da disciplina de Gerenciamento e Desenvolvimento em Banco de "
        "Dados tem como objetivo exercitar, em ambiente controlado, o ciclo completo de construção "
        "e consulta de um banco de dados relacional para uma loja virtual fictícia denominada "
        "LOJABD. Utilizou-se a ferramenta online SQL Fiddle configurada com o motor MySQL 5.6 "
        "(ORACLE CORPORATION, 2023; SQL FIDDLE, 2026), abrangendo instruções de definição de dados "
        "(DDL), manipulação e carga de registros (DML) e consultas analíticas com junções entre "
        "tabelas (DQL com cláusulas INNER JOIN e LEFT JOIN).",
    )
    adicionar_paragrafo(
        doc,
        "Ao longo deste relatório, o leitor encontrará o detalhamento do ambiente computacional "
        "e das decisões técnicas adotadas, os scripts SQL completos utilizados em cada etapa, "
        "as evidências visuais em tela inteira da execução real no SQL Fiddle (MySQL 5.6), os "
        "resultados tabulares obtidos, o checklist de cumprimento integral do roteiro prático e, "
        "por fim, a conclusão sobre os aprendizados consolidados.",
    )

    # =========================================================================
    # 2 DESENVOLVIMENTO
    # =========================================================================
    adicionar_titulo_nivel1(doc, "DESENVOLVIMENTO")
    adicionar_paragrafo(
        doc,
        "O estudo de caso proposto no roteiro prático consiste na modelagem e operacionalização "
        "da base de dados relacional LOJABD, destinada a registrar os dados cadastrais de clientes, "
        "o inventário de produtos e o histórico de vendas de uma loja virtual. A execução foi "
        "organizada em três etapas sequenciais — DDL, DML e DQL — rigorosamente validadas no "
        "ambiente SQL Fiddle com o SGBD MySQL 5.6.",
    )

    # 2.1 Ambiente e Metodologia
    adicionar_titulo_nivel2(doc, "AMBIENTE UTILIZADO E PROCEDIMENTOS METODOLÓGICOS")
    adicionar_paragrafo(
        doc,
        "Os experimentos foram conduzidos na plataforma web SQL Fiddle (http://sqlfiddle.com/), "
        "selecionando-se explicitamente a versão MySQL 5.6 no seletor superior de SGBDs. A "
        "interface do ambiente divide-se em dois painéis principais: à esquerda (Schema Panel), "
        "onde são declaradas e compiladas as instruções DDL e DML por meio do botão Build Schema; "
        "e à direita (Query Panel), onde são executadas as consultas DQL por meio do botão Run SQL, "
        "exibindo a grade de resultados logo abaixo.",
    )
    adicionar_paragrafo(
        doc,
        "Cumpre registrar uma particularidade técnica relevante do ambiente SQL Fiddle: ao iniciar "
        "uma sessão, a plataforma provisiona automaticamente um esquema temporário isolado e "
        "restringe privilégios administrativos de criação de catálogos, retornando erro de acesso "
        "negado caso o comando CREATE DATABASE seja executado diretamente. Dessa forma, os comandos "
        "CREATE DATABASE LOJABD; e USE LOJABD; são mantidos comentados no script de execução "
        "online e ativos no script destinado ao servidor MySQL 5.6 local, garantindo portabilidade "
        "e plena aderência às boas práticas de desenvolvimento.",
    )

    # 2.2 Etapa 1: DDL
    adicionar_titulo_nivel2(doc, "ETAPA 1: CRIAÇÃO DO BANCO DE DADOS E TABELAS (DDL)")
    adicionar_paragrafo(
        doc,
        "Na primeira etapa, modelaram-se as três entidades centrais do domínio: CLIENTE, PRODUTO e "
        "COMPRA. Todas as tabelas foram definidas com o mecanismo de armazenamento InnoDB, "
        "requisito indispensável no MySQL 5.6 para impor a validação estrita de chaves estrangeiras "
        "(FOREIGN KEY) entre COMPRA e as entidades referenciadas. Nas tabelas CLIENTE e PRODUTO, as "
        "chaves primárias (codigo e id) receberam a propriedade AUTO_INCREMENT, enquanto na tabela "
        "COMPRA a chave primária (numero) é informada explicitamente conforme os códigos de venda "
        "do roteiro.",
    )

    adicionar_tabela_abnt(
        doc,
        rotulo="Quadro 1",
        titulo="Estrutura lógica e restrições das tabelas do banco de dados LOJABD",
        colunas=["Tabela", "Atributos e Tipos (MySQL 5.6)", "Restrições de Integridade"],
        larguras_cm=[2.8, 7.6, 5.6],
        linhas=[
            [
                "CLIENTE",
                "codigo (INT), nome (VARCHAR(100)), estado (CHAR(2)), cidade (VARCHAR(100)), telefone (VARCHAR(20))",
                "PK: codigo (AUTO_INCREMENT); atributos NOT NULL.",
            ],
            [
                "PRODUTO",
                "id (INT), nome (VARCHAR(100)), valor (DECIMAL(10,2)), quantidade_estoque (INT)",
                "PK: id (AUTO_INCREMENT); atributos NOT NULL.",
            ],
            [
                "COMPRA",
                "numero (INT), data_compra (DATE), codigo_cliente (INT), id_produto (INT), quantidade_comprada (INT), valor_compra (DECIMAL(10,2))",
                "PK: numero; FK: codigo_cliente -> CLIENTE(codigo); FK: id_produto -> PRODUTO(id).",
            ],
        ],
        fonte="Adaptado do Roteiro de Aula Prática (2026).",
        eh_quadro=True,
    )

    adicionar_bloco_sql(
        doc,
        "Script 1 – Criação do esquema e das tabelas do banco de dados LOJABD (DDL):",
        sqls["ddl"],
    )

    # 2.3 Etapa 2: DML
    adicionar_titulo_nivel2(doc, "ETAPA 2: INSERÇÃO DE DADOS NAS TABELAS (DML)")
    adicionar_paragrafo(
        doc,
        "Com a estrutura relacional definida, procedeu-se à carga inicial dos registros por meio "
        "do comando INSERT INTO, totalizando 7 clientes em CLIENTE (Tabela 1), 4 itens em PRODUTO "
        "(Tabela 2) e 10 vendas em COMPRA (Tabela 3). Para garantir precisão nas datas relativas "
        "exigidas pelo roteiro (current_date + n e current_date - n), empregaram-se as funções "
        "nativas DATE_ADD(CURRENT_DATE, INTERVAL n DAY) e DATE_SUB(CURRENT_DATE, INTERVAL n DAY), "
        "evitando a conversão implícita para inteiro YYYYMMDD que ocorre no MySQL quando se soma "
        "diretamente um escalar a uma data. Além disso, o campo valor_compra foi calculado como o "
        "produto exato entre quantidade_comprada e o valor unitário cadastrado em PRODUTO.",
    )

    adicionar_tabela_abnt(
        doc,
        rotulo="Tabela 1",
        titulo="Registros inseridos na tabela CLIENTE",
        colunas=["Código", "Nome", "Estado", "Cidade", "Telefone"],
        larguras_cm=[2.0, 4.0, 2.0, 4.8, 3.2],
        linhas=[
            ["1", "Fagner", "SP", "P. Prudente", "997989491"],
            ["2", "Maria", "SP", "Campinas", "997989493"],
            ["3", "Marcela", "RJ", "Angra dos Reis", "997989492"],
            ["4", "Caio", "SP", "Assis", "997989495"],
            ["5", "Marcos", "SP", "Campos do Jordão", "997989498"],
            ["6", "Penelope", "MG", "Itajubá", "997989494"],
            ["7", "Rian", "SP", "Santos", "997989490"],
        ],
        fonte="Adaptado do Roteiro de Aula Prática (2026).",
    )

    adicionar_tabela_abnt(
        doc,
        rotulo="Tabela 2",
        titulo="Registros inseridos na tabela PRODUTO",
        colunas=["ID", "Nome", "Valor (R$)", "Quantidade em Estoque"],
        larguras_cm=[2.0, 5.5, 4.0, 4.5],
        linhas=[
            ["1", "Mouse", "200,00", "30"],
            ["2", "Teclado", "250,00", "15"],
            ["3", "Notebook", "3.500,00", "10"],
            ["4", "Fone de ouvido", "150,00", "25"],
        ],
        fonte="Adaptado do Roteiro de Aula Prática (2026).",
    )

    adicionar_tabela_abnt(
        doc,
        rotulo="Tabela 3",
        titulo="Registros inseridos na tabela COMPRA com data relativa e valor calculado",
        colunas=[
            "Número",
            "Expressão de Data (MySQL 5.6)",
            "Cód. Cliente",
            "ID Produto",
            "Qtd.",
            "Valor Compra (R$)",
        ],
        larguras_cm=[1.8, 5.8, 2.2, 2.0, 1.4, 2.8],
        linhas=[
            ["1", "CURRENT_DATE", "1", "4", "1", "150,00"],
            ["2", "DATE_ADD(CURRENT_DATE, INTERVAL 2 DAY)", "2", "2", "2", "500,00"],
            ["3", "DATE_ADD(CURRENT_DATE, INTERVAL 3 DAY)", "3", "1", "2", "400,00"],
            ["4", "DATE_ADD(CURRENT_DATE, INTERVAL 1 DAY)", "4", "3", "1", "3.500,00"],
            ["5", "DATE_SUB(CURRENT_DATE, INTERVAL 2 DAY)", "5", "1", "2", "400,00"],
            ["6", "DATE_SUB(CURRENT_DATE, INTERVAL 5 DAY)", "6", "3", "1", "3.500,00"],
            ["7", "DATE_SUB(CURRENT_DATE, INTERVAL 3 DAY)", "5", "2", "1", "250,00"],
            ["8", "DATE_SUB(CURRENT_DATE, INTERVAL 1 DAY)", "4", "4", "2", "300,00"],
            ["9", "CURRENT_DATE", "3", "4", "3", "450,00"],
            ["10", "DATE_ADD(CURRENT_DATE, INTERVAL 1 DAY)", "2", "2", "4", "1.000,00"],
        ],
        fonte="Elaborado pelo autor a partir do Roteiro de Aula Prática (2026).",
    )

    adicionar_bloco_sql(
        doc,
        "Script 2 – Inserção de dados nas tabelas CLIENTE, PRODUTO e COMPRA (DML):",
        sqls["dml"],
    )

    adicionar_paragrafo(
        doc,
        "Após a inserção dos scripts DDL e DML no painel esquerdo do SQL Fiddle e a ativação do "
        "comando Build Schema, executou-se uma consulta de conferência quantitativa no painel "
        "direito para atestar o carregamento íntegro dos 7 clientes, 4 produtos e 10 compras, "
        "conforme comprovado em tela inteira na Figura 1.",
    )

    adicionar_figura_abnt(
        doc,
        rotulo="Figura 1",
        titulo=IMAGENS_ESPERADAS["fig1"][1],
        caminho_img=evidencias["fig1"],
        fonte="Elaborado pelo autor (2026).",
    )

    # 2.4 Etapa 3: DQL (3 Consultas JOIN)
    adicionar_titulo_nivel2(doc, "ETAPA 3: CONSULTAS RELACIONAIS COM JOIN (DQL)")
    adicionar_paragrafo(
        doc,
        "A terceira etapa compreendeu a elaboração e execução das três consultas DQL solicitadas, "
        "explorando junções internas (INNER JOIN) e junções externas à esquerda (LEFT JOIN) entre "
        "as tabelas do banco LOJABD no ambiente SQL Fiddle (MySQL 5.6).",
    )

    # Consulta 1
    adicionar_paragrafo(
        doc,
        "Na Consulta 1, solicitou-se o retorno do número da venda, nome do cliente, nome do "
        "produto e valor da compra, ordenados crescentemente pelo número da compra. Para tanto, "
        "encadearam-se duas cláusulas INNER JOIN a partir da tabela COMPRA (ligando-a às tabelas "
        "CLIENTE e PRODUTO pelas respectivas chaves estrangeiras) com ordenação explícita por "
        "ORDER BY co.numero ASC. A execução real e os 10 registros resultantes constam na Figura 2 "
        "e na Tabela 4.",
    )
    adicionar_bloco_sql(
        doc,
        "Script 3 – Consulta 1 (INNER JOIN entre COMPRA, CLIENTE e PRODUTO):",
        sqls["consulta1"],
    )
    adicionar_figura_abnt(
        doc,
        rotulo="Figura 2",
        titulo=IMAGENS_ESPERADAS["fig2"][1],
        caminho_img=evidencias["fig2"],
        fonte="Elaborado pelo autor (2026).",
    )
    adicionar_tabela_abnt(
        doc,
        rotulo="Tabela 4",
        titulo="Resultado obtido na Consulta 1 (vendas ordenadas pelo número da compra)",
        colunas=["numero_venda", "nome_cliente", "nome_produto", "valor_compra"],
        larguras_cm=[3.2, 4.4, 4.8, 3.6],
        linhas=[
            ["1", "Fagner", "Fone de ouvido", "150.00"],
            ["2", "Maria", "Teclado", "500.00"],
            ["3", "Marcela", "Mouse", "400.00"],
            ["4", "Caio", "Notebook", "3500.00"],
            ["5", "Marcos", "Mouse", "400.00"],
            ["6", "Penelope", "Notebook", "3500.00"],
            ["7", "Marcos", "Teclado", "250.00"],
            ["8", "Caio", "Fone de ouvido", "300.00"],
            ["9", "Marcela", "Fone de ouvido", "450.00"],
            ["10", "Maria", "Teclado", "1000.00"],
        ],
        fonte="Elaborado pelo autor a partir da execução no SQL Fiddle (2026).",
    )

    # Consulta 2
    adicionar_paragrafo(
        doc,
        "Na Consulta 2, o objetivo foi listar o nome de todos os clientes juntamente com o código "
        "da compra, exibindo o valor NULL para clientes sem compras registradas. Aplicou-se a "
        "junção externa LEFT JOIN partindo da tabela CLIENTE em direção à tabela COMPRA, de modo "
        "a preservar todas as linhas da tabela à esquerda mesmo sem correspondência à direita. "
        "Conforme observado na Figura 3 e na Tabela 5, a consulta retornou 11 linhas, evidenciando "
        "que apenas o cliente Rian (código 7) não realizou compras (codigo_compra igual a NULL).",
    )
    adicionar_bloco_sql(
        doc,
        "Script 4 – Consulta 2 (LEFT JOIN entre CLIENTE e COMPRA para identificar clientes sem compra):",
        sqls["consulta2"],
    )
    adicionar_figura_abnt(
        doc,
        rotulo="Figura 3",
        titulo=IMAGENS_ESPERADAS["fig3"][1],
        caminho_img=evidencias["fig3"],
        fonte="Elaborado pelo autor (2026).",
    )
    adicionar_tabela_abnt(
        doc,
        rotulo="Tabela 5",
        titulo="Resultado obtido na Consulta 2 (clientes e respectivos códigos de compra)",
        colunas=["nome_cliente", "codigo_compra"],
        larguras_cm=[9.0, 7.0],
        linhas=[
            ["Fagner", "1"],
            ["Maria", "2"],
            ["Maria", "10"],
            ["Marcela", "3"],
            ["Marcela", "9"],
            ["Caio", "4"],
            ["Caio", "8"],
            ["Marcos", "5"],
            ["Marcos", "7"],
            ["Penelope", "6"],
            ["Rian", "NULL"],
        ],
        fonte="Elaborado pelo autor a partir da execução no SQL Fiddle (2026).",
    )

    # Consulta 3
    adicionar_paragrafo(
        doc,
        "Na Consulta 3, requereu-se a listagem sem repetições do nome e do telefone dos clientes "
        "que efetuaram compras em data anterior à data atual. Empregou-se INNER JOIN associado ao "
        "modificador SELECT DISTINCT e à cláusula condicional WHERE co.data_compra < CURRENT_DATE. "
        "Como o cliente Marcos realizou duas compras em datas passadas (números 5 e 7), o uso de "
        "DISTINCT evitou sua duplicidade na saída, resultando exclusivamente nos três clientes "
        "apresentados na Figura 4 e na Tabela 6 (Caio, Marcos e Penelope).",
    )
    adicionar_bloco_sql(
        doc,
        "Script 5 – Consulta 3 (INNER JOIN com DISTINCT para compras anteriores à data atual):",
        sqls["consulta3"],
    )
    adicionar_figura_abnt(
        doc,
        rotulo="Figura 4",
        titulo=IMAGENS_ESPERADAS["fig4"][1],
        caminho_img=evidencias["fig4"],
        fonte="Elaborado pelo autor (2026).",
    )
    adicionar_tabela_abnt(
        doc,
        rotulo="Tabela 6",
        titulo="Resultado obtido na Consulta 3 (clientes distintos com compras anteriores à data atual)",
        colunas=["nome_cliente", "telefone"],
        larguras_cm=[9.0, 7.0],
        linhas=[
            ["Caio", "997989495"],
            ["Marcos", "997989498"],
            ["Penelope", "997989494"],
        ],
        fonte="Elaborado pelo autor a partir da execução no SQL Fiddle (2026).",
    )

    # 2.5 Checklist Obrigatório
    adicionar_titulo_nivel2(doc, "CHECKLIST DE VERIFICAÇÃO DA ATIVIDADE")
    adicionar_paragrafo(
        doc,
        "Em atendimento ao roteiro da aula prática, o Quadro 2 sintetiza a verificação integral "
        "dos entregáveis obrigatórios, associando cada item executado às respectivas comprovações "
        "visuais e tabulares presentes neste relatório.",
    )
    adicionar_tabela_abnt(
        doc,
        rotulo="Quadro 2",
        titulo="Checklist obrigatório de verificação das etapas da aula prática",
        colunas=["Item do Checklist (Roteiro)", "Status", "Evidência Comprobatória no Relatório"],
        larguras_cm=[7.0, 2.6, 6.4],
        linhas=[
            [
                "Criação do banco de dados e suas tabelas.",
                "Concluído (✓)",
                "Script 1 (DDL), Quadro 1 e Figura 1 (tela inteira no SQL Fiddle).",
            ],
            [
                "Inserção dos dados em cada uma das 3 tabelas criadas.",
                "Concluído (✓)",
                "Script 2 (DML), Tabelas 1, 2 e 3 e conferência na Figura 1.",
            ],
            [
                "Realização das 3 consultas utilizando o parâmetro JOIN.",
                "Concluído (✓)",
                "Scripts 3, 4 e 5 (DQL), Figuras 2, 3 e 4 e Tabelas 4, 5 e 6.",
            ],
        ],
        fonte="Adaptado do Roteiro de Aula Prática (2026).",
        eh_quadro=True,
    )

    # =========================================================================
    # 3 CONCLUSÃO
    # =========================================================================
    adicionar_titulo_nivel1(doc, "CONCLUSÃO")
    adicionar_paragrafo(
        doc,
        "A realização da atividade prática possibilitou consolidar, de forma aplicada, os "
        "fundamentos de modelagem relacional, integridade referencial e manipulação de dados em "
        "SQL por meio do SGBD MySQL 5.6 no ambiente SQL Fiddle. A criação das tabelas CLIENTE, "
        "PRODUTO e COMPRA com chaves primárias e estrangeiras corretamente tipadas demonstrou como "
        "o mecanismo InnoDB previne inconsistências entre vendas e cadastros vinculados.",
    )
    adicionar_paragrafo(
        doc,
        "Além disso, a execução real das instruções DML e das três consultas com JOIN permitiu "
        "compreender, na prática, a diferença semântica entre INNER JOIN (aplicado para recuperar "
        "exclusivamente registros com correspondência nas entidades relacionadas) e LEFT JOIN "
        "(essencial para identificar clientes sem histórico de pedidos, retornando NULL para Rian), "
        "bem como o papel do modificador DISTINCT aliado a filtros temporais corretos com "
        "DATE_ADD e DATE_SUB.",
    )
    adicionar_paragrafo(
        doc,
        "Conclui-se que todos os objetivos e itens do checklist propostos pela disciplina de "
        "Gerenciamento e Desenvolvimento em Banco de Dados foram plenamente atendidos, com "
        "comprovação integral em tela inteira das execuções reais no ambiente exigido e estrita "
        "conformidade com o modelo textual institucional e as normas ABNT vigentes.",
    )

    # =========================================================================
    # REFERÊNCIAS
    # =========================================================================
    adicionar_referencias_abnt(doc, dados["data_acesso_abnt"])


def ativar_update_fields(docx_path: Path) -> None:
    """Garante `<w:updateFields w:val="true"/>` em `word/settings.xml`."""
    tmp_path = docx_path.with_suffix(".tmp.docx")
    with zipfile.ZipFile(docx_path, "r") as zin, zipfile.ZipFile(
        tmp_path, "w", compression=zipfile.ZIP_DEFLATED
    ) as zout:
        for item in zin.infolist():
            conteudo = zin.read(item.filename)
            if item.filename == "word/settings.xml":
                texto = conteudo.decode("utf-8")
                if "w:updateFields" not in texto:
                    texto = texto.replace(
                        "</w:settings>",
                        '<w:updateFields w:val="true"/></w:settings>',
                    )
                    conteudo = texto.encode("utf-8")
            zout.writestr(item, conteudo)
    tmp_path.replace(docx_path)


def atualizar_sumario_e_exportar_pdf(docx_path: Path, pdf_path: Path) -> None:
    """Usa Microsoft Word via COM (PowerShell) para atualizar o Sumario e gerar PDF."""
    ps_file = Path(__file__).resolve().parent / "atualizar_word_pdf.ps1"
    res = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ps_file),
            "-DocxPath",
            str(docx_path),
            "-PdfPath",
            str(pdf_path),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if res.returncode != 0:
        raise RuntimeError(
            f"Falha ao atualizar Sumario/PDF via Word COM (codigo {res.returncode}):\n"
            f"STDOUT: {res.stdout}\nSTDERR: {res.stderr}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera o relatorio ABNT a partir do Modelo de Atividade Textual (1).docx."
    )
    parser.add_argument(
        "--modo-teste",
        action="store_true",
        help="Usa dados ficticios e imagens placeholder no diretorio --saida-dir para validar o pipeline.",
    )
    parser.add_argument(
        "--atualizar-word",
        action="store_true",
        help="Atualiza o Sumario automatico e exporta PDF usando o Microsoft Word via COM.",
    )
    parser.add_argument(
        "--saida-dir",
        type=Path,
        default=None,
        help="Diretorio de saida para o DOCX e PDF (obrigatorio em --modo-teste).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.modo_teste and args.saida_dir is None:
        raise ValueError("--saida-dir e obrigatorio quando --modo-teste esta ativo.")

    if not ARQ_MODELO.exists():
        raise FileNotFoundError(f"Modelo institucional nao encontrado: {ARQ_MODELO}")

    dados = carregar_dados(modo_teste=args.modo_teste)
    saida_dir = (args.saida_dir or RAIZ).resolve()
    saida_dir.mkdir(parents=True, exist_ok=True)
    evidencias = localizar_evidencias(modo_teste=args.modo_teste, dir_teste=saida_dir)

    nome_docx = dados.get("arquivo_saida_docx", "Relatorio_Aula_Pratica.docx")
    nome_pdf = dados.get("arquivo_saida_pdf", "Relatorio_Aula_Pratica.pdf")
    if args.modo_teste:
        nome_docx = f"TESTE_{nome_docx}"
        nome_pdf = f"TESTE_{nome_pdf}"

    caminho_docx = saida_dir / nome_docx
    caminho_pdf = saida_dir / nome_pdf

    doc = Document(str(ARQ_MODELO))
    atualizar_capa_e_folha_rosto(doc, dados)
    limpar_corpo_exemplo_preservando_sumario(doc)
    construir_corpo_relatorio(doc, dados, evidencias)
    doc.save(str(caminho_docx))
    ativar_update_fields(caminho_docx)

    print(f"DOCX gerado com sucesso: {caminho_docx}")

    if args.atualizar_word:
        atualizar_sumario_e_exportar_pdf(caminho_docx, caminho_pdf)
        print(f"Sumario atualizado e PDF exportado: {caminho_pdf}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
