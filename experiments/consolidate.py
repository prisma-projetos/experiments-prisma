"""Referência do piloto por voto da maioria (D17), sem alterar as fontes.

Subcomandos:
- consolidar: lê as planilhas atuais dos cinco votantes do piloto e gera
              referencia-provisoria.jsonl (formato do gold.jsonl de gold.py),
              pendencias.xlsx para Bea desempatar, report.md e report.json.
- aplicar:    lê pendencias.xlsx preenchida e gera referencia.jsonl e
              decisoes-desempate.json numa saída nova.

Uma resposta entra quando pelo menos 3 dos 5 votantes concordam. O resto
vira pendência para Bea ou descarte listado no relatório; nenhuma heurística
decide no lugar dela. Referências genéricas de partido (D15) e trechos de
parágrafo inteiro não contam como voto. As planilhas são lidas com o mesmo
leitor de agreement.py e conferidas por SHA-256 antes e depois.

Executar da raiz: .venv-experiments/bin/python experiments/consolidate.py --help
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.datavalidation import DataValidation

try:
    from . import agreement, gold
except ImportError:
    import agreement
    import gold

BASE_DIR = agreement.BASE_DIR
PILOTO = BASE_DIR / "experiments/data/anotacao/piloto"
# D17: cinco votantes. Anderson fica fora (planilha editada por Bea antes do
# primeiro backup; contaria o critério dela duas vezes).
VOTERS = {
    "Beatriz": PILOTO / "beatriz.xlsx",
    "Cristovam": PILOTO / "cristovam (1).xlsx",
    "Gustavo": PILOTO / "gustavo - Planilha.xlsx",
    "Lucas": PILOTO / "Lucas - Planilha.xlsx",
    "Nicolas": PILOTO / "nicolas.xlsx",
}
OUT_OF_VOTE = {"Anderson": "D17: planilha editada por Bea antes do primeiro backup; contaria o critério dela duas vezes."}
N_VOTERS = 5
MIN_VOTES = 3
PILOT_IDS = BASE_DIR / "experiments/data/piloto_ids.txt"
DEFAULT_OUTPUT = BASE_DIR / "experiments/results/piloto-referencia"
CONSOLIDATE_OUTPUTS = ("referencia-provisoria.jsonl", "pendencias.xlsx", "report.md", "report.json")
APPLY_OUTPUTS = ("referencia.jsonl", "decisoes-desempate.json")
PENDING_KINDS = ("mencao_tipo", "mencao_limites", "mencao_entidades", "teor_empate")
PENDENCIAS_COLS = ["id", "tipo", "paragraph_id", "texto_paragrafo", "opcoes", "decisoes_validas", "decisao", "observacao"]
FORA = "fora"

# D15: o trecho inteiro é só artigo/contração + partido/legenda/sigla.
# "Partido Liberal" ou "o Partido dos Trabalhadores" não casam (fullmatch).
GENERIC_PARTY = re.compile(
    r"(?:(?:o|a|os|as|do|da|dos|das|no|na|nos|nas|ao|à|aos|às|pelo|pela|pelos|pelas)\s)?"
    r"(?:partido|legenda|sigla)s?"
)

LIMITATIONS = [
    "A referência não é um gabarito adjudicado nem vem de respostas totalmente independentes: as planilhas atuais passaram por revisão (D17).",
    "As regras D10 a D12 foram formuladas olhando o piloto, o que tende a favorecer a heurística avaliada nele.",
    "O protocolo mudou depois do piloto (D15). As respostas originais não foram alteradas; a exclusão de referências genéricas acontece só aqui.",
    "Cinco notícias não permitem generalização.",
]
OPEN_POINTS = [
    "A aba de teor não diz qual trecho motivou a linha. Um teor de partido gerado só por referência genérica (D15) não é detectável automaticamente; ele aparece como alerta de teor sem menção, marcado quando houve exclusão D15 da mesma entidade no parágrafo.",
    "Trechos minoritários sobrepostos a um trecho aceito da mesma entidade são descartados, porque a regra exige o trecho exato. Se outra entidade sem trecho aceito somar 3 votantes no grupo, vira pendência.",
    "Menção repetida pelo mesmo votante com tipos diferentes: o trecho conta um voto, mas o voto de tipo desse votante não conta. Não havia regra para isso.",
    "A exclusão D15 só reconhece o trecho inteiro igual a artigo/contração + partido, legenda ou sigla (singular ou plural). Trechos maiores, como \"o partido do presidente\", passam pela votação normal.",
]


# --------------------------------------------------------------------------
# Consolidação (sem arquivos)
# --------------------------------------------------------------------------


def _pid(record: dict) -> str:
    return f"{record['article_id']}-{record['paragraph_index']}"


def is_generic_party(text: str) -> bool:
    """D15: "o partido", "A Legenda", "das siglas"... (ignora maiúsculas e
    espaços repetidos)."""
    normalized = " ".join(unicodedata.normalize("NFC", text).lower().split())
    return GENERIC_PARTY.fullmatch(normalized) is not None


def _overlap_components(keys) -> list[list[tuple[int, int, str]]]:
    """Agrupa unidades (start, end, entity_id) cujos trechos se sobrepõem,
    direta ou encadeadamente, sem olhar a entidade."""
    groups, end = [], -1
    for key in sorted(keys):
        if groups and key[0] < end:
            groups[-1].append(key)
            end = max(end, key[1])
        else:
            groups.append([key])
            end = key[1]
    return groups


def _majority_type(unit: dict[str, set[str]]) -> str | None:
    """Maioria simples entre quem marcou o trecho. Votante com tipos
    conflitantes na mesma unidade não conta para o tipo."""
    counts = Counter(next(iter(types)) for types in unit.values() if len(types) == 1)
    total = sum(counts.values())
    for tipo, n in counts.items():
        if n * 2 > total:
            return tipo
    return None


def inconsistency_alerts(records: list[dict], d15_items: list[dict] = ()) -> dict:
    """Regra 5: alerta, sem resolver. O protocolo exige teor para toda
    entidade com menção no parágrafo; teor sem menção pode ser legítimo
    (sujeito oculto), por isso também é só alerta."""
    d15 = {(item["paragraph_id"], item["entity_id"]) for item in d15_items}
    alerts = {"mencao_sem_teor": [], "teor_sem_mencao": [], "mencoes_sobrepostas": []}
    for record in records:
        pid = _pid(record)
        mentioned = {str(m["entity_id"]) for m in record["mentions"]}
        rated = {str(eid): label for eid, label in record["teor"].items()}
        for eid in sorted(mentioned - set(rated)):
            alerts["mencao_sem_teor"].append({"paragraph_id": pid, "entity_id": eid})
        for eid in sorted(set(rated) - mentioned):
            alerts["teor_sem_mencao"].append({
                "paragraph_id": pid, "entity_id": eid, "teor": rated[eid],
                "referencia_generica_d15_no_paragrafo": (pid, eid) in d15,
            })
        ordered = sorted(record["mentions"], key=lambda m: (m["start"], m["end"]))
        for i, a in enumerate(ordered):
            for b in ordered[i + 1:]:
                if b["start"] >= a["end"]:
                    break
                alerts["mencoes_sobrepostas"].append({
                    "paragraph_id": pid,
                    "trechos": [{k: m[k] for k in ("start", "end", "text", "entity_id")} for m in (a, b)],
                })
    return alerts


def consolidate(annotators: dict[str, list[dict]]) -> dict:
    """Aplica a regra de 3 de 5 a registros no formato do gold.jsonl.

    Devolve a referência provisória (`records`), as pendências, os
    descartes, as exclusões, as contagens e os alertas. Não lê nem grava
    arquivos."""
    if len(annotators) != N_VOTERS:
        raise ValueError(f"a consolidação exige exatamente {N_VOTERS} votantes; recebeu {len(annotators)}")
    paragraphs: dict[str, dict] = {}
    for records in annotators.values():
        for record in records:
            pid = _pid(record)
            known = paragraphs.setdefault(pid, {k: record[k] for k in ("article_id", "paragraph_index", "text")})
            if known["text"] != record["text"]:
                raise ValueError(f"texto do parágrafo {pid} difere entre votantes")
    order = {pid: i for i, pid in enumerate(paragraphs)}

    # --- menções: exclusões e votos por unidade (parágrafo, início, fim, entidade)
    excluded = {"d15_partido_generico": [], "paragrafo_inteiro": []}
    duplicates = []
    votes: dict[str, dict[tuple[int, int, str], dict[str, set[str]]]] = {}
    for voter, records in annotators.items():
        for record in records:
            pid = _pid(record)
            for mention in record["mentions"]:
                start, end, eid = mention["start"], mention["end"], str(mention["entity_id"])
                item = {"paragraph_id": pid, "votante": voter, "start": start, "end": end,
                        "text": mention["text"], "type": mention["type"], "entity_id": eid}
                if is_generic_party(mention["text"]):
                    excluded["d15_partido_generico"].append(item)
                elif start == 0 and end == len(record["text"]):
                    # Mesmo critério de agreement.py; não conta como voto.
                    excluded["paragrafo_inteiro"].append(item)
                else:
                    unit = votes.setdefault(pid, {}).setdefault((start, end, eid), {})
                    if voter in unit:
                        duplicates.append(item)
                    unit.setdefault(voter, set()).add(mention["type"])
    conflicting_types = [
        {"paragraph_id": pid, "votante": voter, "start": key[0], "end": key[1],
         "text": paragraphs[pid]["text"][key[0]:key[1]], "entity_id": key[2], "types": sorted(types)}
        for pid, units in votes.items() for key, unit in units.items()
        for voter, types in unit.items() if len(types) > 1
    ]

    mentions: dict[str, list[dict]] = {pid: [] for pid in paragraphs}
    teor: dict[str, dict[str, str]] = {pid: {} for pid in paragraphs}
    pending: list[dict] = []
    discarded_mentions: list[dict] = []
    discarded_teor: list[dict] = []
    mention_votes, teor_votes = Counter(), Counter()

    def text_of(pid: str, key: tuple) -> str:
        return paragraphs[pid]["text"][key[0]:key[1]]

    def options(pid: str, keys: list[tuple]) -> list[dict]:
        """Uma opção por (trecho, entidade, tipo) com os votantes de cada."""
        result = []
        for key in keys:
            unit = votes[pid][key]
            for tipo in gold.TIPOS:
                voters = sorted(v for v, types in unit.items() if tipo in types)
                if voters:
                    result.append({"n": len(result) + 1, "start": key[0], "end": key[1], "text": text_of(pid, key),
                                   "entity_id": key[2], "type": tipo, "votantes": voters})
        return result

    def add_mention_pending(kind: str, pid: str, keys: list[tuple], accepted: list[tuple] = ()) -> None:
        opts = options(pid, keys)
        valid = [str(o["n"]) for o in opts] + ([] if kind == "mencao_tipo" else [FORA])
        pending.append({
            "id": None, "tipo": kind, "paragraph_id": pid, "entity_ids": sorted({k[2] for k in keys}),
            "opcoes": opts, "decisoes_validas": valid,
            "sobrepoe_aceitos": [{"start": k[0], "end": k[1], "text": text_of(pid, k), "entity_id": k[2]} for k in accepted],
        })

    def discard(pid: str, keys: list[tuple], motivo: str) -> None:
        for key in keys:
            discarded_mentions.append({"paragraph_id": pid, "start": key[0], "end": key[1], "text": text_of(pid, key),
                                       "entity_id": key[2], "votantes": sorted(votes[pid][key]), "motivo": motivo})

    for pid in paragraphs:
        units = votes.get(pid, {})
        for component in _overlap_components(units):
            # Regra 1: trecho exato com a mesma entidade e >= 3 votantes.
            accepted = [key for key in component if len(units[key]) >= MIN_VOTES]
            if not accepted:
                # Regra 2: grupo sobreposto sem trecho majoritário.
                voters = set().union(*(units[key] for key in component))
                if len(voters) >= MIN_VOTES:
                    kind = "mencao_limites" if len({key[2] for key in component}) == 1 else "mencao_entidades"
                    add_mention_pending(kind, pid, component)
                else:
                    discard(pid, component, "sem maioria, descartado")
                continue
            for key in accepted:
                tipo = _majority_type(units[key])
                if tipo is None:
                    add_mention_pending("mencao_tipo", pid, [key])
                else:
                    mentions[pid].append({"start": key[0], "end": key[1], "text": text_of(pid, key),
                                          "type": tipo, "entity_id": key[2]})
                    mention_votes[len(units[key])] += 1
            rest = [key for key in component if key not in accepted]
            accepted_entities = {key[2] for key in accepted}
            for eid in sorted({key[2] for key in rest}):
                group = [key for key in rest if key[2] == eid]
                voters = set().union(*(units[key] for key in group))
                if eid not in accepted_entities and len(voters) >= MIN_VOTES:
                    add_mention_pending("mencao_limites", pid, group, accepted)
                else:
                    discard(pid, group, "sem maioria, descartado (sobrepõe trecho aceito)")

    # --- teor: unidade (parágrafo, entidade); ausência não é rótulo ----------
    labels: dict[tuple[str, str], dict[str, str]] = {}
    for voter, records in annotators.items():
        for record in records:
            for eid, label in record["teor"].items():
                labels.setdefault((_pid(record), str(eid)), {})[voter] = label
    for pid, eid in sorted(labels, key=lambda k: (order[k[0]], k[1])):
        given = labels[(pid, eid)]
        missing = sorted(set(annotators) - set(given))
        if len(given) < MIN_VOTES:
            discarded_teor.append({"paragraph_id": pid, "entity_id": eid, "rotulos": given, "sem_rotulo": missing,
                                   "motivo": "sem maioria, descartado (menos de 3 votantes deram rótulo)"})
            continue
        label, n = Counter(given.values()).most_common(1)[0]
        if n >= MIN_VOTES:
            teor[pid][eid] = label
            teor_votes[n] += 1
            continue
        voted = sorted(set(given.values()), key=gold.TEORES.index)
        pending.append({
            "id": None, "tipo": "teor_empate", "paragraph_id": pid, "entity_id": eid,
            "opcoes": [{"n": i, "label": value, "votantes": sorted(v for v, x in given.items() if x == value)}
                       for i, value in enumerate(voted, start=1)],
            "sem_rotulo": missing, "decisoes_validas": [*gold.TEORES, FORA],
        })

    numbers = Counter()
    for item in pending:
        prefix = "T" if item["tipo"] == "teor_empate" else "M"
        numbers[prefix] += 1
        item["id"] = f"{prefix}{numbers[prefix]:03d}"

    records = [
        {
            "article_id": p["article_id"], "paragraph_index": p["paragraph_index"], "text": p["text"], "split": None,
            "mentions": sorted(mentions[pid], key=lambda m: (m["start"], m["end"], m["entity_id"])),
            "teor": dict(sorted(teor[pid].items())), "annotator": "referencia-provisoria",
        }
        for pid, p in paragraphs.items()
    ]
    return {
        "records": records,
        "pendencias": pending,
        "contagens": {
            "mencoes_aceitas_por_votos": {str(n): mention_votes[n] for n in (5, 4, 3)},
            "teor_aceito_por_votos": {str(n): teor_votes[n] for n in (5, 4, 3)},
            "pendencias_por_tipo": {kind: sum(p["tipo"] == kind for p in pending) for kind in PENDING_KINDS},
            "mencoes_descartadas": len(discarded_mentions), "teor_descartado": len(discarded_teor),
            "exclusoes_d15": len(excluded["d15_partido_generico"]),
            "exclusoes_paragrafo_inteiro": len(excluded["paragrafo_inteiro"]),
            "mencoes_repetidas": len(duplicates), "tipos_conflitantes": len(conflicting_types),
        },
        "descartes": {"mencoes": discarded_mentions, "teor": discarded_teor},
        "exclusoes": excluded,
        "duplicatas": {"mencoes_repetidas": duplicates, "tipos_conflitantes": conflicting_types},
        "alertas": inconsistency_alerts(records, excluded["d15_partido_generico"]),
    }


# --------------------------------------------------------------------------
# consolidar
# --------------------------------------------------------------------------


def build_report(*, sources: dict[str, Path] = VOTERS, csv_path: Path = gold.RAW_CSV,
                 entities_path: Path = gold.DEFAULT_ENTITIES, ids_path: Path = PILOT_IDS) -> tuple[dict, list[dict]]:
    """Lê as fontes como agreement.py (somente leitura, SHA-256 antes e
    depois) e consolida. Devolve (relatório, registros da referência)."""
    if len(sources) != N_VOTERS:
        raise ValueError(f"D17 exige exatamente {N_VOTERS} votantes; recebeu {len(sources)}")
    paths = {**{name: Path(path) for name, path in sources.items()},
             "raw_csv": Path(csv_path), "entities": Path(entities_path), "pilot_ids": Path(ids_path),
             "gold_code": Path(gold.__file__), "agreement_code": Path(agreement.__file__),
             "consolidate_code": Path(__file__)}
    before = {name: agreement._sha256(path) for name, path in paths.items()}
    articles = gold.load_articles(csv_path, gold.read_id_list(ids_path))
    entities = gold.load_entities(entities_path)
    annotators, coverage = {}, {}
    for name in sources:
        annotators[name], coverage[name] = agreement._read_source(paths[name], name, articles, entities)
    result = consolidate(annotators)
    after = {name: agreement._sha256(path) for name, path in paths.items()}
    if after != before:
        raise RuntimeError("entrada alterada durante a consolidação")
    report = {
        "schema_version": 1, "purpose": "referência provisória do piloto por voto da maioria (D17)",
        "inputs": {name: {"path": agreement._path(path), "sha256": before[name]} for name, path in paths.items()},
        "inputs_unchanged": True,
        "settings": {"votantes": list(sources), "n_votantes": N_VOTERS, "min_votos": MIN_VOTES,
                     "fora_da_votacao": OUT_OF_VOTE},
        "article_ids": list(articles),
        "entities": {e["entity_id"]: e["nome_principal"] for e in entities},
        "coverage": coverage,
        **{key: value for key, value in result.items() if key != "records"},
        "em_aberto": OPEN_POINTS, "limitations": LIMITATIONS,
    }
    return report, result["records"]


def _option_lines(pending: dict, name) -> list[str]:
    if pending["tipo"] == "teor_empate":
        lines = [f"entidade: {name(pending['entity_id'])}"]
        lines += [f"{o['label']}: {', '.join(o['votantes'])}" for o in pending["opcoes"]]
        lines.append(f"sem rótulo: {', '.join(pending['sem_rotulo']) or 'ninguém'}")
        return lines
    lines = [f"{o['n']}) \"{o['text']}\" [{o['start']}:{o['end']}] -> {name(o['entity_id'])} ({o['type']}) | votos: {', '.join(o['votantes'])}"
             for o in pending["opcoes"]]
    lines += [f"sobrepõe trecho já aceito: \"{a['text']}\" -> {name(a['entity_id'])}" for a in pending["sobrepoe_aceitos"]]
    return lines


def build_pendencias_workbook(pendencias: list[dict], texts: dict[str, str], names: dict[str, str]) -> Workbook:
    """Uma linha por pendência; `decisao` e `observacao` ficam vazias."""
    name = lambda eid: names.get(eid, eid)
    wb = Workbook()
    ws = wb.active
    ws.title = "pendencias"
    ws.append(PENDENCIAS_COLS)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for col, width in zip("ABCDEFGH", [8, 18, 12, 80, 80, 22, 14, 40]):
        ws.column_dimensions[col].width = width
    decision_col = PENDENCIAS_COLS.index("decisao") + 1
    validations: dict[tuple[str, bool], DataValidation] = {}
    for row, item in enumerate(pendencias, start=2):
        multiple = item["tipo"] in ("mencao_limites", "mencao_entidades")
        values = [item["id"], item["tipo"], item["paragraph_id"], texts[item["paragraph_id"]],
                  "\n".join(_option_lines(item, name)), ", ".join(item["decisoes_validas"])]
        for col, value in enumerate(values, start=1):
            cell = ws.cell(row=row, column=col)
            gold._set_text(cell, value)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
        # Texto: no Excel em pt-BR, "1,3" digitado viraria o número 1,3.
        for col in (decision_col, decision_col + 1):
            ws.cell(row=row, column=col).number_format = "@"
        key = (",".join(item["decisoes_validas"]), multiple)
        if key not in validations:
            dv = DataValidation(type="list", formula1=f'"{key[0]}"', allow_blank=True, showErrorMessage=True)
            if multiple:
                # Aviso em vez de bloqueio: permite combinar opções (ex.: 1;3).
                dv.errorStyle = "warning"
                dv.error = "Valor fora da lista. Para escolher mais de uma opção, separe os números com ponto e vírgula (ex.: 1;3)."
            else:
                dv.error = "Escolha um valor da lista."
            ws.add_data_validation(dv)
            validations[key] = dv
        validations[key].add(ws.cell(row=row, column=decision_col).coordinate)
    ws.freeze_panes = "A2"

    instrucoes = wb.create_sheet("instrucoes")
    for line in [
        "Preencha a coluna decisao de todas as linhas da aba pendencias. A coluna observacao é opcional.",
        "teor_empate: escolha positivo, negativo, neutro ou indeterminado. fora = o par não entra na referência.",
        "mencao_tipo: escreva o número da opção (cada opção é o mesmo trecho com um tipo).",
        "mencao_limites e mencao_entidades: escreva o número de uma opção ou de várias, separadas por ponto e vírgula (ex.: 1;3). fora = nenhum trecho do grupo entra.",
        "Não altere as colunas id, tipo e paragraph_id. Depois rode o subcomando aplicar de experiments/consolidate.py.",
    ]:
        instrucoes.append([line])
    instrucoes.column_dimensions["A"].width = 120
    return wb


def render_markdown(report: dict) -> str:
    names = report["entities"]

    def name(eid: str) -> str:
        return names.get(eid, eid)

    def mention(item: dict) -> str:
        return f"{item['paragraph_id']} \"{item['text']}\" [{item['start']}:{item['end']}] -> {name(item['entity_id'])}"

    settings, counts, alerts = report["settings"], report["contagens"], report["alertas"]
    m_votes, t_votes = counts["mencoes_aceitas_por_votos"], counts["teor_aceito_por_votos"]
    d15, whole = report["exclusoes"]["d15_partido_generico"], report["exclusoes"]["paragrafo_inteiro"]
    lines = [
        "# Referência provisória do piloto por voto da maioria", "",
        "Gerado por `experiments/consolidate.py consolidar`. A referência fica provisória até Bea decidir as pendências de `pendencias.xlsx` e rodar `aplicar`. Não é um gabarito adjudicado (D17).", "",
        "## Configuração", "",
        f"- Votantes ({settings['n_votantes']}): {', '.join(settings['votantes'])}.",
        f"- Uma unidade entra na referência com pelo menos {settings['min_votos']} votos.",
        *[f"- Fora da votação: {who}. {why}" for who, why in settings["fora_da_votacao"].items()],
        f"- Notícias: {', '.join(report['article_ids'])}.", "",
        "## Unidades aceitas", "",
        "| Unidade | 5/5 | 4/5 | 3/5 | Total |", "|---|---:|---:|---:|---:|",
        f"| Menção (trecho + entidade) | {m_votes['5']} | {m_votes['4']} | {m_votes['3']} | {sum(m_votes.values())} |",
        f"| Teor (parágrafo + entidade) | {t_votes['5']} | {t_votes['4']} | {t_votes['3']} | {sum(t_votes.values())} |", "",
        "Na menção, a coluna conta quem marcou exatamente o mesmo trecho com a mesma entidade; o tipo segue a maioria de quem marcou. No teor, conta quem deu o rótulo escolhido. Ausência de rótulo não conta como neutro.", "",
        "## Pendências para Bea", "",
        "| Tipo | Quantidade |", "|---|---:|",
        *[f"| {kind} | {n} |" for kind, n in counts["pendencias_por_tipo"].items()], "",
        *[f"- {p['id']} ({p['tipo']}), {p['paragraph_id']}: " + "; ".join(_option_lines(p, name)) for p in report["pendencias"]], "",
        "## Descartes (sem maioria)", "",
        f"Menções: {counts['mencoes_descartadas']}. Pares de teor com menos de 3 rótulos: {counts['teor_descartado']}.", "",
        *[f"- {mention(d)}; votos: {', '.join(d['votantes'])} ({d['motivo']})" for d in report["descartes"]["mencoes"]],
        *[f"- teor {d['paragraph_id']} / {name(d['entity_id'])}: " + ", ".join(f"{v}={label}" for v, label in d["rotulos"].items()) + " (sem maioria, descartado)"
          for d in report["descartes"]["teor"]], "",
        "## Exclusões antes da votação", "",
        f"Referências genéricas de partido (D15): {len(d15)}. Trechos de parágrafo inteiro, que não contam como voto: {len(whole)}.", "",
        *[f"- D15, {i['votante']}: {mention(i)}" for i in d15],
        *[f"- Parágrafo inteiro, {i['votante']}: {i['paragraph_id']} -> {name(i['entity_id'])}" for i in whole], "",
        "## Duplicatas", "",
        "Menção repetida pelo mesmo votante conta um voto. Se as repetições tiverem tipos diferentes, o voto de tipo desse votante não conta. Teor duplicado de um votante exclui a unidade inteira desse votante, como em `agreement.py`.", "",
        *[f"- Menção repetida, {i['votante']}: {mention(i)}" for i in report["duplicatas"]["mencoes_repetidas"]],
        *[f"- Tipos conflitantes, {i['votante']}: {mention(i)} ({', '.join(i['types'])})" for i in report["duplicatas"]["tipos_conflitantes"]],
        *[f"- Teor duplicado excluído, {voter}: {item['paragraph_id']} / {name(item['entity_id'])}, linhas {item['rows']}"
          for voter, data in report["coverage"].items() for item in data["duplicate_teor_units_excluded"]], "",
        "## Alertas de inconsistência (sem resolução automática)", "",
        "O protocolo exige linha de teor para toda entidade com menção no parágrafo. Teor sem menção pode ser legítimo (sujeito oculto), por isso também é só alerta. Pendências abertas podem gerar alertas que somem depois de `aplicar`.", "",
        f"- Menção sem teor: {len(alerts['mencao_sem_teor'])}.",
        *[f"  - {a['paragraph_id']} / {name(a['entity_id'])}" for a in alerts["mencao_sem_teor"]],
        f"- Teor sem menção: {len(alerts['teor_sem_mencao'])}.",
        *[f"  - {a['paragraph_id']} / {name(a['entity_id'])} ({a['teor']})" + (", com referência genérica D15 excluída no parágrafo" if a["referencia_generica_d15_no_paragrafo"] else "")
          for a in alerts["teor_sem_mencao"]],
        f"- Menções aceitas sobrepostas: {len(alerts['mencoes_sobrepostas'])}.",
        *[f"  - {a['paragraph_id']}: " + " x ".join(f"\"{t['text']}\" -> {name(t['entity_id'])}" for t in a["trechos"]) for a in alerts["mencoes_sobrepostas"]], "",
        "## Linhas com erro do validador", "",
        "Linhas com erro técnico ficam fora, como em `gold.py validar`. Motivos e valores originais estão em `report.json` (`coverage`).", "",
        "| Votante | Menções válidas | Pares de teor válidos | Linhas com erro em menções / teor |", "|---|---:|---:|---:|",
        *[f"| {voter} | {data['mentions']} | {data['teor_pairs']} | {len(data['excluded_rows']['mencoes'])} / {len(data['excluded_rows']['teor'])} |"
          for voter, data in report["coverage"].items()], "",
        "## Pontos em aberto para Bea", "", *[f"- {item}" for item in report["em_aberto"]], "",
        "## Limitações", "", *[f"- {item}" for item in report["limitations"]], "",
        "## Procedência", "",
        "Entradas lidas sem gravação, com SHA-256 conferido antes e depois.", "",
        "| Entrada | Caminho | SHA-256 |", "|---|---|---|",
        *[f"| {key} | `{value['path']}` | `{value['sha256']}` |" for key, value in report["inputs"].items()],
        *[f"| saída | `{key}` | `{value['sha256']}` |" for key, value in report["outputs"].items()], "",
        "```sh", ".venv-experiments/bin/python experiments/consolidate.py consolidar", "```", "",
    ]
    return "\n".join(lines)


def _jsonl(records: list[dict]) -> str:
    return "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _refuse_existing(paths) -> None:
    existing = [str(path) for path in paths if Path(path).exists()]
    if existing:
        raise ValueError(f"saída já existe; escolha outra pasta: {', '.join(existing)}")


def _write_new(path: Path, text: str) -> None:
    # newline="": os bytes gravados são os mesmos do hash registrado.
    with open(path, "x", encoding="utf-8", newline="") as handle:
        handle.write(text)


def write_consolidation(report: dict, records: list[dict], output_dir: Path) -> dict[str, Path]:
    """Grava os quatro arquivos; recusa se qualquer um já existir."""
    output_dir = Path(output_dir)
    targets = {name: output_dir / name for name in CONSOLIDATE_OUTPUTS}
    _refuse_existing(targets.values())
    reference = _jsonl(records)
    report = {**report, "outputs": {"referencia-provisoria.jsonl": {"sha256": _sha256_text(reference)}}}
    # Serializa tudo antes de abrir as saídas para não deixar arquivo parcial.
    workbook = build_pendencias_workbook(report["pendencias"], {_pid(r): r["text"] for r in records}, report["entities"])
    markdown = render_markdown(report)
    payload = json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n"
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_new(targets["referencia-provisoria.jsonl"], reference)
    with open(targets["pendencias.xlsx"], "xb") as handle:
        workbook.save(handle)
    _write_new(targets["report.md"], markdown)
    _write_new(targets["report.json"], payload)
    return targets


def cmd_consolidar(args: argparse.Namespace) -> int:
    report, records = build_report(csv_path=args.csv, entities_path=args.entidades, ids_path=args.ids)
    targets = write_consolidation(report, records, args.saida)
    counts = report["contagens"]
    print(json.dumps({
        "saida": agreement._path(Path(args.saida)), "inputs_unchanged": report["inputs_unchanged"],
        "mencoes_aceitas_por_votos": counts["mencoes_aceitas_por_votos"],
        "teor_aceito_por_votos": counts["teor_aceito_por_votos"],
        "pendencias_por_tipo": counts["pendencias_por_tipo"],
        "arquivos": [path.name for path in targets.values()],
    }, ensure_ascii=False, indent=2))
    return 0


# --------------------------------------------------------------------------
# aplicar
# --------------------------------------------------------------------------


def parse_decision(pending: dict, raw: str):
    """Valida a decisão de uma linha. Teor: rótulo ou FORA. Menção: lista de
    números de opção ([] para FORA). Levanta ValueError com o motivo."""
    value = raw.strip().lower()
    if not value:
        raise ValueError("decisão vazia")
    valid = ", ".join(pending["decisoes_validas"])
    if pending["tipo"] == "teor_empate":
        if value not in (*gold.TEORES, FORA):
            raise ValueError(f"decisão inválida {raw!r}; use uma de: {valid}")
        return value
    if value == FORA:
        if pending["tipo"] == "mencao_tipo":
            raise ValueError(f"decisão inválida {raw!r}; pendência de tipo exige uma opção: {valid}")
        return []
    parts = [part for part in re.split(r"[,;\s]+", value) if part]
    if not parts or any(not re.fullmatch(r"[0-9]+", part) for part in parts):
        raise ValueError(f"decisão inválida {raw!r}; use uma de: {valid} (várias opções separadas por ponto e vírgula)")
    numbers = sorted({int(part) for part in parts})
    options = {o["n"]: o for o in pending["opcoes"]}
    unknown = [n for n in numbers if n not in options]
    if unknown:
        raise ValueError(f"decisão inválida {raw!r}; opção inexistente {unknown}; use uma de: {valid}")
    if pending["tipo"] == "mencao_tipo" and len(numbers) != 1:
        raise ValueError(f"decisão inválida {raw!r}; pendência de tipo aceita uma única opção")
    spans = [(options[n]["start"], options[n]["end"], options[n]["entity_id"]) for n in numbers]
    if len(set(spans)) != len(spans):
        raise ValueError(f"decisão inválida {raw!r}; duas opções do mesmo trecho e entidade com tipos diferentes")
    return numbers


def read_decisions(path: Path, pendencias: list[dict]) -> dict[str, dict]:
    """Lê pendencias.xlsx preenchida. Junta todos os problemas, com o número
    da linha, num único ValueError."""
    by_id = {item["id"]: item for item in pendencias}
    wb = load_workbook(path, data_only=True)
    try:
        if "pendencias" not in wb.sheetnames:
            raise ValueError(f"{path}: aba 'pendencias' ausente")
        headers = [gold._cell_text(cell.value) for cell in wb["pendencias"][1]]
        required = {"id", "tipo", "paragraph_id", "decisao", "observacao"}
        if not required.issubset(headers):
            raise ValueError(f"{path}: colunas ausentes: {sorted(required - set(headers))}")
        errors, seen, decisions = [], set(), {}
        for row, values in gold._sheet_rows(wb, "pendencias", len(headers)):
            item = dict(zip(headers, values))
            pid = gold._cell_text(item["id"])
            if pid not in by_id:
                errors.append(f"linha {row}: id desconhecido {pid!r}")
                continue
            if pid in seen:
                errors.append(f"linha {row} ({pid}): id repetido")
                continue
            seen.add(pid)
            pending = by_id[pid]
            if gold._cell_text(item["tipo"]) != pending["tipo"] or gold._cell_text(item["paragraph_id"]) != pending["paragraph_id"]:
                errors.append(f"linha {row} ({pid}): tipo ou paragraph_id não confere com report.json")
                continue
            raw = gold._cell_text(item["decisao"])
            try:
                choice = parse_decision(pending, raw)
            except ValueError as exc:
                errors.append(f"linha {row} ({pid}): {exc}")
                continue
            decisions[pid] = {"decisao": raw, "escolha": choice, "observacao": gold._cell_text(item["observacao"]), "linha": row}
        errors += [f"pendência {pid} ausente da planilha" for pid in by_id if pid not in seen]
        if errors:
            raise ValueError("pendencias.xlsx com problemas:\n" + "\n".join(errors))
        return decisions
    finally:
        wb.close()


def apply_decisions(provisional: list[dict], pendencias: list[dict], decisions: dict[str, dict]) -> tuple[list[dict], list[dict]]:
    """Acrescenta à referência provisória o que Bea escolheu. Devolve
    (registros finais, registro das decisões). Não altera `provisional`."""
    records = [{**r, "mentions": list(r["mentions"]), "teor": dict(r["teor"]), "annotator": "referencia"} for r in provisional]
    by_pid = {_pid(r): r for r in records}
    log = []
    for pending in pendencias:
        decision = decisions[pending["id"]]
        record = by_pid.get(pending["paragraph_id"])
        if record is None:
            raise ValueError(f"{pending['id']}: parágrafo {pending['paragraph_id']} ausente da referência provisória")
        applied = []
        if pending["tipo"] == "teor_empate":
            if decision["escolha"] != FORA:
                if pending["entity_id"] in record["teor"]:
                    raise ValueError(f"{pending['id']}: teor de {pending['entity_id']} já está na referência provisória")
                record["teor"][pending["entity_id"]] = decision["escolha"]
                applied.append({"entity_id": pending["entity_id"], "teor": decision["escolha"]})
        else:
            for option in pending["opcoes"]:
                if option["n"] not in decision["escolha"]:
                    continue
                if record["text"][option["start"]:option["end"]] != option["text"]:
                    raise ValueError(f"{pending['id']}: trecho da opção {option['n']} não confere com o parágrafo")
                key = (option["start"], option["end"], option["entity_id"])
                if any((m["start"], m["end"], str(m["entity_id"])) == key for m in record["mentions"]):
                    raise ValueError(f"{pending['id']}: opção {option['n']} já está na referência provisória")
                mention = {k: option[k] for k in ("start", "end", "text", "type", "entity_id")}
                record["mentions"].append(mention)
                applied.append(mention)
        log.append({"id": pending["id"], "tipo": pending["tipo"], "paragraph_id": pending["paragraph_id"],
                    "linha_planilha": decision["linha"], "decisao": decision["decisao"],
                    "observacao": decision["observacao"], "aplicado": applied})
    for record in records:
        record["mentions"].sort(key=lambda m: (m["start"], m["end"], m["entity_id"]))
        record["teor"] = dict(sorted(record["teor"].items()))
    return records, log


def remove_teor(records: list[dict], pairs: list[str], motivo: str | None) -> list[dict]:
    """Remove de `records` (no lugar) os pares de teor PARAGRAPH_ID:ENTITY_ID
    que Bea decidiu tirar da referência. Menções não são tocadas. Devolve o
    registro das remoções."""
    if not pairs:
        return []
    if not (motivo or "").strip():
        raise ValueError("--motivo-remocao é obrigatório quando há --remover-teor")
    by_pid = {_pid(r): r for r in records}
    log = []
    for pair in pairs:
        pid, sep, eid = pair.partition(":")
        if not sep or not pid or not eid:
            raise ValueError(f"--remover-teor {pair!r}: use PARAGRAPH_ID:ENTITY_ID")
        record = by_pid.get(pid)
        if record is None:
            raise ValueError(f"--remover-teor {pair!r}: parágrafo {pid} ausente da referência")
        if eid not in record["teor"]:
            raise ValueError(f"--remover-teor {pair!r}: entidade {eid} sem teor no parágrafo {pid}")
        log.append({"paragraph_id": pid, "entity_id": eid, "teor": record["teor"].pop(eid), "motivo": motivo.strip()})
    return log


def cmd_aplicar(args: argparse.Namespace) -> int:
    consolidation = Path(args.consolidacao)
    output_dir = Path(args.saida)
    targets = {name: output_dir / name for name in APPLY_OUTPUTS}
    _refuse_existing(targets.values())
    paths = {
        "report": consolidation / "report.json",
        "referencia_provisoria": consolidation / "referencia-provisoria.jsonl",
        "pendencias": Path(args.pendencias) if args.pendencias else consolidation / "pendencias.xlsx",
    }
    before = {name: agreement._sha256(path) for name, path in paths.items()}
    report = json.loads(paths["report"].read_text(encoding="utf-8"))
    if before["referencia_provisoria"] != report["outputs"]["referencia-provisoria.jsonl"]["sha256"]:
        raise ValueError("referencia-provisoria.jsonl não confere com o hash registrado em report.json")
    provisional = [json.loads(line) for line in paths["referencia_provisoria"].read_text(encoding="utf-8").splitlines() if line.strip()]
    decisions = read_decisions(paths["pendencias"], report["pendencias"])
    records, log = apply_decisions(provisional, report["pendencias"], decisions)
    # Depois dos desempates e antes dos alertas, que refletem a referência final.
    removals = remove_teor(records, args.remover_teor, args.motivo_remocao)
    alerts =inconsistency_alerts(records, report["exclusoes"]["d15_partido_generico"])
    after = {name: agreement._sha256(path) for name, path in paths.items()}
    if after != before:
        raise RuntimeError("entrada alterada durante a aplicação")
    reference = _jsonl(records)
    payload = {
        "schema_version": 1, "purpose": "desempates de Bea sobre a referência provisória do piloto (D17)",
        "inputs": {name: {"path": agreement._path(path), "sha256": before[name]} for name, path in paths.items()},
        "inputs_unchanged": True,
        "consolidate_code_sha256": agreement._sha256(Path(__file__)),
        "decisoes": log,
        "remocoes_teor": removals,
        "contagens": {
            "decisoes": len(log),
            "por_tipo": {kind: sum(item["tipo"] == kind for item in log) for kind in PENDING_KINDS},
            "fora": sum(not item["aplicado"] for item in log),
            "remocoes_teor": len(removals),
            "mencoes": sum(len(r["mentions"]) for r in records),
            "pares_de_teor": sum(len(r["teor"]) for r in records),
        },
        "alertas": alerts,
        "outputs": {"referencia.jsonl": {"sha256": _sha256_text(reference)}},
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n"
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_new(targets["referencia.jsonl"], reference)
    _write_new(targets["decisoes-desempate.json"], text)
    print(json.dumps({"saida": agreement._path(output_dir), **payload["contagens"],
                      "alertas": {key: len(value) for key, value in alerts.items()}}, ensure_ascii=False, indent=2))
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("consolidar", help="gera a referência provisória, as pendências e o relatório")
    p.add_argument("--saida", type=Path, default=DEFAULT_OUTPUT, help="pasta de saída; arquivos existentes não são sobrescritos")
    p.add_argument("--csv", type=Path, default=gold.RAW_CSV, help="CSV bruto de artigos")
    p.add_argument("--entidades", type=Path, default=gold.DEFAULT_ENTITIES, help="snapshot de entidades usado no piloto")
    p.add_argument("--ids", type=Path, default=PILOT_IDS, help="IDs das notícias do piloto")
    p.set_defaults(func=cmd_consolidar)

    p = sub.add_parser("aplicar", help="aplica as decisões de pendencias.xlsx e gera a referência final")
    p.add_argument("--consolidacao", type=Path, default=DEFAULT_OUTPUT, help="pasta gerada por consolidar")
    p.add_argument("--pendencias", type=Path, help="pendencias.xlsx preenchida (padrão: dentro de --consolidacao)")
    p.add_argument("--saida", required=True, type=Path, help="pasta para referencia.jsonl e decisoes-desempate.json")
    p.add_argument("--remover-teor", action="append", default=[], metavar="PARAGRAPH_ID:ENTITY_ID",
                   help="remove o par de teor da referência final por decisão de Bea (repetível)")
    p.add_argument("--motivo-remocao", help="motivo das remoções, registrado em decisoes-desempate.json (obrigatório com --remover-teor)")
    p.set_defaults(func=cmd_aplicar)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, OSError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
