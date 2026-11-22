"""Gabarito dos experimentos do artigo: planilhas de anotação -> gold.jsonl.

Subcomandos:
- gerar:   cria uma planilha .xlsx por anotador com os parágrafos dos
           artigos e as abas de menções e teor (listas suspensas).
- validar: lê as planilhas preenchidas, localiza cada trecho no parágrafo,
           gera o relatório de erros e um gold.jsonl por anotador.
- split:   divide os artigos em treino/validação/teste (D3).

Decisões de método em docs/decisoes-experimentos.md (D1, D3, D4, D5) e
contrato do gold.jsonl em docs/plano-implementacao-experimentos.md (3.1).

O texto dos parágrafos SEMPRE vem do CSV bruto + segment() de produção
(D5), nunca da aba `paragrafos`: o anotador pode ter editado a planilha, e
os offsets precisam bater com o que o sistema A vê.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import json
import random
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

import yaml  # noqa: E402
from openpyxl import Workbook, load_workbook  # noqa: E402
from openpyxl.styles import Alignment, Font  # noqa: E402
from openpyxl.worksheet.datavalidation import DataValidation  # noqa: E402

from segmentation import segment  # noqa: E402

RAW_CSV = BASE_DIR / "data" / "raw" / "articles_202608191040.csv"
DEFAULT_ENTITIES = BASE_DIR / "data" / "exports" / "target_entities.yaml"

TIPOS = ["DIR", "IND"]
# `indeterminado` = o anotador não conseguiu decidir o teor. `nao_relacionado`
# (rótulo da rodada 1) fica de fora de propósito (decisão da Bea, 26/10).
TEORES = ["positivo", "negativo", "neutro", "indeterminado"]

# Linhas já preparadas com lista suspensa e formato texto nas abas de
# preenchimento. Se o anotador passar disso, a planilha continua aceitando
# (o validador lê qualquer linha), só perde a lista suspensa.
LINHAS_PREPARADAS = 300

MENCOES_COLS = ["paragraph_id", "trecho", "ocorrencia", "tipo", "candidato", "obs"]
TEOR_COLS = ["paragraph_id", "candidato", "teor", "obs"]
TEMPO_COLS = ["article_id", "titulo", "minutos", "obs"]
MINUTOS_MIN, MINUTOS_MAX = 1, 600

SPLIT_RATIOS = {"train": 0.65, "validation": 0.10, "test": 0.25}

INSTRUCOES = [
    "Leia antes o protocolo: docs/protocolo-anotacao-v2.md",
    "",
    "Como preencher esta planilha",
    "",
    "Aba paragrafos: só leitura. Cada parágrafo tem um paragraph_id (artigo-índice).",
    "Aba mencoes: uma linha por menção.",
    "  - trecho: copie exatamente do parágrafo (copiar e colar evita erro de digitação).",
    "  - ocorrencia: só é obrigatória quando o trecho aparece mais de uma vez no parágrafo (1 = primeira).",
    "  - tipo e candidato: escolha na lista suspensa.",
    "Aba teor: uma linha de teor por candidato tratado no parágrafo.",
    "  - use indeterminado quando não der para decidir o teor.",
    f"Aba tempo: minutos gastos em cada artigo (número inteiro de {MINUTOS_MIN} a {MINUTOS_MAX}).",
    "Dúvidas sobre o que anotar: siga o protocolo de anotação da equipe.",
]


# --------------------------------------------------------------------------
# Entradas
# --------------------------------------------------------------------------


def load_entities(path: Path) -> list[dict]:
    """Lê o snapshot de entidades (D4). Exige nome_principal único, porque é
    ele que o anotador escolhe na lista e que vira entity_id no validador."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    entities = data["entities"]
    names = [e["nome_principal"] for e in entities]
    duplicated = sorted({n for n in names if names.count(n) > 1})
    if duplicated:
        raise ValueError(f"nome_principal repetido no arquivo de entidades: {duplicated}")
    return [{"entity_id": str(e["entity_id"]), "nome_principal": e["nome_principal"]} for e in entities]


