"""Deterministic quality controls for Threads leads.

The gate runs before an LLM is called.  It is intentionally explainable and
stable so a search can be replayed, evaluated against a golden set, and
debugged without depending on model output.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit

from app.agent.schemas import RawLead


IT_TERMS: tuple[str, ...] = (
    "server", "hosting", "vps", "cloud", "aws", "azure", "gcp", "website",
    "web app", "aplikasi", "software", "erp", "crm", "hris", "pos", "database",
    "jaringan", "network", "wifi", "vpn", "firewall", "backup", "keamanan",
    "cybersecurity", "pentest", "data center", "devops", "docker", "kubernetes",
    "it support", "managed service", "maintenance", "integrasi api", "otomasi",
    "dashboard", "sistem informasi", "infrastruktur", "virtual machine",
)

BUYING_INTENT_TERMS: tuple[str, ...] = (
    "butuh", "membutuhkan", "cari", "mencari", "rekomendasi", "vendor", "penyedia",
    "jasa", "hire", "sewa", "pengadaan", "tender", "quotation", "penawaran",
    "ada yang bisa", "siapa yang bisa", "looking for", "need", "recommend",
    "provider", "outsource", "outsourcing", "project", "budget",
)

NEGATIVE_INTENT_TERMS: tuple[str, ...] = (
    "belajar", "tutorial", "kursus", "lowongan", "loker", "open to work", "resume",
    "portfolio", "tips", "tutorial", "cara membuat", "dokumentasi", "berita",
    "opini", "diskusi umum",
)

SPAM_TERMS: tuple[str, ...] = (
    "giveaway", "airdrop", "casino", "judi", "slot gacor", "crypto gratis", "investasi pasti",
    "diskon 99%", "promo terbatas", "klik link", "cuan cepat", "jual followers", "jual akun",
    "free iphone", "hadiah jutaan",
)

FAKE_TERMS: tuple[str, ...] = (
    "open to work", "available for hire", "freelance developer", "jasa saya", "hubungi saya",
    "dm for collab", "dm me", "kontak saya",
)


def _norm(value: str | None) -> str:
    text = unicodedata.normalize("NFKC", value or "").casefold()
    return re.sub(r"\s+", " ", text).strip()


def canonicalize_threads_url(url: str | None) -> str:
    """Return a stable Threads URL with query strings/fragments removed."""
    if not url:
        return ""
    try:
        parsed = urlsplit(url.strip())
        if not parsed.netloc:
            return url.strip()
        host = parsed.netloc.casefold().removeprefix("www.")
        path = re.sub(r"/{2,}", "/", parsed.path or "/").rstrip("/") or "/"
        return urlunsplit(("https", host, path, "", ""))
    except Exception:
        return url.strip()


def canonical_threads_post_id(
    source_url: str | None,
    *,
    post_code: str | None = None,
    explicit_id: str | None = None,
    content: str = "",
    author_name: str | None = None,
    published_at: datetime | None = None,
) -> str:
    """Build a provider-independent stable identity for a Threads post.

    Apify actors expose different combinations of ``id``, ``postCode`` and
    URLs.  Prefer the provider ID, then the URL's post token, and only use a
    content fingerprint as a last resort for malformed/legacy records.
    """
    for value in (explicit_id, post_code):
        clean = _norm(str(value) if value is not None else "")
        if clean:
            if clean.startswith("threads:"):
                clean = clean.removeprefix("threads:")
            return f"threads:{clean}"

    url = canonicalize_threads_url(source_url)
    path = urlsplit(url).path if url else ""
    # Threads commonly uses /t/<code>, /post/<id>, or /@user/post/<id>.
    matches = re.findall(r"(?:^|/)(?:t|post)/([^/]+)", path, flags=re.I)
    if matches:
        return f"threads:{matches[-1].casefold()}"

    fingerprint = "|".join((_norm(content), _norm(author_name), published_at.isoformat() if published_at else ""))
    return "threads:hash:" + hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:32]


@dataclass(frozen=True)
class RelevanceDecision:
    score: int
    accepted: bool
    label: str
    reason: str
    signals: tuple[str, ...] = ()


@dataclass(frozen=True)
class SpamDecision:
    label: str
    score: int
    is_spam: bool
    reasons: tuple[str, ...] = ()


def _matches(text: str, terms: Iterable[str]) -> list[str]:
    return [term for term in terms if term in text]


def deterministic_relevance(content: str) -> RelevanceDecision:
    """Classify buying relevance using lexical signals only.

    A high-value post needs an IT signal and a buying/need signal.  Educational
    and job-seeking posts are rejected even when they mention technology.
    """
    text = _norm(content)
    it = _matches(text, IT_TERMS)
    intent = _matches(text, BUYING_INTENT_TERMS)
    negative = _matches(text, NEGATIVE_INTENT_TERMS)
    score = min(100, len(it) * 22 + len(intent) * 28 - len(negative) * 30)
    score = max(0, score)
    if not it:
        return RelevanceDecision(score, False, "irrelevant", "no_it_signal", tuple(intent + negative))
    if negative and not intent:
        return RelevanceDecision(score, False, "non_buying", "learning_or_job_context", tuple(it + negative))
    if intent and it:
        return RelevanceDecision(score, score >= 50, "relevant" if score >= 50 else "ambiguous", "it_and_buying_signals", tuple(it + intent))
    return RelevanceDecision(score, False, "ambiguous", "it_signal_without_buying_intent", tuple(it))


def classify_spam_or_fake(content: str, *, author_name: str | None = None, source_url: str | None = None) -> SpamDecision:
    text = _norm(content)
    url_text = _norm(source_url)
    spam = _matches(text, SPAM_TERMS)
    fake = _matches(text, FAKE_TERMS)
    reasons: list[str] = []
    score = 0
    if spam:
        score += min(80, 35 * len(spam))
        reasons.extend(f"spam:{term}" for term in spam)
    if fake:
        score += min(45, 25 * len(fake))
        reasons.extend(f"fake:{term}" for term in fake)
    if re.search(r"https?://(?:bit\.ly|tinyurl\.com|t\.co)/", f"{text} {url_text}"):
        score += 25
        reasons.append("shortened_url")
    if len(re.findall(r"#\w+", text)) >= 8:
        score += 15
        reasons.append("hashtag_burst")
    if not (author_name or "").strip():
        score += 10
        reasons.append("missing_author")
    score = min(100, score)
    if spam or score >= 70:
        return SpamDecision("suspected_spam", score, True, tuple(reasons))
    if fake or score >= 40:
        return SpamDecision("suspected_fake", score, True, tuple(reasons))
    return SpamDecision("genuine", score, False, tuple(reasons))


def apply_threads_quality_gate(raw: RawLead) -> RawLead | None:
    """Attach deterministic quality metadata and drop clear false positives."""
    relevance = deterministic_relevance(raw.content)
    spam = classify_spam_or_fake(raw.content, author_name=raw.author_name, source_url=raw.source_url)
    canonical_id = raw.canonical_post_id or canonical_threads_post_id(
        raw.source_url,
        content=raw.content,
        author_name=raw.author_name,
        published_at=raw.published_at,
    )
    flags = list(dict.fromkeys([
        *raw.quality_flags,
        *(f"relevance:{signal}" for signal in relevance.signals[:5]),
        *spam.reasons[:5],
    ]))
    enriched = raw.model_copy(update={
        "canonical_post_id": canonical_id,
        "deterministic_relevance_score": relevance.score,
        "deterministic_relevance_label": relevance.label,
        "deterministic_relevance_reason": relevance.reason,
        "spam_label": spam.label,
        "spam_score": spam.score,
        "is_spam": spam.is_spam,
        "quality_flags": flags,
    })
    # Keep ambiguous posts out of LLM spend, while preserving relevant posts
    # with imperfect wording for human review.
    if spam.is_spam or not relevance.accepted:
        return None
    return enriched


def evaluate_golden_set(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate gate decisions against a small labelled fixture."""
    rows = list(records)
    tp = fp = tn = fn = 0
    spam_tp = spam_fp = spam_tn = spam_fn = 0
    for row in rows:
        relevance = deterministic_relevance(str(row.get("content", ""))).accepted
        expected = bool(row.get("relevant", False))
        if relevance and expected: tp += 1
        elif relevance and not expected: fp += 1
        elif not relevance and expected: fn += 1
        else: tn += 1
        spam = classify_spam_or_fake(str(row.get("content", "")), author_name=row.get("author_name")).is_spam
        expected_spam = bool(row.get("spam", False))
        if spam and expected_spam: spam_tp += 1
        elif spam and not expected_spam: spam_fp += 1
        elif not spam and expected_spam: spam_fn += 1
        else: spam_tn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    spam_precision = spam_tp / (spam_tp + spam_fp) if spam_tp + spam_fp else 0.0
    spam_recall = spam_tp / (spam_tp + spam_fn) if spam_tp + spam_fn else 0.0
    return {
        "samples": len(rows),
        "relevance": {"tp": tp, "fp": fp, "tn": tn, "fn": fn, "precision": round(precision, 4), "recall": round(recall, 4)},
        "spam": {"tp": spam_tp, "fp": spam_fp, "tn": spam_tn, "fn": spam_fn, "precision": round(spam_precision, 4), "recall": round(spam_recall, 4)},
    }


def load_golden_set(path: str | Path) -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))

