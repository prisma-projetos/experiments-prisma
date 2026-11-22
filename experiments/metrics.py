"""Métricas dos experimentos, sem dependência de banco ou bibliotecas de ML.

As funções de avaliação recebem os registros por parágrafo de ``gold.py``.
Offsets usam o intervalo [start, end), no texto original. Ausência de teor
não é convertida em neutro. Valores indefinidos são devolvidos como None.
"""
from __future__ import annotations

import math
import random
from collections import Counter, defaultdict
from numbers import Integral

CLASSES = ("positivo", "negativo", "neutro")
TIPOS = ("DIR", "IND")


def _prf(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "tp": tp, "fp": fp, "fn": fn,
        "precision": precision, "recall": recall,
        "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0,
    }


def _check_span(mention: dict) -> None:
    start, end = mention["start"], mention["end"]
    if (
        isinstance(start, bool) or isinstance(end, bool)
        or not isinstance(start, Integral) or not isinstance(end, Integral)
        or start < 0 or end <= start
    ):
        raise ValueError(f"offsets inválidos: {start!r}, {end!r}")
    if mention["type"] not in TIPOS:
        raise ValueError(f"tipo de menção desconhecido: {mention['type']!r}")


def match_mentions(
    gold: list[dict], predicted: list[dict], *, mode: str = "exact",
    require_type: bool = False, require_entity: bool = False,
) -> list[tuple[int, int]]:
    """Casamento bipartido de cardinalidade máxima para um único parágrafo.

    Cada índice é usado uma vez. O desempate percorre trechos em ordem de
    offsets e posição de entrada; a entidade não orienta o casamento de
    detecção. O modo partial aceita interseção de pelo menos um caractere.
    """
    if mode not in {"exact", "partial"}:
        raise ValueError("mode deve ser 'exact' ou 'partial'")
    for mention in gold + predicted:
        _check_span(mention)
    order = lambda mentions, i: (mentions[i]["start"], mentions[i]["end"], i)
    gold_order = sorted(range(len(gold)), key=lambda i: order(gold, i))
    pred_order = sorted(range(len(predicted)), key=lambda i: order(predicted, i))
    edges = {}
    for i in gold_order:
        a = gold[i]
        edges[i] = []
        for j in pred_order:
            b = predicted[j]
            intersects = max(a["start"], b["start"]) < min(a["end"], b["end"])
            same_span = (a["start"], a["end"]) == (b["start"], b["end"])
            if not (same_span if mode == "exact" else intersects):
                continue
            if require_type and a["type"] != b["type"]:
                continue
            if require_entity and str(a["entity_id"]) != str(b["entity_id"]):
                continue
            edges[i].append(j)

    owner: dict[int, int] = {}

    def augment(i: int, visited: set[int]) -> bool:
        for j in edges[i]:
            if j in visited:
                continue
            visited.add(j)
            if j not in owner or augment(owner[j], visited):
                owner[j] = i
                return True
        return False

    for i in gold_order:
        augment(i, set())
    return sorted((i, j) for j, i in owner.items())


def _paragraphs(records: list[dict]) -> dict[tuple[str, int], dict]:
    paragraphs = {}
    for record in records:
        key = (str(record["article_id"]), record["paragraph_index"])
        if key in paragraphs:
            raise ValueError(f"parágrafo duplicado: {key}")
        paragraphs[key] = record
    return paragraphs