def read_id_list(path: Path) -> list[str]:
    """Um ID por linha; ignora linhas vazias e repetições (mantém a ordem)."""
    ids: list[str] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if value and value not in ids:
            ids.append(value)
    return ids


def load_articles(csv_path: Path, article_ids: list[str]) -> dict[str, dict]:
    """Devolve {article_id: {"title", "paragraphs"}} na ordem de article_ids,
    segmentando com o segment() de produção (D5). Falha se algum ID não
    existir no CSV ou não tiver extraction_status == "success"."""
    # full_text de algumas notícias passa do limite padrão do módulo csv
    # (128 KB por campo).
    csv.field_size_limit(10**9)
    wanted = set(article_ids)
    found: dict[str, dict] = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["id"] in wanted and row["extraction_status"] == "success":
                found[row["id"]] = {
                    "title": row["title"],
                    "paragraphs": segment("news_article", row["full_text"]),
                }
    missing = [a for a in article_ids if a not in found]
    if missing:
        raise ValueError(f"artigos ausentes no CSV ou sem extraction_status=success: {missing}")
    return {a: found[a] for a in article_ids}


# --------------------------------------------------------------------------
# gerar
# --------------------------------------------------------------------------


def _set_text(cell, value) -> None:
    """Grava como texto puro. Sem isso, o openpyxl trata qualquer string que
    começa com "=" como fórmula (um parágrafo ou título começando com "="
    viraria fórmula na planilha do anotador)."""
    cell.value = value
    cell.data_type = "s"


def build_workbook(articles: dict[str, dict], entities: list[dict]) -> Workbook:
    wb = Workbook()

    # --- paragrafos -------------------------------------------------------
    ws = wb.active
    ws.title = "paragrafos"
    ws.append(["paragraph_id", "article_id", "paragraph_index", "titulo", "texto"])
    for article_id, article in articles.items():
        for idx, text in enumerate(article["paragraphs"]):
            row = ws.max_row + 1
            values = [f"{article_id}-{idx}", article_id, idx, article["title"], text]
            for col, value in enumerate(values, start=1):
                cell = ws.cell(row=row, column=col)
                if isinstance(value, str):
                    _set_text(cell, value)
                else:
                    cell.value = value
                cell.alignment = Alignment(wrap_text=True, vertical="top")
    for col, width in zip("ABCDE", [12, 10, 10, 40, 100]):
        ws.column_dimensions[col].width = width
    for cell in ws[1]:
        cell.font = Font(bold=True)
    ws.freeze_panes = "A2"
    # Proteção sem senha: só evita edição acidental. Selecionar e copiar o
    # trecho continua funcionando, e qualquer um desprotege pelo menu.
    ws.protection.sheet = True
    ws.protection.formatColumns = False
    ws.protection.formatRows = False

    # --- listas (oculta) --------------------------------------------------
    # Lista de candidatos por intervalo numa aba oculta, e não inline: a
    # lista inline do Excel tem limite de 255 caracteres e quebra em vírgula.
    listas = wb.create_sheet("listas")
    listas.append(["candidato"])
    for e in entities:
        _set_text(listas.cell(row=listas.max_row + 1, column=1), e["nome_principal"])
    listas.sheet_state = "hidden"
    candidatos_ref = f"listas!$A$2:$A${len(entities) + 1}"
    last_row = LINHAS_PREPARADAS + 1

    def add_list(sheet, col_letter: str, formula: str) -> None:
        dv = DataValidation(type="list", formula1=formula, allow_blank=True, showErrorMessage=True)
        dv.error = "Escolha um valor da lista."
        sheet.add_data_validation(dv)
        dv.add(f"{col_letter}2:{col_letter}{last_row}")

    def prepare_fill_sheet(title: str, columns: list[str], widths: list[int]) -> object:
        sheet = wb.create_sheet(title)
        sheet.append(columns)
        for cell in sheet[1]:
            cell.font = Font(bold=True)
        for i, width in enumerate(widths):
            sheet.column_dimensions[chr(ord("A") + i)].width = width
        # paragraph_id em formato texto: sem isso, o Excel converte IDs
        # como "2-1" em data (2 de janeiro) assim que o anotador digita.
        for row in range(2, last_row + 1):
            sheet.cell(row=row, column=1).number_format = "@"
        sheet.freeze_panes = "A2"
        return sheet

    # --- mencoes ----------------------------------------------------------
    mencoes = prepare_fill_sheet("mencoes", MENCOES_COLS, [14, 40, 11, 8, 35, 30])
    add_list(mencoes, "D", f'"{",".join(TIPOS)}"')
    add_list(mencoes, "E", candidatos_ref)

    # --- teor -------------------------------------------------------------
    teor = prepare_fill_sheet("teor", TEOR_COLS, [14, 35, 12, 30])
    add_list(teor, "B", candidatos_ref)
    add_list(teor, "C", f'"{",".join(TEORES)}"')

    # --- tempo ------------------------------------------------------------
    # Uma linha pré-preenchida por artigo, na ordem do arquivo de IDs.
    tempo = wb.create_sheet("tempo")
    tempo.append(TEMPO_COLS)
    for cell in tempo[1]:
        cell.font = Font(bold=True)
    for row, (article_id, article) in enumerate(articles.items(), start=2):
        _set_text(tempo.cell(row=row, column=1), article_id)
        _set_text(tempo.cell(row=row, column=2), article["title"])
    for col, width in zip("ABCD", [12, 60, 10, 30]):
        tempo.column_dimensions[col].width = width
    if articles:
        dv = DataValidation(
            type="whole", operator="between", formula1=str(MINUTOS_MIN), formula2=str(MINUTOS_MAX),
            allow_blank=True, showErrorMessage=True,
        )
        dv.error = f"Informe um número inteiro de {MINUTOS_MIN} a {MINUTOS_MAX}."
        tempo.add_data_validation(dv)
        dv.add(f"C2:C{len(articles) + 1}")
    tempo.freeze_panes = "A2"

    # --- instrucoes -------------------------------------------------------
    instrucoes = wb.create_sheet("instrucoes", 0)
    for line in INSTRUCOES:
        instrucoes.append([line])
    instrucoes["A1"].font = Font(bold=True)
    instrucoes["A3"].font = Font(bold=True)
    instrucoes.column_dimensions["A"].width = 110
    return wb


