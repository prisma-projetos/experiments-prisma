"""Menções experimentais com offsets no parágrafo original (D10–D12).

``matcher`` conserva a decisão de produção, inclusive seus aliases e fuzzy.
``recency`` usa o reconhecimento experimental e liga os indiretos em ordem.
Recebe parágrafos já segmentados; não lê rótulos de menção ou teor da entrada.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from collections.abc import Iterable
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR / "src") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "src"))

import yaml  # noqa: E402

from entities_store import Entity  # noqa: E402
from entity_matcher import (  # noqa: E402
    _CASE_SENSITIVE_ALIASES,
    _alias_pattern,
    _fold_diacritics,
    _fuzzy_match_score,
    match_entities,
)

# Congelado com o valor de config/settings.yaml nesta etapa experimental.
FUZZY_THRESHOLD = 0.85
_PARTY_TYPES = {"party", "partido"}
_PERSON_TYPES = {"politician", "politico"}
_WORD_RE = re.compile(r"\w+", re.UNICODE)
_PRONOUN_RE = re.compile(r"\b(?:ele|ela|dele|dela)\b", re.IGNORECASE)
# Lista fixa derivada dos exemplos do protocolo; não é aprendida no teste.
PERSON_DESCRIPTIONS = (
    "presidente", "candidato", "candidata", "petista", "pessebista",
    "senador", "senadora", "ex-presidente", "ex-governador", "ex-governadora",
)
PARTY_DESCRIPTIONS = ("partido", "legenda", "sigla")
_ARTICLES = {"o", "a", "os", "as", "do", "da", "dos", "das", "no", "na",
             "nos", "nas", "ao", "aos", "pelo", "pela", "pelos", "pelas"}
_COMMON_PARTY_NAMES = {
    "missao", "avante", "republicanos", "cidadania", "podemos", "solidariedade",
    "agir", "democrata", "novo", "rede", "uniao",
}


def load_entities_snapshot(path: Path | str) -> list[Entity]:
    """Converte o snapshot D4 para Entity, com os IDs iguais aos do validador."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("entities"), list):
        raise ValueError("snapshot precisa de uma lista 'entities'")
    entities = []
    seen = set()
    for raw in data["entities"]:
        if not isinstance(raw, dict):
            raise ValueError("entidade do snapshot precisa ser um mapeamento")
        entity_id = raw.get("entity_id", raw.get("id"))
        name = raw.get("nome_principal", raw.get("canonical_name"))
        kind = raw.get("entity_type")
        aliases = raw.get("aliases", [])
        if (not isinstance(entity_id, (str, int)) or isinstance(entity_id, bool)
                or not str(entity_id).strip() or not isinstance(name, str) or not name.strip()
                or kind not in _PARTY_TYPES | _PERSON_TYPES
                or not isinstance(aliases, list)
                or any(not isinstance(a, str) or not a.strip() for a in aliases)):
            raise ValueError("entidade inválida no snapshot")
        entity_id = str(entity_id)
        if entity_id in seen:
            raise ValueError(f"entity_id repetido: {entity_id}")
        seen.add(entity_id)
        entities.append(Entity(entity_id, name, kind, tuple(aliases)))
    return entities


def normalize_with_map(text: str) -> tuple[str, list[tuple[int, int]]]:
    """Normaliza D12; cada caractere aponta para [start, end) no original.

    Pontuação, símbolos e espaços viram separadores. Marcas combinantes
    pertencem à letra anterior para preservar offsets em Unicode decomposto.
    """
    chars: list[str] = []
    positions: list[tuple[int, int]] = []
    for index, char in enumerate(text):
        if unicodedata.combining(char):
            if positions:
                positions[-1] = (positions[-1][0], index + 1)
            continue
        folded = _fold_diacritics(char).lower()
        for letter in folded:
            if letter.isalnum():
                chars.append(letter)
                positions.append((index, index + 1))
            elif chars and chars[-1] != " ":
                chars.append(" ")
                positions.append((index, index + 1))
            elif positions and chars[-1] == " ":
                positions[-1] = (positions[-1][0], index + 1)
    if chars and chars[-1] == " ":
        chars.pop()
        positions.pop()
    return "".join(chars), positions


def _fold_with_map(text: str) -> tuple[str, list[tuple[int, int]]]:
    # Este caminho mantém pontuação e caixa exatamente como a produção.
    chars, positions = [], []
    for index, char in enumerate(text):
        if unicodedata.combining(char):
            if positions:
                positions[-1] = (positions[-1][0], index + 1)
            continue
        for letter in _fold_diacritics(char):
            chars.append(letter)
            positions.append((index, index + 1))
    return "".join(chars), positions