def mention_scores(
    gold_records: list[dict], predicted_records: list[dict], *, mode: str = "exact",
) -> dict:
    """Detecção, ligação dos trechos casados e F1 de trecho + entidade.

    O total ignora tipo. Por tipo, uma confusão DIR/IND conta como FP no
    tipo previsto e FN no tipo do gabarito. Joint exige trecho e entidade,
    sem exigir tipo, como a definição de ligação no plano.
    """
    if mode not in {"exact", "partial"}:
        raise ValueError("mode deve ser 'exact' ou 'partial'")
    gold, predicted = _paragraphs(gold_records), _paragraphs(predicted_records)
    counts = Counter()
    types = {kind: Counter() for kind in TIPOS}
    for key in sorted(gold.keys() | predicted.keys()):
        truth = gold.get(key, {}).get("mentions", [])
        guess = predicted.get(key, {}).get("mentions", [])
        matches = match_mentions(truth, guess, mode=mode)
        joint = match_mentions(truth, guess, mode=mode, require_entity=True)
        counts.update({"gold": len(truth), "predicted": len(guess), "matched": len(matches), "joint": len(joint)})
        counts["linked"] += sum(str(truth[i]["entity_id"]) == str(guess[j]["entity_id"]) for i, j in matches)
        for kind in TIPOS:
            a = [m for m in truth if m["type"] == kind]
            b = [m for m in guess if m["type"] == kind]
            types[kind].update({"gold": len(a), "predicted": len(b), "matched": len(match_mentions(a, b, mode=mode))})

    def score(c: Counter, field: str = "matched") -> dict:
        return _prf(c[field], c["predicted"] - c[field], c["gold"] - c[field])

    return {
        "overall": score(counts),
        "by_type": {kind: score(count) for kind, count in types.items()},
        "linking": {
            "matched": counts["matched"], "correct": counts["linked"],
            "accuracy": counts["linked"] / counts["matched"] if counts["matched"] else None,
        },
        "joint": score(counts, "joint"),
    }


def _teores(records: list[dict]) -> dict[tuple[str, int, str], str]:
    values = {}
    for (article_id, paragraph_index), record in _paragraphs(records).items():
        for entity_id, label in record.get("teor", {}).items():
            if label not in (*CLASSES, "indeterminado"):
                raise ValueError(f"teor desconhecido: {label!r}")
            key = (article_id, paragraph_index, str(entity_id))
            if key in values:
                raise ValueError(f"par de teor duplicado: {key}")
            values[key] = label
    return values


def teor_scores(
    gold_records: list[dict], predicted_records: list[dict], *, end_to_end: bool = False,
) -> dict:
    """Teor em três classes; gold indeterminado exclui a unidade inteira.

    Na etapa isolada, previsões fora dos pares do gold são informadas, mas
    não avaliadas. Fim a fim também conta esses pares como FP. Abstenção
    prevista (indeterminado) conta como ausência, nunca como classe neutra.
    """
    truth, guess = _teores(gold_records), _teores(predicted_records)
    excluded = {key for key, label in truth.items() if label == "indeterminado"}
    truth = {key: label for key, label in truth.items() if key not in excluded}
    guessed = {key: label for key, label in guess.items() if key not in excluded and label != "indeterminado"}
    outside = set(guessed) - set(truth)
    if not end_to_end:
        guessed = {key: label for key, label in guessed.items() if key in truth}
    per_class = {}
    for label in CLASSES:
        a = {key for key, value in truth.items() if value == label}
        b = {key for key, value in guessed.items() if value == label}
        per_class[label] = _prf(len(a & b), len(b - a), len(a - b))
    matrix = [[0 for _ in CLASSES] for _ in CLASSES]
    missing = Counter()
    for key, label in truth.items():
        if key in guessed:
            matrix[CLASSES.index(label)][CLASSES.index(guessed[key])] += 1
        else:
            missing[label] += 1
    balance = {}
    for entity_id in sorted({key[2] for key in truth.keys() | guessed.keys()}):
        balance[entity_id] = {}
        for label in CLASSES:
            n_gold = sum(key[2] == entity_id and value == label for key, value in truth.items())
            n_predicted = sum(key[2] == entity_id and value == label for key, value in guessed.items())
            balance[entity_id][label] = {"gold": n_gold, "predicted": n_predicted, "absolute_difference": abs(n_predicted - n_gold)}
    return {
        "labels": list(CLASSES), "per_class": per_class,
        "macro_f1": sum(value["f1"] for value in per_class.values()) / len(CLASSES),
        "confusion_matrix": matrix,
        "missing_predictions": {label: missing[label] for label in CLASSES},
        "coverage": {
            "gold_pairs": len(truth), "predicted_pairs": len(guessed),
            "gold_indeterminado_excluded": len(excluded),
            "outside_gold_predictions": len(outside),
            "abstentions": sum(label == "indeterminado" and key not in excluded for key, label in guess.items()),
        },
        "entity_balance": balance,
    }