def cmd_gerar(args: argparse.Namespace) -> int:
    entities = load_entities(args.entidades)
    article_ids = read_id_list(args.artigos)
    articles = load_articles(args.csv, article_ids)
    out_dir = Path(args.saida)
    out_dir.mkdir(parents=True, exist_ok=True)

    for annotator in args.anotadores:
        # O nome vira nome de arquivo e, no validar, volta como anotador.
        if not annotator or "/" in annotator or "\\" in annotator or annotator.startswith("."):
            raise ValueError(f"nome de anotador inválido para nome de arquivo: {annotator!r}")

    for annotator in args.anotadores:
        path = out_dir / f"{annotator}.xlsx"
        build_workbook(articles, entities).save(path)
        print(f"gerado: {path}")
    for article_id, article in articles.items():
        n = len(article["paragraphs"])
        aviso = "  (AVISO: nenhum parágrafo após a segmentação)" if n == 0 else ""
        print(f"artigo {article_id}: {n} parágrafos{aviso}")
    return 0


# --------------------------------------------------------------------------
# Localização do trecho
# --------------------------------------------------------------------------


class SpanError(ValueError):
    """Trecho não localizável no parágrafo; a mensagem é o motivo que vai
    para o relatório."""


def _occurrences(haystack: str, needle: str) -> list[int]:
    """Posições de todas as ocorrências, inclusive sobrepostas."""
    positions = []
    pos = haystack.find(needle)
    while pos != -1:
        positions.append(pos)
        pos = haystack.find(needle, pos + 1)
    return positions


