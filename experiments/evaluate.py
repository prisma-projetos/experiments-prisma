"""Avaliação das regras sem treino contra a referência do piloto (D17).

Sistemas: matcher de produção e heurística de menção mais recente
(``mentions.predict_mentions``, D15: sem descrições de partido), léxico de
produção nos pares da referência (teor isolado) e as duas combinações fim a
fim. Toda métrica sai de ``metrics.py``; este módulo só orquestra, mede tempo
e lista erros, sem interpretá-los. Entradas e código são conferidos por
SHA-256 antes e depois; nenhum arquivo de saída existente é sobrescrito.

Executar da raiz: .venv-experiments/bin/python experiments/evaluate.py --help
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

try:
    from . import agreement, consolidate, gold, mentions, metrics, teor
except ImportError:
    import agreement
    import consolidate
    import gold
    import mentions
    import metrics
    import teor

BASE_DIR = agreement.BASE_DIR
DEFAULT_REFERENCE = BASE_DIR / "experiments/results/piloto-referencia-final/referencia.jsonl"
DEFAULT_LEXICON = BASE_DIR / "config/lexicon.yaml"
DEFAULT_OUTPUT = BASE_DIR / "experiments/results/piloto-avaliacao"
MENTION_SYSTEMS = ("matcher", "recency")
MODES = ("exact", "partial")
PREDICTION_FILES = {
    "lexico_pares_referencia": "predicoes-lexico-pares-referencia.jsonl",
    "matcher_lexico": "predicoes-matcher-lexico.jsonl",
    "recency_lexico": "predicoes-recency-lexico.jsonl",
}
OUTPUTS = ("report.md", "report.json", *PREDICTION_FILES.values())
SNIPPET = 160
LIMITATIONS = [
    "A referência tem só 5 notícias (92 parágrafos). O bootstrap reamostra notícias inteiras; com 5 unidades os intervalos são grosseiros e não permitem generalização.",
    "Há um único par de teor positivo na referência: F1 positivo e F1 macro são instáveis e dependem de um acerto ou erro.",
    "A referência vem de voto da maioria sobre planilhas revisadas, não de gabarito adjudicado (D17). As regras D10 a D12 foram formuladas olhando o piloto, o que tende a favorecer a heurística de menção mais recente.",
    "O matcher de produção só prevê menções diretas; seus resultados de IND são zero por construção.",
    "O tempo foi medido nesta máquina, não na VPS de produção; serve para comparar os sistemas entre si, não para estimar custo absoluto em produção.",
]


def load_reference(path: Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _inputs_for_prediction(reference: list[dict]) -> list[dict]:
    # A predição de menções só recebe texto e posição, nunca os rótulos.
    return [{"article_id": r["article_id"], "paragraph_index": r["paragraph_index"], "text": r["text"]} for r in reference]


def run_systems(reference: list[dict], entities: list, lexicon_path: Path) -> dict[str, list[dict]]:
    """Predições de cada sistema; as fim a fim também carregam as menções."""
    predictions = {}
    for system in MENTION_SYSTEMS:
        found = mentions.predict_mentions(_inputs_for_prediction(reference), entities,
                                          system=system, include_party_descriptions=False)
        predictions[f"{system}_lexico"] = teor.predict_lexicon(found, pairs="mentions", lexicon_path=lexicon_path)
    predictions["lexico_pares_referencia"] = teor.predict_lexicon(reference, pairs="gold", lexicon_path=lexicon_path)
    return predictions


def _f1(field: str, mode: str, kind: str | None = None):
    def score(g, p):
        result = metrics.mention_scores(g, p, mode=mode)
        return (result["by_type"][kind] if kind else result[field])["f1"]
    return score


def evaluate(reference: list[dict], predictions: dict[str, list[dict]], *, n_resamples: int = 1000, seed: int = 42) -> dict:
    mention_results = {}
    for system in MENTION_SYSTEMS:
        predicted = predictions[f"{system}_lexico"]
        mention_results[system] = {}
        for mode in MODES:
            mention_results[system][mode] = {
                "scores": metrics.mention_scores(reference, predicted, mode=mode),
                "bootstrap": {
                    "overall_f1": metrics.bootstrap_by_article(reference, predicted, _f1("overall", mode),
                                                               n_resamples=n_resamples, seed=seed),
                    "ind_f1": metrics.bootstrap_by_article(reference, predicted, _f1("by_type", mode, "IND"),
                                                           n_resamples=n_resamples, seed=seed),
                },
            }
    return {
        "mentions": mention_results,
        "teor_isolado": metrics.teor_scores(reference, predictions["lexico_pares_referencia"], end_to_end=False),
        "fim_a_fim": {system: metrics.teor_scores(reference, predictions[f"{system}_lexico"], end_to_end=True)
                      for system in MENTION_SYSTEMS},
    }


def measure_cost(reference: list[dict], entities: list, lexicon_path: Path, *, repeats: int = 7) -> dict:
    """Mediana de ``repeats`` execuções, normalizada para mil parágrafos.

    Carregar entidades fica fora do tempo; carregar o léxico fica dentro,
    porque predict_lexicon o lê a cada chamada.
    """
    if repeats < 1:
        raise ValueError("repeats deve ser pelo menos 1")
    inputs = _inputs_for_prediction(reference)

    def found(system):
        return mentions.predict_mentions(inputs, entities, system=system, include_party_descriptions=False)

    def lexicon(records, pairs):
        return teor.predict_lexicon(records, pairs=pairs, lexicon_path=lexicon_path)

    runs = {
        "matcher": lambda: found("matcher"),
        "recency": lambda: found("recency"),
        "lexico_pares_referencia": lambda: lexicon(reference, "gold"),
        "matcher_lexico": lambda: lexicon(found("matcher"), "mentions"),
        "recency_lexico": lambda: lexicon(found("recency"), "mentions"),
    }
    result = {}
    for name, run in runs.items():
        seconds = []
        for _ in range(repeats):
            start = time.perf_counter()
            run()
            seconds.append(time.perf_counter() - start)
        median = statistics.median(seconds)
        result[name] = {"seconds": seconds, "median_seconds": median,
                        "seconds_per_1000_paragraphs": median / len(reference) * 1000}
    return {"repeats": repeats, "paragraphs": len(reference), "systems": result, "machine": machine_info()}


def machine_info() -> dict:
    cpu = platform.processor()
    if sys.platform == "darwin":
        try:
            cpu = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True,
                                 text=True, check=True, timeout=5).stdout.strip() or cpu
        except (OSError, subprocess.SubprocessError):
            pass
    return {"platform": platform.platform(), "machine": platform.machine(), "cpu": cpu,
            "cpu_count": os.cpu_count(), "python": platform.python_version()}


def _pid(record: dict) -> str:
    return f"{record['article_id']}-{record['paragraph_index']}"


def _context(text: str, start: int, end: int, margin: int = 50) -> str:
    left, right = max(0, start - margin), min(len(text), end + margin)
    return ("…" if left else "") + text[left:right] + ("…" if right < len(text) else "")


def _short(text: str) -> str:
    return text if len(text) <= SNIPPET else text[:SNIPPET] + "…"


def error_analysis(reference: list[dict], predictions: dict[str, list[dict]]) -> dict:
    """Listagens para a discussão, sem interpretação.

    IND perdida: nenhuma menção prevista com interseção e mesma entidade
    (equivale ao joint parcial). FP do recency: menção prevista sem par no
    casamento de detecção exato, com a indicação se também é FP no parcial.
    """
    gold_by_key = {(r["article_id"], r["paragraph_index"]): r for r in reference}
    missed_ind = {}
    for system in MENTION_SYSTEMS:
        missed_ind[system] = []
        for predicted in predictions[f"{system}_lexico"]:
            truth = gold_by_key[(predicted["article_id"], predicted["paragraph_index"])]
            guess = predicted["mentions"]
            joint = {i for i, _ in metrics.match_mentions(truth["mentions"], guess, mode="partial", require_entity=True)}
            detected = dict(metrics.match_mentions(truth["mentions"], guess, mode="partial"))
            for i, mention in enumerate(truth["mentions"]):
                if mention["type"] != "IND" or i in joint:
                    continue
                overlap = guess[detected[i]] if i in detected else None
                missed_ind[system].append({
                    "paragraph_id": _pid(truth), "text": mention["text"], "start": mention["start"], "end": mention["end"],
                    "entity_id": str(mention["entity_id"]),
                    "predicted_overlap": None if overlap is None else {
                        "text": overlap["text"], "entity_id": str(overlap["entity_id"]), "type": overlap["type"]},
                    "context": _context(truth["text"], mention["start"], mention["end"]),
                })
    recency_fp = []
    for predicted in predictions["recency_lexico"]:
        truth = gold_by_key[(predicted["article_id"], predicted["paragraph_index"])]
        guess = predicted["mentions"]
        exact = {j for _, j in metrics.match_mentions(truth["mentions"], guess, mode="exact")}
        partial = {j for _, j in metrics.match_mentions(truth["mentions"], guess, mode="partial")}
        for j, mention in enumerate(guess):
            if j in exact:
                continue
            recency_fp.append({
                "paragraph_id": _pid(truth), "text": mention["text"], "start": mention["start"], "end": mention["end"],
                "type": mention["type"], "entity_id": str(mention["entity_id"]), "fp_partial": j not in partial,
                "context": _context(truth["text"], mention["start"], mention["end"]),
            })
    teor_errors = []
    for predicted in predictions["lexico_pares_referencia"]:
        truth = gold_by_key[(predicted["article_id"], predicted["paragraph_index"])]
        for entity_id, label in truth["teor"].items():
            guess = predicted["teor"].get(str(entity_id))
            if label != "indeterminado" and guess != label:
                teor_errors.append({"paragraph_id": _pid(truth), "entity_id": str(entity_id), "reference": label,
                                    "predicted": guess, "text": _short(truth["text"])})
    return {"ind_perdidas": missed_ind, "recency_fp_exato": recency_fp, "teor_isolado_erros": teor_errors}


def build_report(*, reference_path: Path = DEFAULT_REFERENCE, entities_path: Path = gold.DEFAULT_ENTITIES,
                 lexicon_path: Path = DEFAULT_LEXICON, n_resamples: int = 1000, seed: int = 42,
                 repeats: int = 7) -> tuple[dict, dict[str, list[dict]]]:
    src = BASE_DIR / "src"
    paths = {"referencia": Path(reference_path), "entities": Path(entities_path), "lexicon": Path(lexicon_path),
             "evaluate_code": Path(__file__), "metrics_code": Path(metrics.__file__),
             "mentions_code": Path(mentions.__file__), "teor_code": Path(teor.__file__),
             "consolidate_code": Path(consolidate.__file__), "agreement_code": Path(agreement.__file__),
             "entity_matcher_code": src / "entity_matcher.py", "entities_store_code": src / "entities_store.py",
             "lexicon_code": src / "lexicon.py"}
    before = {name: agreement._sha256(path) for name, path in paths.items()}
    reference = load_reference(reference_path)
    entities = mentions.load_entities_snapshot(entities_path)
    predictions = run_systems(reference, entities, lexicon_path)
    results = evaluate(reference, predictions, n_resamples=n_resamples, seed=seed)
    cost = measure_cost(reference, entities, lexicon_path, repeats=repeats)
    errors = error_analysis(reference, predictions)
    after = {name: agreement._sha256(path) for name, path in paths.items()}
    if after != before:
        raise RuntimeError("entrada alterada durante a avaliação")
    report = {
        "schema_version": 1, "purpose": "avaliação das regras sem treino contra a referência do piloto (D17)",
        "inputs": {name: {"path": agreement._path(path), "sha256": before[name]} for name, path in paths.items()},
        "inputs_unchanged": True,
        "settings": {"n_resamples": n_resamples, "seed": seed, "confidence": .95, "include_party_descriptions": False,
                     "fuzzy_threshold": mentions.FUZZY_THRESHOLD, "timing_repeats": repeats},
        "article_ids": list(dict.fromkeys(r["article_id"] for r in reference)),
        "entities": {e.id: e.canonical_name for e in entities},
        "reference": {
            "paragraphs": len(reference),
            "mentions": dict(Counter(m["type"] for r in reference for m in r["mentions"])),
            "teor": dict(Counter(label for r in reference for label in r["teor"].values())),
        },
        **results, "cost": cost, "errors": errors, "limitations": LIMITATIONS,
    }
    return report, predictions


def _f(value) -> str:
    return "n/d" if value is None else f"{value:.4f}"


def _ci(item: dict) -> str:
    return f"[{item['lower']:.4f}; {item['upper']:.4f}]"


def render_markdown(report: dict) -> str:
    names = report["entities"]
    name = lambda eid: names.get(str(eid), str(eid))
    ref, settings = report["reference"], report["settings"]
    labels = list(metrics.CLASSES)
    system_label = {"matcher": "Matcher (produção)", "recency": "Menção mais recente"}
    mode_label = {"exact": "exato", "partial": "parcial"}
    lines = [
        "# Avaliação das regras sem treino no piloto", "",
        f"Referência: voto da maioria do piloto (D17), {ref['paragraphs']} parágrafos de {len(report['article_ids'])} notícias ({', '.join(report['article_ids'])}). "
        f"Menções: {sum(ref['mentions'].values())} ({ref['mentions'].get('DIR', 0)} DIR, {ref['mentions'].get('IND', 0)} IND). "
        f"Pares de teor: {sum(ref['teor'].values())}. Descrições genéricas de partido desligadas (D15).", "",
        "## Limitações", "", *[f"- {item}" for item in report["limitations"]], "",
        "## 1. Menções", "",
        f"IC 95% por bootstrap percentil reamostrando notícias inteiras ({settings['n_resamples']} reamostragens, semente {settings['seed']}). "
        f"**Atenção: só há {len(report['article_ids'])} notícias**, então os intervalos são largos e pouco informativos.", "",
        "### Detecção (geral, sem exigir entidade nem tipo)", "",
        "| Sistema | Modo | TP | FP | FN | P | R | F1 | IC 95% F1 |", "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for system in MENTION_SYSTEMS:
        for mode in MODES:
            item = report["mentions"][system][mode]
            s = item["scores"]["overall"]
            lines.append(f"| {system_label[system]} | {mode_label[mode]} | {s['tp']} | {s['fp']} | {s['fn']} | {_f(s['precision'])} | {_f(s['recall'])} | {_f(s['f1'])} | {_ci(item['bootstrap']['overall_f1'])} |")
    lines += ["", "### Por tipo", "",
              "Uma confusão DIR/IND conta como FP no tipo previsto e FN no tipo da referência.", "",
              "| Sistema | Modo | Tipo | TP | FP | FN | P | R | F1 | IC 95% F1 |", "|---|---|---|---:|---:|---:|---:|---:|---:|---|"]
    for system in MENTION_SYSTEMS:
        for mode in MODES:
            item = report["mentions"][system][mode]
            for kind in metrics.TIPOS:
                s = item["scores"]["by_type"][kind]
                ci = _ci(item["bootstrap"]["ind_f1"]) if kind == "IND" else "–"
                lines.append(f"| {system_label[system]} | {mode_label[mode]} | {kind} | {s['tp']} | {s['fp']} | {s['fn']} | {_f(s['precision'])} | {_f(s['recall'])} | {_f(s['f1'])} | {ci} |")
    lines += ["", "### Ligação e joint (trecho + entidade)", "",
              "Ligação: acurácia da entidade entre os trechos casados na detecção. Joint: exige trecho e entidade, sem exigir tipo.", "",
              "| Sistema | Modo | Trechos casados | Ligação correta | Acurácia da ligação | Joint P | Joint R | Joint F1 |",
              "|---|---|---:|---:|---:|---:|---:|---:|"]
    for system in MENTION_SYSTEMS:
        for mode in MODES:
            s = report["mentions"][system][mode]["scores"]
            j = s["joint"]
            lines.append(f"| {system_label[system]} | {mode_label[mode]} | {s['linking']['matched']} | {s['linking']['correct']} | {_f(s['linking']['accuracy'])} | {_f(j['precision'])} | {_f(j['recall'])} | {_f(j['f1'])} |")

    def teor_tables(result: dict) -> list[str]:
        out = ["| Classe | TP | FP | FN | P | R | F1 |", "|---|---:|---:|---:|---:|---:|---:|"]
        out += [f"| {label} | {s['tp']} | {s['fp']} | {s['fn']} | {_f(s['precision'])} | {_f(s['recall'])} | {_f(s['f1'])} |"
                for label, s in result["per_class"].items()]
        out += ["", f"F1 macro: {_f(result['macro_f1'])}.", "",
                "Matriz de confusão (linhas: referência; colunas: previsto; pares sem previsão ficam fora da matriz):", "",
                "| Referência \\ Previsto | " + " | ".join(labels) + " | sem previsão |", "|---|" + "---:|" * (len(labels) + 1)]
        out += [f"| {label} | " + " | ".join(str(n) for n in row) + f" | {result['missing_predictions'][label]} |"
                for label, row in zip(labels, result["confusion_matrix"])]
        c = result["coverage"]
        out += ["", f"Cobertura: {c['gold_pairs']} pares na referência, {c['predicted_pairs']} pares previstos avaliados, "
                f"{c['outside_gold_predictions']} previstos fora da referência, {c['abstentions']} abstenções, "
                f"{c['gold_indeterminado_excluded']} indeterminados excluídos.", ""]
        return out

    lines += ["", "## 2. Teor isolado (léxico nos pares da referência)", "",
              f"**Atenção: há {ref['teor'].get('positivo', 0)} par positivo na referência**; F1 positivo e F1 macro são instáveis. "
              "`metrics.teor_scores` não devolve acurácia, então ela não é reportada.", "",
              "Distribuição das classes na referência:", "",
              "| Classe | Pares |", "|---|---:|", *[f"| {label} | {ref['teor'].get(label, 0)} |" for label in (*labels, "indeterminado")], "",
              *teor_tables(report["teor_isolado"]),
              "## 3. Fim a fim (menções previstas + léxico)", "",
              "Pares previstos fora da referência contam como FP; pares da referência sem previsão contam como FN.", ""]
    for system in MENTION_SYSTEMS:
        lines += [f"### {system_label[system]} + léxico", "", *teor_tables(report["fim_a_fim"][system])]
    lines += ["### Saldo por entidade (contagem de pares por classe)", "",
              "Ref = referência; M = matcher + léxico; R = recency + léxico. Formato positivo/negativo/neutro.", "",
              "| Entidade | Ref | M | R |", "|---|---|---|---|"]
    balances = {system: report["fim_a_fim"][system]["entity_balance"] for system in MENTION_SYSTEMS}
    triple = lambda counts, field: "/".join(str(counts[label][field]) if counts else "0" for label in labels)
    for eid in sorted(set().union(*balances.values()), key=lambda e: name(e)):
        ref_counts = next(b[eid] for b in balances.values() if eid in b)
        lines.append(f"| {name(eid)} | {triple(ref_counts, 'gold')} | {triple(balances['matcher'].get(eid), 'predicted')} | {triple(balances['recency'].get(eid), 'predicted')} |")
    cost = report["cost"]
    machine = cost["machine"]
    cost_label = {"matcher": "Matcher (só menções)", "recency": "Menção mais recente (só menções)",
                  "lexico_pares_referencia": "Léxico (pares da referência)",
                  "matcher_lexico": "Matcher + léxico", "recency_lexico": "Menção mais recente + léxico"}
    lines += ["", "## 4. Custo", "",
              f"Mediana de {cost['repeats']} execuções sobre os {cost['paragraphs']} parágrafos, normalizada para mil parágrafos (`time.perf_counter`). "
              f"Medido nesta máquina, não na VPS: {machine['platform']}, CPU {machine['cpu']} ({machine['cpu_count']} núcleos lógicos), Python {machine['python']}. "
              "Carregar entidades fica fora do tempo; carregar o léxico fica dentro.", "",
              "| Sistema | Mediana (s, 92 parágrafos) | s / 1000 parágrafos |", "|---|---:|---:|",
              *[f"| {cost_label[k]} | {v['median_seconds']:.4f} | {v['seconds_per_1000_paragraphs']:.4f} |" for k, v in cost["systems"].items()], ""]
    errors = report["errors"]
    lines += ["## 5. Listagem de erros (sem interpretação)", ""]
    for system in MENTION_SYSTEMS:
        items = errors["ind_perdidas"][system]
        lines += [f"### IND da referência perdidas: {system_label[system]} ({len(items)})", "",
                  "Perdida = nenhuma menção prevista com interseção e mesma entidade. A coluna seguinte mostra a previsão que se sobrepõe, se houver.", "",
                  "| Parágrafo | Trecho | Entidade | Previsão sobreposta | Contexto |", "|---|---|---|---|---|"]
        for i in items:
            overlap = i["predicted_overlap"]
            shown = "–" if overlap is None else f"\"{overlap['text']}\" ({overlap['type']}) -> {name(overlap['entity_id'])}"
            lines.append(f"| {i['paragraph_id']} | \"{i['text']}\" [{i['start']}:{i['end']}] | {name(i['entity_id'])} | {shown} | {_md(i['context'])} |")
        lines.append("")
    items = errors["recency_fp_exato"]
    lines += [f"### Menções previstas falsas (FP) da menção mais recente, modo exato ({len(items)})", "",
              "| Parágrafo | Trecho | Tipo | Entidade | FP também no parcial | Contexto |", "|---|---|---|---|---|---|",
              *[f"| {i['paragraph_id']} | \"{i['text']}\" [{i['start']}:{i['end']}] | {i['type']} | {name(i['entity_id'])} | {'sim' if i['fp_partial'] else 'não'} | {_md(i['context'])} |" for i in items], ""]
    items = errors["teor_isolado_erros"]
    lines += [f"### Pares de teor errados pelo léxico, teor isolado ({len(items)})", "",
              "| Parágrafo | Entidade | Referência | Previsto | Texto |", "|---|---|---|---|---|",
              *[f"| {i['paragraph_id']} | {name(i['entity_id'])} | {i['reference']} | {i['predicted']} | {_md(i['text'])} |" for i in items], ""]
    lines += ["## Procedência", "", "Entradas e código lidos sem gravação, com SHA-256 conferido antes e depois.", "",
              "| Entrada | Caminho | SHA-256 |", "|---|---|---|",
              *[f"| {key} | `{value['path']}` | `{value['sha256']}` |" for key, value in report["inputs"].items()],
              *[f"| saída | `{key}` | `{value['sha256']}` |" for key, value in report["outputs"].items()], "",
              "```sh", ".venv-experiments/bin/python experiments/evaluate.py", "```", ""]
    return "\n".join(lines)


def _md(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def write_evaluation(report: dict, predictions: dict[str, list[dict]], output_dir: Path) -> dict[str, Path]:
    """Grava relatório e predições; recusa se qualquer arquivo já existir."""
    output_dir = Path(output_dir)
    targets = {name: output_dir / name for name in OUTPUTS}
    consolidate._refuse_existing(targets.values())
    texts = {PREDICTION_FILES[key]: consolidate._jsonl(records) for key, records in predictions.items()}
    report = {**report, "outputs": {name: {"sha256": consolidate._sha256_text(text)} for name, text in texts.items()}}
    # Serializa tudo antes de abrir as saídas para não deixar arquivo parcial.
    texts["report.md"] = render_markdown(report)
    texts["report.json"] = json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n"
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in OUTPUTS:
        consolidate._write_new(targets[name], texts[name])
    return targets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--referencia", type=Path, default=DEFAULT_REFERENCE, help="referencia.jsonl consolidada (D17)")
    parser.add_argument("--entidades", type=Path, default=gold.DEFAULT_ENTITIES, help="snapshot de entidades usado no piloto")
    parser.add_argument("--lexico", type=Path, default=DEFAULT_LEXICON, help="léxico de produção")
    parser.add_argument("--saida", type=Path, default=DEFAULT_OUTPUT, help="pasta de saída; arquivos existentes não são sobrescritos")
    parser.add_argument("--reamostragens", type=int, default=1000)
    parser.add_argument("--semente", type=int, default=42)
    parser.add_argument("--repeticoes", type=int, default=7, help="execuções por sistema na medição de tempo")
    args = parser.parse_args(argv)
    try:
        # Falha cedo, antes de rodar bootstrap e medição de tempo.
        consolidate._refuse_existing(Path(args.saida) / name for name in OUTPUTS)
        report, predictions = build_report(reference_path=args.referencia, entities_path=args.entidades,
                                           lexicon_path=args.lexico, n_resamples=args.reamostragens,
                                           seed=args.semente, repeats=args.repeticoes)
        targets = write_evaluation(report, predictions, args.saida)
    except (ValueError, OSError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"saida": agreement._path(Path(args.saida)), "inputs_unchanged": report["inputs_unchanged"],
                      "arquivos": [path.name for path in targets.values()]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
