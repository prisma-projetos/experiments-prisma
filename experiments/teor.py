"""Adaptadores do léxico de produção e TF-IDF para avaliar teor por alvo.

Em ``pairs='mentions'``, usa as entidades das menções previstas. Em
``pairs='gold'``, usa somente as chaves de ``teor`` do gabarito, inclusive
pares sem menção explícita. Na predição, os valores anotados nunca são
usados como features ou copiados para a saída. O léxico classifica o texto
original uma vez por parágrafo e aplica a categoria a todos os alvos,
como em produção. TF-IDF usa uma representação marcada por alvo e mantém
o texto original quando não há trecho correspondente. Scikit-learn é uma
dependência opcional, importada apenas por fit_tfidf durante o treino.
"""
from __future__ import annotations

import sys
import hashlib
import json
import platform
from collections import Counter
from collections.abc import Iterable
from copy import deepcopy
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR / "src") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "src"))

from lexicon import classify_paragraph, load_lexicon  # noqa: E402


def _entity_id(value) -> str:
    if (isinstance(value, bool) or not isinstance(value, (str, int))
            or not str(value).strip()):
        raise ValueError("entity_id precisa ser string não vazia ou inteiro")
    return str(value).strip()


def predict_lexicon(
    records: Iterable[dict], *, pairs: str = "mentions",
    lexicon_path: Path | str = BASE_DIR / "config" / "lexicon.yaml",
) -> list[dict]:
    """Prevê teor sem alterar a entrada ou filtrar rótulos indeterminados.

    A exclusão de ``indeterminado`` pertence às métricas, que recebem o
    gabarito separadamente. ``prediction_config`` registra o modo e a
    origem dos pares; a opção gold é uma avaliação isolada de teor.
    """
    if pairs not in {"mentions", "gold"}:
        raise ValueError("pairs deve ser 'mentions' ou 'gold'")
    lexicon = load_lexicon(Path(lexicon_path))
    predictions, seen = [], set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("registro precisa ser um mapeamento")
        article_id, index, text = record.get("article_id"), record.get("paragraph_index"), record.get("text")
        if (not isinstance(article_id, str) or not article_id.strip()
                or not isinstance(index, int) or isinstance(index, bool) or index < 0
                or not isinstance(text, str)):
            raise ValueError("registro requer article_id string, paragraph_index inteiro >= 0 e text string")
        if (article_id, index) in seen:
            raise ValueError(f"parágrafo duplicado: {(article_id, index)}")
        seen.add((article_id, index))
        mentions = record.get("mentions", [])
        config = record.get("prediction_config", {})
        if not isinstance(mentions, list) or any(not isinstance(m, dict) for m in mentions):
            raise ValueError("mentions precisa ser uma lista de mapeamentos")
        if not isinstance(config, dict):
            raise ValueError("prediction_config precisa ser um mapeamento")
        mentions = deepcopy(mentions)
        for mention in mentions:
            mention["entity_id"] = _entity_id(mention.get("entity_id"))
        if pairs == "mentions":
            entity_ids = list(dict.fromkeys(m["entity_id"] for m in mentions))
        else:
            gold_pairs = record.get("teor", {})
            if not isinstance(gold_pairs, dict):
                raise ValueError("teor precisa ser um mapeamento no modo gold")
            entity_ids = [_entity_id(entity_id) for entity_id in gold_pairs]
            if len(entity_ids) != len(set(entity_ids)):
                raise ValueError("chaves de teor duplicadas após normalizar entity_id")
        category = classify_paragraph(text, lexicon).category if entity_ids else None
        prediction = {
            "article_id": article_id, "paragraph_index": index, "text": text,
            "mentions": mentions, "teor": {entity_id: category for entity_id in entity_ids},
            "prediction_config": {**deepcopy(config), "mode": "production_lexicon", "pairs": pairs},
        }
        if "split" in record:
            prediction["split"] = deepcopy(record["split"])
        predictions.append(prediction)
    return predictions