def _mention(text: str, start: int, end: int, entity_id: str, kind: str, **extra) -> dict:
    return {"start": start, "end": end, "text": text[start:end],
            "type": kind, "entity_id": entity_id, **extra}


def _production_mentions(text: str, entities: list[Entity]) -> list[dict]:
    folded, positions = _fold_with_map(text)
    words = list(_WORD_RE.finditer(folded))
    mentions = []
    for match in match_entities(text, entities, fuzzy_threshold=FUZZY_THRESHOLD):
        alias = match.matched_alias
        if match.match_type == "exact":
            special = _CASE_SENSITIVE_ALIASES.get(alias.upper())
            pattern = _alias_pattern(special or _fold_diacritics(alias),
                                     re.UNICODE if special else re.IGNORECASE | re.UNICODE)
            spans = [(m.start(), m.end(), 1.0) for m in pattern.finditer(folded)]
        else:
            size = len(alias.split())
            spans = []
            for index in range(len(words) - size + 1):
                start, end = words[index].start(), words[index + size - 1].end()
                score = _fuzzy_match_score(alias, folded[start:end])
                if score >= FUZZY_THRESHOLD:
                    spans.append((start, end, score))
        for start, end, score in spans:
            mentions.append(_mention(text, positions[start][0], positions[end - 1][1],
                                     match.entity_id, "DIR", match_type=match.match_type,
                                     score=score, matched_alias=alias))
    return _deduplicate(mentions)


def _deduplicate(mentions: list[dict]) -> list[dict]:
    # Prefere o alias maior da mesma entidade. Candidatos diferentes ficam
    # explícitos, mesmo que ocupem o mesmo trecho.
    kept = []
    for mention in sorted(mentions, key=lambda m: (-(m["end"] - m["start"]), m["start"], m["entity_id"])):
        if any(m["entity_id"] == mention["entity_id"]
               and m["start"] < mention["end"] and mention["start"] < m["end"] for m in kept):
            continue
        kept.append(mention)
    return sorted(kept, key=lambda m: (m["start"], m["end"], m["entity_id"]))


def _experimental_mentions(text: str, entities: list[Entity]) -> list[dict]:
    normalized, positions = normalize_with_map(text)
    words = list(_WORD_RE.finditer(normalized))
    parentheses, openings = [], []
    for index, char in enumerate(text):
        if char == "(":
            openings.append(index)
        elif char == ")" and openings:
            parentheses.append((openings.pop(), index + 1))
    parentheses.extend((start, len(text) + 1) for start in openings)
    mentions = []
    for entity in entities:
        for alias in dict.fromkeys(entity.all_match_candidates()):
            normalized_alias, _ = normalize_with_map(alias)
            if not normalized_alias:
                continue
            exact = list(_alias_pattern(normalized_alias, re.UNICODE).finditer(normalized))
            spans = [(m.start(), m.end(), "exact", 1.0) for m in exact]
            if not exact and normalized_alias not in _COMMON_PARTY_NAMES:
                size = len(normalized_alias.split())
                for index in range(len(words) - size + 1):
                    start, end = words[index].start(), words[index + size - 1].end()
                    score = _fuzzy_match_score(normalized_alias, normalized[start:end])
                    if score >= FUZZY_THRESHOLD:
                        spans.append((start, end, "fuzzy", score))
            for start, end, match_type, score in spans:
                original_start, original_end = positions[start][0], positions[end - 1][1]
                if entity.entity_type in _PARTY_TYPES:
                    previous = normalized[:start].split()
                    previous_word = previous[-1] if previous else None
                    if normalized_alias in _COMMON_PARTY_NAMES:
                        if previous_word != "partido":
                            continue
                    elif len(normalized_alias.split()) == 1:
                        if (previous_word not in _ARTICLES
                                or any(a < original_start and original_end < b for a, b in parentheses)):
                            continue
                mentions.append(_mention(text, original_start, original_end, entity.id, "DIR",
                                         match_type=match_type, score=score, matched_alias=alias))
    return _deduplicate(mentions)


def _description_pattern(terms: tuple[str, ...]) -> re.Pattern[str]:
    return re.compile(r"\b(?:o|a|do|da|no|na|ao|pelo|pela|à)\s+(?:"
                      + "|".join(re.escape(term) for term in sorted(terms, key=len, reverse=True))
                      + r")\b", re.IGNORECASE)


