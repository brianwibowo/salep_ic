"""Scoring service — deterministic lead scoring based on agent analysis."""

from app.agent.schemas import LeadAnalysis, IntentType, HIGH_VALUE_INTENTS, ScoreBreakdown


# Intent strength scores (0-40)
INTENT_SCORES: dict[IntentType, int] = {
    IntentType.LOOKING_FOR_VENDOR: 40,
    IntentType.REQUESTING_RECOMMENDATION: 35,
    IntentType.EVALUATING_SOLUTION: 30,
    IntentType.PROBLEM_IDENTIFICATION: 20,
    IntentType.GENERAL_DISCUSSION: 10,
    IntentType.LEARNING: 5,
    IntentType.JOB_SEEKING: 0,
    IntentType.IRRELEVANT: 0,
    IntentType.UNKNOWN: 5,
}

INTENT_DESCRIPTIONS: dict[IntentType, tuple[str, str]] = {
    IntentType.LOOKING_FOR_VENDOR: (
        "Mencari Vendor",
        "Calon klien secara aktif mencari vendor/jasa pengembang (bobot maksimal 40/40).",
    ),
    IntentType.REQUESTING_RECOMMENDATION: (
        "Minta Rekomendasi",
        "Calon klien meminta rekomendasi penyedia solusi atau agency (bobot tinggi 35/40).",
    ),
    IntentType.EVALUATING_SOLUTION: (
        "Evaluasi Solusi",
        "Calon klien aktif membandingkan opsi software atau vendor (bobot 30/40).",
    ),
    IntentType.PROBLEM_IDENTIFICATION: (
        "Identifikasi Masalah",
        "Menyampaikan kendala operasional bisnis tanpa eksplisit mencari vendor (bobot 20/40).",
    ),
    IntentType.GENERAL_DISCUSSION: (
        "Diskusi Umum",
        "Percakapan seputar industri teknologi tanpa sinyal pembelian langsung (bobot 10/40).",
    ),
    IntentType.LEARNING: (
        "Belajar / Edukasi",
        "Pengguna mencari materi pembelajaran/tutorial, bukan pembeli B2B (bobot 5/40).",
    ),
    IntentType.JOB_SEEKING: (
        "Mencari Kerja",
        "Pengguna mencari lowongan kerja atau magang, bukan calon klien (bobot 0/40).",
    ),
    IntentType.IRRELEVANT: (
        "Tidak Relevan",
        "Topik tidak terkait dengan domain layanan teknologi/bisnis (bobot 0/40).",
    ),
    IntentType.UNKNOWN: (
        "Tidak Teridentifikasi",
        "Pola intent belum dapat diklasifikasikan secara tegas (bobot 5/40).",
    ),
}


def calculate_score_breakdown(analysis: LeadAnalysis) -> ScoreBreakdown:
    """Calculate deterministic lead score with 100% transparency breakdown.

    Scoring dimensions:
      - Intent strength:  0–40
      - Problem clarity:  0–20
      - IT relevance:     0–20
      - Product fit:      0–20
      Total:              0–100
    """
    # 1. Intent strength (0-40)
    intent_score = INTENT_SCORES.get(analysis.intent, 5)
    intent_name, intent_desc = INTENT_DESCRIPTIONS.get(
        analysis.intent,
        ("Tidak Teridentifikasi", "Pola intent belum dapat diklasifikasikan secara tegas (bobot 5/40)."),
    )

    # 2. Problem clarity (0-20): based on extracted pain points and needs
    needs_count = len(analysis.needs)
    pain_count = len(analysis.pain_points)
    problem_clarity = min(20, (needs_count * 5) + (pain_count * 5))
    if needs_count + pain_count == 0:
        clarity_desc = "Tidak ada kebutuhan atau kendala spesifik yang terdeteksi (0/20 poin)."
    else:
        clarity_desc = (
            f"Terdeteksi {needs_count} kebutuhan spesifik ({needs_count * 5} poin) dan "
            f"{pain_count} kendala operasional ({pain_count * 5} poin), total bobot {problem_clarity}/20 poin."
        )

    # 3. IT relevance (0-20): high-value intents + having needs = IT relevant
    it_relevance = 0
    if analysis.intent in HIGH_VALUE_INTENTS:
        it_relevance = 15
    elif analysis.intent == IntentType.PROBLEM_IDENTIFICATION:
        it_relevance = 10
    elif analysis.intent == IntentType.GENERAL_DISCUSSION:
        it_relevance = 5

    if needs_count > 0:
        it_relevance = min(20, it_relevance + 5)

    if it_relevance >= 15:
        relevance_desc = f"Kebutuhan selaras tinggi dengan kapabilitas layanan software/digital agency ({it_relevance}/20 poin)."
    elif it_relevance > 0:
        relevance_desc = f"Kebutuhan memiliki korelasi menengah dengan domain teknologi ({it_relevance}/20 poin)."
    else:
        relevance_desc = "Konten tidak menunjukkan relevansi dengan proyek teknologi informasi (0/20 poin)."

    # 4. Product fit (0-20): based on recommended services and their match scores
    product_fit = 0
    if analysis.recommended_services:
        avg_match = sum(s.match_score for s in analysis.recommended_services) / len(
            analysis.recommended_services
        )
        product_fit = min(20, int(avg_match * 0.2))
        fit_desc = (
            f"Ditemukan {len(analysis.recommended_services)} layanan cocok dengan rata-rata kecocokan "
            f"{int(avg_match)}% ({product_fit}/20 poin)."
        )
    else:
        fit_desc = "Belum ada produk/layanan dalam katalog yang cocok secara langsung (0/20 poin)."

    total = min(100, max(0, intent_score + problem_clarity + it_relevance + product_fit))
    conf_pct = int(round(analysis.confidence * 100))
    conf_desc = (
        f"AI Gemini memiliki tingkat keyakinan ekstraksi {conf_pct}% "
        f"berdasarkan {len(analysis.evidence)} bukti kalimat prospek."
    )

    formula = (
        f"{intent_score} (Intent) + {problem_clarity} (Kejelasan) + "
        f"{it_relevance} (Relevansi IT) + {product_fit} (Kesesuaian Produk) = {total}/100"
    )

    return ScoreBreakdown(
        intent_score=intent_score,
        intent_max=40,
        intent_name=intent_name,
        intent_explanation=intent_desc,
        problem_clarity_score=problem_clarity,
        problem_clarity_max=20,
        problem_clarity_explanation=clarity_desc,
        it_relevance_score=it_relevance,
        it_relevance_max=20,
        it_relevance_explanation=relevance_desc,
        product_fit_score=product_fit,
        product_fit_max=20,
        product_fit_explanation=fit_desc,
        total_score=total,
        ai_confidence=analysis.confidence,
        ai_confidence_pct=conf_pct,
        ai_confidence_explanation=conf_desc,
        formula_summary=formula,
    )


def calculate_lead_score(analysis: LeadAnalysis) -> int:
    """Calculate deterministic lead score from AI analysis.

    Returns:
        Score between 0 and 100.
    """
    breakdown = calculate_score_breakdown(analysis)
    return breakdown.total_score