def fleiss_kappa(counts: list[list[int]]) -> float | None:
    """Kappa de Fleiss com número constante de avaliadores por unidade.

    Cada linha contém contagens por categoria, não os códigos dos rótulos.
    Sem unidades ou com concordância esperada igual a 1, é indefinido.
    """
    if not counts:
        return None
    width = len(counts[0])
    if width < 2:
        raise ValueError("são necessárias pelo menos duas categorias")
    for row in counts:
        if len(row) != width or any(isinstance(n, bool) or not isinstance(n, Integral) or n < 0 for n in row):
            raise ValueError("contagens devem ser inteiros não negativos, com categorias constantes")
    n_raters = sum(counts[0])
    if n_raters < 2:
        raise ValueError("são necessários pelo menos dois avaliadores")
    for row in counts:
        if sum(row) != n_raters:
            raise ValueError("número de avaliadores deve ser constante entre unidades")
    observed = sum(sum(n * (n - 1) for n in row) / (n_raters * (n_raters - 1)) for row in counts) / len(counts)
    expected = sum((sum(row[j] for row in counts) / (len(counts) * n_raters)) ** 2 for j in range(width))
    return (observed - expected) / (1 - expected) if expected < 1 else None


def _quantile(values: list[float], probability: float) -> float:
    position = (len(values) - 1) * probability
    low = math.floor(position)
    fraction = position - low
    return values[low] * (1 - fraction) + values[min(low + 1, len(values) - 1)] * fraction


def bootstrap_by_article(
    gold_records: list[dict], predicted_records: list[dict], score_fn, *,
    n_resamples: int = 1000, seed: int = 42, confidence: float = 0.95,
) -> dict:
    """IC percentil reamostrando notícias inteiras, com reposição.

    Cada cópia sorteada recebe um ID próprio para não colapsar unidades
    repetidas nas métricas por chave. O callback recebe duas listas de
    registros e deve devolver um número finito.
    """
    if isinstance(n_resamples, bool) or not isinstance(n_resamples, Integral) or n_resamples < 1:
        raise ValueError("n_resamples deve ser inteiro positivo")
    if not 0 < confidence < 1:
        raise ValueError("confidence deve estar entre zero e um")
    gold, predicted = defaultdict(list), defaultdict(list)
    for record in gold_records:
        gold[str(record["article_id"])].append(record)
    for record in predicted_records:
        predicted[str(record["article_id"])].append(record)
    article_ids = sorted(gold.keys() | predicted.keys())
    if not article_ids:
        raise ValueError("bootstrap exige pelo menos uma notícia")

    def evaluate(a, b):
        value = float(score_fn(a, b))
        if not math.isfinite(value):
            raise ValueError("score_fn deve devolver número finito")
        return value

    estimate = evaluate(gold_records, predicted_records)
    rng, values = random.Random(seed), []
    for _ in range(n_resamples):
        a, b = [], []
        for draw in range(len(article_ids)):
            article_id = rng.choice(article_ids)
            copy_id = f"{draw}:{article_id}"
            a.extend({**record, "article_id": copy_id} for record in gold[article_id])
            b.extend({**record, "article_id": copy_id} for record in predicted[article_id])
        values.append(evaluate(a, b))
    values.sort()
    tail = (1 - confidence) / 2
    return {
        "estimate": estimate, "lower": _quantile(values, tail), "upper": _quantile(values, 1 - tail),
        "confidence": confidence, "n_articles": len(article_ids), "n_resamples": n_resamples, "seed": seed,
    }