def _normalize_with_map(text: str) -> tuple[str, list[int]]:
    """Minúsculas + espaços em sequência colapsados em um. Devolve também,
    para cada caractere do texto normalizado, o índice dele no original --
    é isso que permite devolver offsets no texto ORIGINAL."""
    chars: list[str] = []
    index: list[int] = []
    prev_space = False
    for i, c in enumerate(text):
        if c.isspace():
            if not prev_space:
                chars.append(" ")
                index.append(i)
            prev_space = True
            continue
        prev_space = False
        # lower() pode gerar mais de um caractere (ex.: "İ"); todos apontam
        # para o mesmo caractere original.
        for lc in c.lower():
            chars.append(lc)
            index.append(i)
    return "".join(chars), index


def find_span(paragraph: str, trecho: str, ocorrencia: int | None) -> tuple[int, int, str | None]:
    """Localiza o trecho no parágrafo e devolve (start, end, aviso).

    Busca exata primeiro. Só se não houver nenhuma ocorrência exata, tenta
    ignorando maiúsculas/minúsculas e espaços duplicados (devolve aviso).
    Sem fuzzy: um trecho que não está no texto é erro do anotador e precisa
    ser corrigido, não adivinhado. Levanta SpanError com o motivo."""
    trecho = trecho.strip()
    if not trecho:
        raise SpanError("trecho vazio")

    normalized = False
    positions = _occurrences(paragraph, trecho)
    if positions:
        spans = [(p, p + len(trecho)) for p in positions]
    else:
        normalized = True
        norm_par, index = _normalize_with_map(paragraph)
        norm_trecho, _ = _normalize_with_map(trecho)
        norm_positions = _occurrences(norm_par, norm_trecho)
        if not norm_positions:
            raise SpanError(f"trecho não encontrado no parágrafo: {trecho!r}")
        spans = [(index[p], index[p + len(norm_trecho) - 1] + 1) for p in norm_positions]

    if ocorrencia is None:
        if len(spans) > 1:
            raise SpanError(f"trecho {trecho!r} aparece {len(spans)} vezes no parágrafo; preencha `ocorrencia`")
        ocorrencia = 1
    if ocorrencia < 1 or ocorrencia > len(spans):
        raise SpanError(f"ocorrencia {ocorrencia} inválida: o trecho {trecho!r} aparece {len(spans)} vez(es)")

    start, end = spans[ocorrencia - 1]
    aviso = None
    if normalized:
        aviso = (
            f"trecho {trecho!r} só foi encontrado ignorando maiúsculas/espaços; "
            f"usado {paragraph[start:end]!r} do parágrafo"
        )
    return start, end, aviso


# --------------------------------------------------------------------------
# validar
# --------------------------------------------------------------------------


