"""Concordância descritiva do piloto, sem alterar ou adjudicar as fontes.

Executar da raiz: .venv/bin/python experiments/agreement.py --help.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

from openpyxl import load_workbook

try:
    from . import gold, metrics
except ImportError:
    import gold
    import metrics

BASE_DIR = Path(__file__).resolve().parent.parent
BACKUPS = BASE_DIR / "experiments/data/anotacao/backups"
SOURCE_FILES = {
    "Anderson": BACKUPS / "20261102T183539Z/Anderson - Planilha.xlsx",
    "Beatriz": BACKUPS / "20261102T180337Z/beatriz.xlsx",
    "Cristovam": BACKUPS / "20261102T180337Z/cristovam (1).xlsx",
    "Gustavo": BACKUPS / "20261102T180337Z/gustavo - Planilha.xlsx",
    "Lucas": BACKUPS / "20261102T180337Z/Lucas - Planilha.xlsx",
    "Nicolas": BACKUPS / "20261102T180337Z/nicolas.xlsx",
}
LABELS = (*metrics.CLASSES, "indeterminado")
LIMITATIONS = [
    "Cinco fontes precedem as intervenções automáticas. A cópia disponível de Anderson já havia sido editada manualmente; sua independência não pode ser comprovada.",
    "Beatriz anotou também trechos de parágrafo inteiro, incompatíveis com os limites de menção do protocolo. Esses trechos foram preservados e afetam especialmente o F1 exato.",
    "A análise principal usa os cinco originais preservados. A análise adicional inclui Anderson, com independência não comprovada. Nenhuma análise constitui gabarito consensual.",
    "As novas regras D10 a D12 não foram aplicadas às respostas. Em particular, nenhuma atribuição de 145-6 foi corrigida ou adjudicada.",
    "Ausência de teor não é neutro. Kappa usa quatro categorias, incluindo indeterminado, apenas em unidades com todos os anotadores presentes. F1 de teor dos sistemas usa três classes em metrics.py.",
    "O bootstrap reamostra notícias inteiras. Os cinco artigos do piloto limitam a interpretação dos intervalos; eles não corrigem a procedência ou as exclusões.",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(BASE_DIR))
    except ValueError:
        return str(path.resolve())


def compute_teor_agreement(annotators: dict[str, list[dict]]) -> dict:
    """Fleiss em unidades completas; as demais ficam listadas por chave."""
    if len(annotators) < 2:
        raise ValueError("concordância exige pelo menos dois anotadores")
    values = {name: metrics._teores(records) for name, records in annotators.items()}
    keys = sorted(set().union(*(set(items) for items in values.values())))
    counts, excluded, units = [], [], []
    for key in keys:
        labels = {name: items.get(key) for name, items in values.items()}
        missing = [name for name, label in labels.items() if label is None]
        unit = {"article_id": key[0], "paragraph_index": key[1], "entity_id": key[2], "labels": labels}
        if missing:
            excluded.append({**unit, "missing_annotators": missing})
            continue
        counts.append([list(labels.values()).count(label) for label in LABELS])
        units.append(unit)
    return {
        "labels": list(LABELS), "n_annotators": len(annotators),
        "union_units": len(keys), "included_units": len(counts),
        "excluded_units": len(excluded), "kappa": metrics.fleiss_kappa(counts),
        "counts": counts, "units": units, "excluded": excluded,
        "missing_by_annotator": {name: sum(name in u["missing_annotators"] for u in excluded) for name in annotators},
    }


def pairwise_mentions(annotators: dict[str, list[dict]], *, n_resamples: int = 1000, seed: int = 42) -> list[dict]:
    """F1 simétrico para cada par; ligação condicional tem direção explícita."""
    pairs = []
    for a, b in combinations(sorted(annotators), 2):
        truth, predicted = annotators[a], annotators[b]
        scores = {mode: metrics.mention_scores(truth, predicted, mode=mode) for mode in ("exact", "partial")}
        intervals = {}
        for mode, field in (("exact", "overall"), ("partial", "overall"), ("exact", "joint"), ("partial", "joint")):
            intervals[f"{mode}_{field}"] = metrics.bootstrap_by_article(
                truth, predicted,
                lambda g, p, mode=mode, field=field: metrics.mention_scores(g, p, mode=mode)[field]["f1"],
                n_resamples=n_resamples, seed=seed,
            )
        pairs.append({"reference": a, "predicted": b, **scores, "bootstrap": intervals})
    return pairs


def _read_source(path: Path, name: str, articles: dict, entities: list[dict]) -> tuple[list[dict], dict]:
    wb = load_workbook(path, data_only=False)
    try:
        # Os cabeçalhos identificam as posições originais da planilha de Bea.
        headers = [gold._cell_text(cell.value) for cell in wb["paragrafos"][1]]
        if len(set(h for h in headers if h)) != len([h for h in headers if h]):
            raise ValueError(f"cabeçalhos duplicados em {name}")
        required = {"paragraph_id", "article_id", "paragraph_index", "texto"}
        if not required.issubset(headers):
            raise ValueError(f"cabeçalhos de parágrafos ausentes em {name}: {required - set(headers)}")
        canonical = {f"{aid}-{i}": text for aid, item in articles.items() for i, text in enumerate(item["paragraphs"])}
        source_paragraphs = {}
        for row in wb["paragrafos"].iter_rows(min_row=2, values_only=True):
            pid = gold._cell_text(row[headers.index("paragraph_id")])
            if not pid:
                continue
            if pid in source_paragraphs:
                raise ValueError(f"parágrafo duplicado na fonte {name}: {pid}")
            source_paragraphs[pid] = row[headers.index("texto")]
        if source_paragraphs != canonical:
            raise ValueError(f"parágrafos da fonte {name} diferem do CSV segmentado; comparação interrompida")
        records, issues = gold.validate_workbook(wb, name, articles, entities)
        # Uma duplicata de teor não estabelece qual resposta vale: excluir a
        # unidade, em vez de aceitar a primeira linha por ordem da planilha.
        names = {e["nome_principal"]: str(e["entity_id"]) for e in entities}
        seen, conflicts = {}, []
        for row, values in gold._sheet_rows(wb, "teor", 4):
            pid, candidate, label = map(gold._cell_text, values[:3])
            if pid not in canonical or candidate not in names or label not in LABELS:
                continue
            key = (pid, names[candidate])
            if key in seen:
                conflicts.append({"paragraph_id": pid, "entity_id": names[candidate], "rows": [seen[key], row]})
            else:
                seen[key] = row
        blocked = {(item["paragraph_id"], item["entity_id"]) for item in conflicts}
        for record in records:
            pid = f"{record['article_id']}-{record['paragraph_index']}"
            record["teor"] = {eid: label for eid, label in record["teor"].items() if (pid, str(eid)) not in blocked}
        raw = {}
        exclusions = {}
        for sheet, columns in (("mencoes", 6), ("teor", 4)):
            rows = list(gold._sheet_rows(wb, sheet, columns))
            error_rows = {i["linha"] for i in issues if i["aba"] == sheet and i["nivel"] == "erro" and i["linha"] is not None}
            raw[sheet] = len(rows)
            exclusions[sheet] = [{"row": row, "values": list(values), "reasons": [i["motivo"] for i in issues if i["aba"] == sheet and i["linha"] == row and i["nivel"] == "erro"]} for row, values in rows if row in error_rows]
        return records, {
            "paragraph_headers": headers, "paragraphs": len(records), "source_nonempty_rows": raw,
            "mentions": sum(len(r["mentions"]) for r in records),
            "teor_pairs": sum(len(r["teor"]) for r in records),
            "whole_paragraph_mentions": sum(m["start"] == 0 and m["end"] == len(r["text"]) for r in records for m in r["mentions"]),
            "issue_counts": dict(Counter(i["nivel"] for i in issues)), "issues": issues,
            "excluded_rows": exclusions, "duplicate_teor_units_excluded": conflicts,
        }
    finally:
        wb.close()


def build_report(*, csv_path: Path = gold.RAW_CSV, entities_path: Path = gold.DEFAULT_ENTITIES,
                 ids_path: Path = BASE_DIR / "experiments/data/piloto_ids.txt",
                 n_resamples: int = 1000, seed: int = 42) -> dict:
    paths = {**SOURCE_FILES, "raw_csv": csv_path, "entities": entities_path, "pilot_ids": ids_path,
             "gold_code": Path(gold.__file__), "metrics_code": Path(metrics.__file__), "agreement_code": Path(__file__)}
    before = {name: _sha256(path) for name, path in paths.items()}
    articles = gold.load_articles(csv_path, gold.read_id_list(ids_path))
    entities = gold.load_entities(entities_path)
    annotators, coverage = {}, {}
    for name, path in SOURCE_FILES.items():
        annotators[name], coverage[name] = _read_source(path, name, articles, entities)
    all_pairs = pairwise_mentions(annotators, n_resamples=n_resamples, seed=seed)
    pairs = [pair for pair in all_pairs if "Anderson" not in (pair["reference"], pair["predicted"])]
    originals = {name: records for name, records in annotators.items() if name != "Anderson"}
    after = {name: _sha256(path) for name, path in paths.items()}
    if after != before:
        raise RuntimeError("entrada alterada durante a análise")
    return {
        "schema_version": 1, "purpose": "concordância descritiva do piloto disponível",
        "inputs": {name: {"path": _path(path), "sha256": before[name]} for name, path in paths.items()},
        "inputs_unchanged": True, "settings": {"n_resamples": n_resamples, "seed": seed, "confidence": .95},
        "article_ids": list(articles), "coverage": coverage, "pairs": pairs,
        "mean_pairwise_f1": {f"{mode}_{field}": sum(p[mode][field]["f1"] for p in pairs) / len(pairs) for mode in ("exact", "partial") for field in ("overall", "joint")},
        "teor": compute_teor_agreement(originals),
        "additional_six_annotators": {
            "independence_proven": False, "pairs": all_pairs,
            "mean_pairwise_f1": {f"{mode}_{field}": sum(p[mode][field]["f1"] for p in all_pairs) / len(all_pairs) for mode in ("exact", "partial") for field in ("overall", "joint")},
            "teor": compute_teor_agreement(annotators),
        }, "limitations": LIMITATIONS,
    }


def write_report(report: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Concordância descritiva do piloto", "", *[f"- {item}" for item in report["limitations"]], "",
             f"Notícias: {', '.join(report['article_ids'])}. Bootstrap: {report['settings']['n_resamples']} reamostragens por notícia; semente {report['settings']['seed']}; IC de 95%.", "",
             "| Par (referência / previsão) | F1 exato | IC 95% | F1 parcial | IC 95% | F1 conjunto exato | F1 conjunto parcial |",
             "|---|---:|---|---:|---|---:|---:|"]
    for pair in report["pairs"]:
        intervals = pair["bootstrap"]
        ci = lambda key: f"[{intervals[key]['lower']:.4f}; {intervals[key]['upper']:.4f}]"
        lines.append(f"| {pair['reference']} / {pair['predicted']} | {pair['exact']['overall']['f1']:.4f} | {ci('exact_overall')} | {pair['partial']['overall']['f1']:.4f} | {ci('partial_overall')} | {pair['exact']['joint']['f1']:.4f} | {pair['partial']['joint']['f1']:.4f} |")
    lines += ["", "Médias dos 10 pares dos cinco originais: " + "; ".join(f"{key} = {value:.4f}" for key, value in report["mean_pairwise_f1"].items()) + ".", "",
              "O F1 conjunto exige trecho e entidade corretos. A ligação condicional e os resultados por tipo estão no JSON; a direção da referência é explícita. O JSON inclui também IC dos F1 conjuntos.", "",
              "## Cobertura e exclusões", "", "| Anotador | Menções válidas | Trechos de parágrafo inteiro | Pares de teor válidos | Linhas com erro em menções / teor |", "|---|---:|---:|---:|---:|"]
    for name, data in report["coverage"].items():
        lines.append(f"| {name} | {data['mentions']} | {data['whole_paragraph_mentions']} | {data['teor_pairs']} | {len(data['excluded_rows']['mencoes'])} / {len(data['excluded_rows']['teor'])} |")
    teor = report["teor"]
    lines += ["", f"Fleiss principal (cinco originais, quatro categorias): {teor['kappa']}. Foram incluídas {teor['included_units']} de {teor['union_units']} unidades na união; {teor['excluded_units']} ficaram fora por ausência de pelo menos um rótulo válido. As contagens por unidade e os anotadores ausentes estão no JSON.", "",
              "Linhas não vazias com erro técnico são excluídas pelo validador. Isso inclui linhas apenas com observações ou identificador, sem anotação completa; as contagens não representam necessariamente anotações tentadas. Unidades de teor duplicadas são excluídas por inteiro, sem escolher a primeira resposta. Avisos de normalização preservam os offsets localizados no texto original.", ""]
    for name, data in report["coverage"].items():
        for sheet, rows in data["excluded_rows"].items():
            if rows:
                lines.append(f"- {name}, {sheet}: linhas " + ", ".join(str(row["row"]) for row in rows) + ".")
        for item in data["duplicate_teor_units_excluded"]:
            lines.append(f"- {name}, teor duplicado excluído: {item['paragraph_id']} / {item['entity_id']}, linhas {item['rows']}.")
    extra = report["additional_six_annotators"]
    lines += ["", "## Análise adicional com Anderson", "", "A independência da planilha de Anderson não foi comprovada. A tabela reúne os 15 pares para descrever a versão disponível, sem interpretar os seis como respostas independentes.", "",
              "| Par | F1 exato | F1 parcial | F1 conjunto exato | F1 conjunto parcial |", "|---|---:|---:|---:|---:|"]
    for pair in extra["pairs"]:
        lines.append(f"| {pair['reference']} / {pair['predicted']} | {pair['exact']['overall']['f1']:.4f} | {pair['partial']['overall']['f1']:.4f} | {pair['exact']['joint']['f1']:.4f} | {pair['partial']['joint']['f1']:.4f} |")
    t = extra["teor"]
    lines += ["", f"Fleiss adicional: {t['kappa']}; {t['included_units']} unidades completas de {t['union_units']} na união; {t['excluded_units']} excluídas. Os IC por par estão no JSON.", "",
              "## Reprodução e procedência", "", "```sh", ".venv/bin/python experiments/agreement.py", "```", "",
              "Os arquivos de entrada foram lidos sem gravação, com SHA-256 conferido antes e depois. Caminhos, hashes de dados e código, configuração efetiva, exclusões com motivos e valores originais estão em `report.json`. O CSV fornece os textos segmentados; a ordem das colunas de Beatriz foi identificada pelos cabeçalhos.", ""]
    (output_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=gold.RAW_CSV)
    parser.add_argument("--entities", type=Path, default=gold.DEFAULT_ENTITIES)
    parser.add_argument("--ids", type=Path, default=BASE_DIR / "experiments/data/piloto_ids.txt")
    parser.add_argument("--output", type=Path, default=BASE_DIR / "experiments/results/piloto-concordancia")
    parser.add_argument("--resamples", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)
    report = build_report(csv_path=args.csv, entities_path=args.entities, ids_path=args.ids, n_resamples=args.resamples, seed=args.seed)
    write_report(report, args.output)
    print(json.dumps({"output": _path(args.output), "pairs": len(report["pairs"]), "kappa": report["teor"]["kappa"], "included_units": report["teor"]["included_units"], "inputs_unchanged": report["inputs_unchanged"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