def mark_target(text: str, mentions: list[dict], entity_id: str | int) -> str:
    """Substitui todos os trechos do alvo por [ALVO], nos offsets originais.

    Sobreposições da mesma entidade são fundidas. Sem trecho do alvo, mantém
    o texto: alvos sem trecho no mesmo parágrafo têm a mesma representação.
    """
    target = _entity_id(entity_id)
    if not isinstance(text, str) or not isinstance(mentions, list):
        raise ValueError("text precisa ser string e mentions uma lista")
    spans = []
    for mention in mentions:
        if not isinstance(mention, dict):
            raise ValueError("menção precisa ser um mapeamento")
        current = _entity_id(mention.get("entity_id"))
        start, end = mention.get("start"), mention.get("end")
        if (not isinstance(start, int) or isinstance(start, bool)
                or not isinstance(end, int) or isinstance(end, bool)
                or not 0 <= start < end <= len(text)):
            raise ValueError("offsets de menção inválidos no texto original")
        if "text" in mention and mention["text"] != text[start:end]:
            raise ValueError("texto da menção difere do trecho nos offsets")
        if current == target:
            spans.append((start, end))
    merged = []
    for start, end in sorted(spans):
        if merged and start < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    for start, end in reversed(merged):
        text = text[:start] + "[ALVO]" + text[end:]
    return text


def _tfidf_records(records: Iterable[dict], pairs: str) -> list[tuple[dict, list[str]]]:
    if pairs not in {"gold", "mentions"}:
        raise ValueError("pairs deve ser 'mentions' ou 'gold'")
    output, seen, article_splits = [], set(), {}
    for source in records:
        if not isinstance(source, dict):
            raise ValueError("registro precisa ser um mapeamento")
        record = deepcopy(source)
        article_id, index, text = record.get("article_id"), record.get("paragraph_index"), record.get("text")
        if (not isinstance(article_id, str) or not article_id.strip()
                or not isinstance(index, int) or isinstance(index, bool) or index < 0
                or not isinstance(text, str)):
            raise ValueError("registro requer article_id string, paragraph_index inteiro >= 0 e text string")
        key = article_id, index
        if key in seen:
            raise ValueError(f"parágrafo duplicado: {key}")
        seen.add(key)
        split = record.get("split")
        if article_id in article_splits and article_splits[article_id] != split:
            raise ValueError(f"notícia em splits diferentes: {article_id}")
        article_splits[article_id] = split
        mentions = record.setdefault("mentions", [])
        # Valida inclusive parágrafos sem pares antes de chamar o modelo.
        mark_target(text, mentions, "__validation__")
        for mention in mentions:
            mention["entity_id"] = _entity_id(mention["entity_id"])
        if not isinstance(record.get("prediction_config", {}), dict):
            raise ValueError("prediction_config precisa ser um mapeamento")
        if pairs == "gold":
            raw = record.get("teor", {})
            if not isinstance(raw, dict):
                raise ValueError("teor precisa ser um mapeamento no modo gold")
            ids = [_entity_id(entity_id) for entity_id in raw]
            if len(ids) != len(set(ids)):
                raise ValueError("chaves de teor duplicadas após normalizar entity_id")
            record["teor"] = dict(zip(ids, raw.values()))
        else:
            ids = list(dict.fromkeys(m["entity_id"] for m in mentions))
        output.append((record, ids))
    return output