def _cell_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _parse_int(value) -> int | None:
    """None se vazio; int se válido; levanta ValueError caso contrário."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        raise ValueError
    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError
        return int(value)
    return int(str(value).strip())


def _sheet_rows(wb, sheet_name: str, n_cols: int):
    """(número da linha na planilha, valores) das linhas não vazias."""
    for row_number, values in enumerate(
        wb[sheet_name].iter_rows(min_row=2, max_col=n_cols, values_only=True), start=2
    ):
        if all(v is None or (isinstance(v, str) and not v.strip()) for v in values):
            continue
        yield row_number, values


def validate_workbook(
    wb, annotator: str, articles: dict[str, dict], entities: list[dict]
) -> tuple[list[dict], list[dict]]:
    """Valida uma planilha preenchida contra os parágrafos de `articles`
    (já segmentados a partir do CSV). Devolve (registros do gold.jsonl,
    problemas). Linhas com erro ficam fora dos registros."""
    name_to_id = {e["nome_principal"]: e["entity_id"] for e in entities}
    paragraphs = {
        f"{article_id}-{idx}": text
        for article_id, article in articles.items()
        for idx, text in enumerate(article["paragraphs"])
    }
    issues: list[dict] = []

    def issue(level: str, sheet: str, row: int | None, motivo: str) -> None:
        issues.append({"anotador": annotator, "nivel": level, "aba": sheet, "linha": row, "motivo": motivo})

    def check_paragraph_id(sheet: str, row: int, raw) -> str | None:
        if isinstance(raw, (datetime.datetime, datetime.date)):
            issue("erro", sheet, row, f"paragraph_id virou data ({raw}); formate a coluna como texto e redigite")
            return None
        pid = _cell_text(raw)
        if not pid:
            issue("erro", sheet, row, "paragraph_id vazio")
            return None
        if pid not in paragraphs:
            issue("erro", sheet, row, f"paragraph_id inexistente: {pid!r}")
            return None
        return pid

    def check_candidato(sheet: str, row: int, raw) -> str | None:
        nome = _cell_text(raw)
        if nome not in name_to_id:
            issue("erro", sheet, row, f"candidato fora da lista: {nome!r}")
            return None
        return name_to_id[nome]

    # --- mencoes ----------------------------------------------------------
    mentions_by_pid: dict[str, list[dict]] = {}
    for row, values in _sheet_rows(wb, "mencoes", len(MENCOES_COLS)):
        raw_pid, raw_trecho, raw_ocorrencia, raw_tipo, raw_candidato, _obs = values
        pid = check_paragraph_id("mencoes", row, raw_pid)
        tipo = _cell_text(raw_tipo)
        tipo_ok = tipo in TIPOS
        if not tipo_ok:
            issue("erro", "mencoes", row, f"tipo fora da lista: {tipo!r}")
        entity_id = check_candidato("mencoes", row, raw_candidato)
        try:
            ocorrencia = _parse_int(raw_ocorrencia)
        except ValueError:
            issue("erro", "mencoes", row, f"ocorrencia não é um número inteiro: {raw_ocorrencia!r}")
            continue
        if pid is None:
            continue
        text = paragraphs[pid]
        try:
            start, end, aviso = find_span(text, _cell_text(raw_trecho), ocorrencia)
        except SpanError as exc:
            issue("erro", "mencoes", row, str(exc))
            continue
        if aviso:
            issue("aviso", "mencoes", row, aviso)
        if not tipo_ok or entity_id is None:
            continue
        mentions_by_pid.setdefault(pid, []).append(
            {"start": start, "end": end, "text": text[start:end], "type": tipo, "entity_id": entity_id, "_row": row}
        )

    # --- teor -------------------------------------------------------------
    teor_by_pid: dict[str, dict[str, str]] = {}
    seen_teor: dict[tuple[str, str], int] = {}
    for row, values in _sheet_rows(wb, "teor", len(TEOR_COLS)):
        raw_pid, raw_candidato, raw_teor, _obs = values
        pid = check_paragraph_id("teor", row, raw_pid)
        entity_id = check_candidato("teor", row, raw_candidato)
        teor = _cell_text(raw_teor)
        if teor not in TEORES:
            issue("erro", "teor", row, f"teor fora da lista: {teor!r}")
            continue
        if pid is None or entity_id is None:
            continue
        key = (pid, entity_id)
        if key in seen_teor:
            # Mantém a primeira linha; a repetida é erro para o anotador
            # decidir qual vale (o código de saída já falha).
            issue("erro", "teor", row, f"teor duplicado para {pid} + {_cell_text(raw_candidato)!r} (já na linha {seen_teor[key]})")
            continue
        seen_teor[key] = row
        teor_by_pid.setdefault(pid, {})[entity_id] = teor

    # --- avisos cruzados ---------------------------------------------------
    id_to_name = {v: k for k, v in name_to_id.items()}
    for pid, mentions in mentions_by_pid.items():
        for entity_id in sorted({m["entity_id"] for m in mentions}):
            if entity_id not in teor_by_pid.get(pid, {}):
                rows = [m["_row"] for m in mentions if m["entity_id"] == entity_id]
                issue("aviso", "mencoes", rows[0], f"menção a {id_to_name[entity_id]!r} em {pid} sem linha de teor")
        ordered = sorted(mentions, key=lambda m: (m["start"], m["end"]))
        for i, a in enumerate(ordered):
            for b in ordered[i + 1 :]:
                if b["start"] >= a["end"]:
                    break
                issue("aviso", "mencoes", b["_row"], f"trecho sobreposto ao da linha {a['_row']} em {pid}")

    # --- registros ---------------------------------------------------------
    records = []
    for article_id, article in articles.items():
        for idx, text in enumerate(article["paragraphs"]):
            pid = f"{article_id}-{idx}"
            mentions = sorted(mentions_by_pid.get(pid, []), key=lambda m: (m["start"], m["end"]))
            records.append(
                {
                    "article_id": article_id,
                    "paragraph_index": idx,
                    "text": text,
                    "split": None,
                    "mentions": [{k: v for k, v in m.items() if k != "_row"} for m in mentions],
                    "teor": teor_by_pid.get(pid, {}),
                    "annotator": annotator,
                }
            )
    return records, issues


def validate_tempo(wb, annotator: str, articles: dict[str, dict]) -> tuple[list[dict], list[dict]]:
    """Lê a aba `tempo`: uma linha de saída por artigo de `articles`.
    Vazio (ou planilha antiga sem a aba) é aviso; valor que não é inteiro de
    MINUTOS_MIN a MINUTOS_MAX é erro, a mesma regra da validação de dados."""
    issues: list[dict] = []

    def issue(level: str, row: int | None, motivo: str) -> None:
        issues.append({"anotador": annotator, "nivel": level, "aba": "tempo", "linha": row, "motivo": motivo})

    by_article: dict[str, tuple[int, object]] = {}
    if "tempo" in wb.sheetnames:
        for row, values in _sheet_rows(wb, "tempo", len(TEMPO_COLS)):
            by_article.setdefault(_cell_text(values[0]), (row, values[2]))

    rows = []
    for article_id, article in articles.items():
        row, raw = by_article.get(article_id, (None, None))
        minutos = None
        try:
            minutos = _parse_int(raw)
        except ValueError:
            issue("erro", row, f"minutos não é um número inteiro no artigo {article_id}: {raw!r}")
        else:
            if minutos is None:
                issue("aviso", row, f"tempo não informado no artigo {article_id}")
            elif not MINUTOS_MIN <= minutos <= MINUTOS_MAX:
                issue("erro", row, f"minutos fora de {MINUTOS_MIN}-{MINUTOS_MAX} no artigo {article_id}: {minutos}")
                minutos = None
        rows.append(
            {
                "anotador": annotator,
                "article_id": article_id,
                "n_paragrafos": len(article["paragraphs"]),
                "minutos": minutos,
            }
        )
    return rows, issues


def _articles_in_workbook(wb) -> list[str]:
    """Os artigos a validar são os listados na aba `paragrafos` (só o
    article_id; o texto vem do CSV)."""
    ids: list[str] = []
    for values in wb["paragrafos"].iter_rows(min_row=2, min_col=2, max_col=2, values_only=True):
        article_id = _cell_text(values[0])
        if article_id and article_id not in ids:
            ids.append(article_id)
    return ids


def cmd_validar(args: argparse.Namespace) -> int:
    entities = load_entities(args.entidades)
    out_dir = Path(args.saida)
    out_dir.mkdir(parents=True, exist_ok=True)
    all_issues: list[dict] = []
    all_tempo: list[dict] = []

    for path in map(Path, args.planilhas):
        annotator = path.stem
        wb = load_workbook(path, data_only=True)
        articles = load_articles(args.csv, _articles_in_workbook(wb))
        records, issues = validate_workbook(wb, annotator, articles, entities)
        tempo_rows, tempo_issues = validate_tempo(wb, annotator, articles)
        issues.extend(tempo_issues)
        all_issues.extend(issues)
        all_tempo.extend(tempo_rows)

        gold_path = out_dir / f"{annotator}.gold.jsonl"
        with open(gold_path, "w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        n_err = sum(1 for i in issues if i["nivel"] == "erro")
        n_warn = len(issues) - n_err
        n_mentions = sum(len(r["mentions"]) for r in records)
        n_teor = sum(len(r["teor"]) for r in records)
        print(f"\n== {annotator} ({path.name}) ==")
        print(
            f"{len(articles)} artigos, {len(records)} parágrafos, {n_mentions} menções e "
            f"{n_teor} teores válidos | {n_err} erro(s), {n_warn} aviso(s) -> {gold_path}"
        )
        for i in issues:
            print(f"  [{i['nivel'].upper()}] {i['aba']} linha {i['linha']}: {i['motivo']}")

    report_path = out_dir / "relatorio.csv"
    with open(report_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["anotador", "nivel", "aba", "linha", "motivo"])
        writer.writeheader()
        writer.writerows(all_issues)
    tempo_path = out_dir / "tempo.csv"
    with open(tempo_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["anotador", "article_id", "n_paragrafos", "minutos"])
        writer.writeheader()
        writer.writerows(all_tempo)
    print(f"\nrelatório: {report_path}")
    print(f"tempo: {tempo_path}")
    return 1 if any(i["nivel"] == "erro" for i in all_issues) else 0


# --------------------------------------------------------------------------
# split
# --------------------------------------------------------------------------


def split_articles(article_ids: list[str], shared: list[str], seed: int = 42) -> tuple[dict[str, str], list[str]]:
    """Divide POR ARTIGO (D3). Os compartilhados vão todos para o teste e
    contam na cota dele. Devolve ({article_id: split}, avisos).

    Determinístico: ordena os IDs antes de embaralhar, então a ordem do
    arquivo de entrada não muda o resultado."""
    missing = [a for a in shared if a not in article_ids]
    if missing:
        raise ValueError(f"compartilhados fora da lista de artigos: {missing}")
    warnings = []
    n = len(article_ids)
    n_test = round(n * SPLIT_RATIOS["test"])
    n_val = round(n * SPLIT_RATIOS["validation"])
    if len(shared) > n_test:
        warnings.append(
            f"{len(shared)} compartilhados passam da cota de teste ({n_test}); todos ficam no teste"
        )

    rest = sorted(set(article_ids) - set(shared))
    random.Random(seed).shuffle(rest)
    n_test_rest = max(0, n_test - len(shared))
    assignment = {a: "test" for a in shared}
    for i, article_id in enumerate(rest):
        if i < n_test_rest:
            assignment[article_id] = "test"
        elif i < n_test_rest + n_val:
            assignment[article_id] = "validation"
        else:
            assignment[article_id] = "train"
    return assignment, warnings


def cmd_split(args: argparse.Namespace) -> int:
    article_ids = read_id_list(args.artigos)
    shared = read_id_list(args.compartilhados) if args.compartilhados else []
    assignment, warnings = split_articles(article_ids, shared, args.seed)
    for w in warnings:
        print(f"AVISO: {w}")
    out = Path(args.saida)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(sorted(assignment.items())), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name in ["train", "validation", "test"]:
        print(f"{name}: {sum(1 for s in assignment.values() if s == name)} artigos")
    print(f"gravado: {out}")
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("gerar", help="gera uma planilha de anotação por anotador")
    p.add_argument("--artigos", required=True, type=Path, help="arquivo com um article_id por linha")
    p.add_argument("--anotadores", required=True, nargs="+", help="nomes (viram o nome do arquivo)")
    p.add_argument("--saida", required=True, type=Path, help="pasta de saída das planilhas")
    p.add_argument("--entidades", type=Path, default=DEFAULT_ENTITIES)
    p.add_argument("--csv", type=Path, default=RAW_CSV, help="CSV bruto de artigos")
    p.set_defaults(func=cmd_gerar)

    p = sub.add_parser("validar", help="valida planilhas preenchidas e gera gold.jsonl por anotador")
    p.add_argument("planilhas", nargs="+", type=Path, help=".xlsx preenchidos (anotador = nome do arquivo)")
    p.add_argument("--saida", required=True, type=Path, help="pasta para <anotador>.gold.jsonl e relatorio.csv")
    p.add_argument("--entidades", type=Path, default=DEFAULT_ENTITIES)
    p.add_argument("--csv", type=Path, default=RAW_CSV, help="CSV bruto de artigos")
    p.set_defaults(func=cmd_validar)

    p = sub.add_parser("split", help="divide os artigos em treino/validação/teste")
    p.add_argument("--artigos", required=True, type=Path, help="arquivo com um article_id por linha")
    p.add_argument("--compartilhados", type=Path, help="article_ids anotados por todos (vão para o teste)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--saida", required=True, type=Path, help="caminho do split.json")
    p.set_defaults(func=cmd_split)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ValueError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