def predict_mentions(
    records: Iterable[dict],
    entities: list[Entity],
    *,
    system: str = "matcher",
    include_party_descriptions: bool,
) -> list[dict]:
    """Prevê DIR e, em recency, IND; exige decisão explícita sobre D10.

    Retorna registros com article_id, paragraph_index, text, mentions e teor
    vazio, na ordem recebida. Para recency, ordena internamente por índice e
    reinicia antecedentes em cada notícia. Não há lookahead nem filtro de
    gênero. Descrições usam a última entidade *nomeada* do tipo apropriado.
    Empates entre candidatos ficam sem ligação indireta até nova menção.

    Limites: lista descritiva curta, sem extensão automática de adjetivos;
    não distingue Jair de Flávio pelo cargo. Matcher localiza somente o
    alias escolhido pela produção, inclusive suas janelas fuzzy aprovadas.
    """
    if system not in {"matcher", "recency"}:
        raise ValueError("system deve ser 'matcher' ou 'recency'")
    if not isinstance(include_party_descriptions, bool):
        raise ValueError("include_party_descriptions precisa ser bool explícito")
    by_id = {}
    for entity in entities:
        if (not isinstance(entity, Entity) or not isinstance(entity.id, str) or not entity.id
                or entity.entity_type not in _PERSON_TYPES | _PARTY_TYPES
                or not isinstance(entity.canonical_name, str) or not entity.canonical_name.strip()
                or not isinstance(entity.aliases, tuple)
                or any(not isinstance(alias, str) or not alias.strip() for alias in entity.aliases)
                or entity.id in by_id):
            raise ValueError("entities precisa conter Entity com IDs únicos e tipos válidos")
        by_id[entity.id] = entity
    output, articles, seen = [], {}, set()
    for record in records:
        article_id, index, text = record.get("article_id"), record.get("paragraph_index"), record.get("text")
        if (not isinstance(article_id, str) or not article_id
                or not isinstance(index, int) or isinstance(index, bool) or index < 0
                or not isinstance(text, str)):
            raise ValueError("registro requer article_id string, paragraph_index inteiro >= 0 e text string")
        key = article_id, index
        if key in seen:
            raise ValueError(f"parágrafo duplicado: {key}")
        seen.add(key)
        prediction = {"article_id": article_id, "paragraph_index": index, "text": text,
                      "mentions": [], "teor": {},
                      "prediction_config": {"system": system,
                                            "include_party_descriptions": include_party_descriptions,
                                            "fuzzy_threshold": FUZZY_THRESHOLD}}
        output.append(prediction)
        articles.setdefault(article_id, []).append(prediction)
    person_pattern = _description_pattern(PERSON_DESCRIPTIONS)
    party_pattern = _description_pattern(PARTY_DESCRIPTIONS)
    for paragraphs in articles.values():
        last_any = last_person = last_party = None
        for paragraph in sorted(paragraphs, key=lambda p: p["paragraph_index"]):
            text = paragraph["text"]
            direct = (_production_mentions(text, entities) if system == "matcher"
                      else _experimental_mentions(text, entities))
            paragraph["mentions"] = direct.copy()
            if system == "matcher":
                continue
            events = [(m["start"], m["end"], "direct", m) for m in direct]
            events.extend((m.start(), m.end(), "pronoun", None) for m in _PRONOUN_RE.finditer(text))
            events.extend((m.start(), m.end(), "person", None) for m in person_pattern.finditer(text))
            if include_party_descriptions:
                events.extend((m.start(), m.end(), "party", None) for m in party_pattern.finditer(text))
            # Spans iguais de entidades diferentes são ambiguidades, sem
            # desempate arbitrário pela ordem da lista de entidades.
            groups = {}
            for event in events:
                groups.setdefault(event[0], []).append(event)
            for start, same_start in sorted(groups.items()):
                named = [event[3] for event in same_start if event[2] == "direct"]
                if named:
                    ids = {m["entity_id"] for m in named}
                    last_any = next(iter(ids)) if len(ids) == 1 else None
                    people = {eid for eid in ids if by_id[eid].entity_type in _PERSON_TYPES}
                    parties = ids - people
                    if people:
                        last_person = next(iter(people)) if len(people) == 1 else None
                    if parties:
                        last_party = next(iter(parties)) if len(parties) == 1 else None
                for _, end, kind, _ in same_start:
                    if kind == "direct" or any(m["start"] < end and start < m["end"] for m in direct):
                        continue
                    antecedent = {"pronoun": last_any, "person": last_person, "party": last_party}[kind]
                    if antecedent is not None:
                        paragraph["mentions"].append(_mention(text, start, end, antecedent, "IND"))
                        last_any = antecedent
            paragraph["mentions"].sort(key=lambda m: (m["start"], m["end"], m["entity_id"]))
    return output