def _dataset_hash(records: list[dict]) -> str:
    data = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def fit_tfidf(records: Iterable[dict]):
    """Ajusta TF-IDF e regressão logística somente nos pares de treino.

    Exclui indeterminado; exige ao menos duas classes conhecidas. Split
    ausente permite fixtures sintéticas; split informado precisa ser train.
    O piloto fica sempre fora. Metadados ficam em training_metadata_.
    """
    prepared = _tfidf_records(records, "gold")
    texts, labels = [], []
    unmarked = excluded = 0
    classes = ("positivo", "negativo", "neutro")
    pilot_ids = {"145", "159", "146", "160", "175"}
    for record, ids in prepared:
        if "split" in record and record["split"] != "train":
            raise ValueError("fit_tfidf aceita somente split train")
        if record["article_id"].strip() in pilot_ids:
            raise ValueError("notícia do piloto não pode entrar no treino")
        if record.get("needs_review", False) is not False:
            raise ValueError("registro pendente de revisão não pode entrar no treino")
        for entity_id in ids:
            label = record["teor"][entity_id]
            if label == "indeterminado":
                excluded += 1
                continue
            if not isinstance(label, str) or label not in classes:
                raise ValueError(f"rótulo de treino desconhecido: {label!r}")
            texts.append(mark_target(record["text"], record["mentions"], entity_id))
            labels.append(label)
            unmarked += not any(m["entity_id"] == entity_id for m in record["mentions"])
    if len(set(labels)) < 2:
        raise ValueError("treino requer pelo menos duas classes determinadas")
    try:
        import sklearn
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
    except ImportError as exc:
        raise ImportError("TF-IDF requer scikit-learn no ambiente isolado de experimentos") from exc
    model = Pipeline([
        ("tfidf", TfidfVectorizer()),
        ("classifier", LogisticRegression(class_weight="balanced", random_state=42, max_iter=1000)),
    ])
    model.fit(texts, labels)
    counts = Counter(labels)
    model.training_metadata_ = {
        "mode": "tfidf_logistic_regression", "seed": 42,
        "paragraphs": len(prepared), "pairs": len(labels), "unmarked_pairs": unmarked,
        "article_ids": sorted({record["article_id"] for record, _ in prepared}),
        "excluded_indeterminado": excluded,
        "label_counts": {label: counts[label] for label in classes},
        "split_counts": dict(Counter(record.get("split", "unspecified") for record, _ in prepared)),
        "dataset_sha256": _dataset_hash([record for record, _ in prepared]),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "versions": {"python": platform.python_version(), "scikit-learn": sklearn.__version__},
        "features": {"marker": "[ALVO]", "marker_token": "alvo", "lowercase": True,
                     "ngram_range": [1, 1], "class_weight": "balanced", "max_iter": 1000},
        "unmarked_policy": "original_text",
    }
    return model


def predict_tfidf(model, records: Iterable[dict], *, pairs: str = "mentions") -> list[dict]:
    """Prevê uma classe por alvo; gold usa apenas as chaves anotadas.

    Cada registro informa quantos pares ficaram sem marcador. O texto e as
    menções originais são preservados; os rótulos recebidos não são features.
    """
    prepared = _tfidf_records(records, pairs)
    predictions = []
    training_ids = set(getattr(model, "training_metadata_", {}).get("article_ids", []))
    for record, ids in prepared:
        if record["article_id"] in training_ids and record.get("split") in {"validation", "test"}:
            raise ValueError("notícia de treino também aparece na validação/teste")
        texts = [mark_target(record["text"], record["mentions"], entity_id) for entity_id in ids]
        labels = model.predict(texts).tolist() if texts else []
        if len(labels) != len(ids) or any(label not in {"positivo", "negativo", "neutro"} for label in labels):
            raise ValueError("modelo retornou classes de teor inválidas")
        unmarked = sum(not any(m["entity_id"] == entity_id for m in record["mentions"]) for entity_id in ids)
        prediction = {
            "article_id": record["article_id"], "paragraph_index": record["paragraph_index"],
            "text": record["text"], "mentions": record["mentions"], "teor": dict(zip(ids, labels)),
            "prediction_config": {**record.get("prediction_config", {}),
                                  "mode": "tfidf_logistic_regression", "pairs": pairs,
                                  "unmarked_pairs": unmarked, "unmarked_policy": "original_text"},
        }
        if "split" in record:
            prediction["split"] = record["split"]
        predictions.append(prediction)
    return predictions
