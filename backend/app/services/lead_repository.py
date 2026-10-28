"""Lead Repository — SQLite persistence layer for SALEP leads with RBAC status management."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.agent.schemas import LeadRecord, ScoreBreakdown, IntentType
from app.core.config import settings
from app.core.logging import logger
from app.services.scoring_service import calculate_score_breakdown
from app.services.lead_merge import scraped_lead_changes

DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_PATH = DB_DIR / "salep_leads.db"


class LeadRepository:
    """Manages SQLite storage for all analyzed leads."""

    def __init__(self, db_path: Path = DB_PATH, *, seed_samples: bool = True):
        self.db_path = db_path
        self.seed_samples = seed_samples
        self._ensure_db()

    def _get_connection(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_db(self) -> None:
        """Create tables if not existing and seed sample leads if empty."""
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS leads (
                        lead_id TEXT PRIMARY KEY,
                        source TEXT NOT NULL,
                        source_url TEXT NOT NULL,
                        author_name TEXT,
                        author_profile_url TEXT,
                        published_at TEXT,
                        matched_keyword TEXT,
                        content TEXT NOT NULL,
                        is_potential_lead INTEGER NOT NULL DEFAULT 0,
                        intent TEXT NOT NULL,
                        industry TEXT,
                        needs TEXT,
                        pain_points TEXT,
                        recommended_services TEXT,
                        lead_score INTEGER NOT NULL DEFAULT 0,
                        confidence REAL NOT NULL DEFAULT 0.0,
                        evidence TEXT,
                        score_breakdown TEXT,
                        analyzed_at TEXT NOT NULL,
                        marketing_status TEXT NOT NULL DEFAULT 'pending',
                        sales_status TEXT NOT NULL DEFAULT 'Belum Dihubungi',
                        sales_status_logs TEXT NOT NULL DEFAULT '[]',
                        notes TEXT,
                        marketing_reviewed_by_user_id TEXT,
                        marketing_reviewed_by_username TEXT,
                        marketing_reviewed_at TEXT,
                        marketing_review_note TEXT,
                        canonical_post_id TEXT,
                        deterministic_relevance_score INTEGER NOT NULL DEFAULT 0,
                        deterministic_relevance_label TEXT NOT NULL DEFAULT 'unreviewed',
                        deterministic_relevance_reason TEXT,
                        spam_label TEXT NOT NULL DEFAULT 'unknown',
                        spam_score INTEGER NOT NULL DEFAULT 0,
                        is_spam INTEGER NOT NULL DEFAULT 0,
                        quality_flags TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_leads_mkt_status ON leads(marketing_status)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(lead_score)"
                )
                # Existing local databases predate the quality columns. Keep
                # the adapter backwards compatible while PostgreSQL uses the
                # Alembic migration.
                existing_columns = {row[1] for row in conn.execute("PRAGMA table_info(leads)").fetchall()}
                additions = {
                    "canonical_post_id": "TEXT",
                    "deterministic_relevance_score": "INTEGER NOT NULL DEFAULT 0",
                    "deterministic_relevance_label": "TEXT NOT NULL DEFAULT 'unreviewed'",
                    "deterministic_relevance_reason": "TEXT",
                    "spam_label": "TEXT NOT NULL DEFAULT 'unknown'",
                    "spam_score": "INTEGER NOT NULL DEFAULT 0",
                    "is_spam": "INTEGER NOT NULL DEFAULT 0",
                    "quality_flags": "TEXT",
                    "sales_status_logs": "TEXT NOT NULL DEFAULT '[]'",
                    "marketing_reviewed_by_user_id": "TEXT",
                    "marketing_reviewed_by_username": "TEXT",
                    "marketing_reviewed_at": "TEXT",
                    "marketing_review_note": "TEXT",
                }
                for column, definition in additions.items():
                    if column not in existing_columns:
                        conn.execute(f"ALTER TABLE leads ADD COLUMN {column} {definition}")
            
            if not self.seed_samples:
                return

            # Check if seeding or SPSE seeding is needed
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM leads WHERE source='spse'")
            spse_count = cur.fetchone()[0]
            if spse_count == 0:
                self._seed_sample_leads(conn)
        finally:
            conn.close()

    def _seed_sample_leads(self, conn: sqlite3.Connection) -> None:
        """Seed realistic sample leads for immediate RBAC demonstration."""
        sample_records: list[dict[str, Any]] = [
            {
                "lead_id": "lead_demo_001",
                "source": "threads",
                "source_url": "https://www.threads.net/@brian_wibowo/post/DEMO001",
                "author_name": "Brian Wibowo",
                "author_profile_url": "https://www.threads.net/@brian_wibowo",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "matched_keyword": "vendor software ERP",
                "content": "Ada rekomendasi software house atau vendor yang bisa develop sistem ERP kustom dan integrasi web toko online? Bisnis retail fashion kami sudah 4 cabang dan mulai kewalahan rekap manual.",
                "is_potential_lead": 1,
                "intent": "looking_for_vendor",
                "industry": "retail_fashion",
                "needs": ["Sistem ERP Multi-Cabang", "Integrasi Website Toko Online", "Manajemen Stok Otomatis"],
                "pain_points": ["Pencatatan manual tidak efisien", "Selisih stok antar 4 cabang", "Kewalahan rekap bulanan"],
                "recommended_services": [
                    {"product_id": "svc-001", "product_name": "Custom Software Development", "match_score": 95, "reason": "Kebutuhan sistem ERP kustom terdistribusi."},
                    {"product_id": "svc-002", "product_name": "E-Commerce Website Integration", "match_score": 90, "reason": "Integrasi portal web toko online dengan database pusat."}
                ],
                "lead_score": 93,
                "confidence": 0.94,
                "evidence": ["mencari software house", "develop sistem ERP", "integrasi web toko online"],
                "marketing_status": "valid",
                "sales_status": "Belum Dihubungi",
                "notes": "Prioritas tinggi — prospek siap implementasi.",
            },
            {
                "lead_id": "lead_demo_002",
                "source": "linkedin",
                "source_url": "https://www.linkedin.com/feed/update/urn:li:activity:DEMO002",
                "author_name": "Dimas Pratama",
                "author_profile_url": "https://www.linkedin.com/in/dimas-pratama-demo",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "matched_keyword": "jasa website company profile",
                "content": "Perusahaan kami sedang mencari digital agency untuk redesign website company profile B2B & implementasi landing page lead generation. Butuh vendor berpengalaman dengan portofolio terpercaya.",
                "is_potential_lead": 1,
                "intent": "requesting_recommendation",
                "industry": "corporate_services",
                "needs": ["Redesign Website Corporate", "Landing Page Lead Gen", "SEO & Performance Optimization"],
                "pain_points": ["Tampilan website lama ketinggalan zaman", "Konversi lead online rendah"],
                "recommended_services": [
                    {"product_id": "svc-003", "product_name": "Corporate Web Development", "match_score": 92, "reason": "Redesign website corporate profesional."},
                    {"product_id": "svc-004", "product_name": "High-Converting Landing Pages", "match_score": 88, "reason": "Optimasi penangkapan prospek B2B."}
                ],
                "lead_score": 88,
                "confidence": 0.91,
                "evidence": ["mencari digital agency", "redesign website company profile", "butuh vendor berpengalaman"],
                "marketing_status": "valid",
                "sales_status": "Sedang Dihubungi",
                "notes": "Sudah dikirim company deck via LinkedIn DM.",
            },
            {
                "lead_id": "lead_demo_003",
                "source": "threads",
                "source_url": "https://www.threads.net/@sarah_kuliner/post/DEMO003",
                "author_name": "Sarah Oktavia",
                "author_profile_url": "https://www.threads.net/@sarah_kuliner",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "matched_keyword": "aplikasi kasir POS",
                "content": "Stok bahan baku di dapur resto sering selisih pas rekap akhir bulan. Ada yang punya saran software kasir / inventory resto yang user friendly? Capek banget rekap nota satu-satu.",
                "is_potential_lead": 1,
                "intent": "problem_identification",
                "industry": "food_and_beverage",
                "needs": ["Sistem Kasir POS Resto", "Pencatatan Bahan Baku Real-Time"],
                "pain_points": ["Stok sering selisih", "Rekap nota manual memakan waktu"],
                "recommended_services": [
                    {"product_id": "svc-005", "product_name": "POS & Restaurant Management", "match_score": 85, "reason": "Solusi otomatisasi kasir dan inventory F&B."}
                ],
                "lead_score": 68,
                "confidence": 0.84,
                "evidence": ["stok bahan baku selisih", "butuh saran software kasir inventory"],
                "marketing_status": "pending",
                "sales_status": "Belum Dihubungi",
                "notes": "Marketing perlu review sebelum dikirim ke Sales.",
            },
            {
                "lead_id": "lead_demo_004",
                "source": "threads",
                "source_url": "https://www.threads.net/@fikri_tech/post/DEMO004",
                "author_name": "Fikri Maulana",
                "author_profile_url": "https://www.threads.net/@fikri_tech",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "matched_keyword": "bikin aplikasi mobile",
                "content": "Teman-teman pengusaha, biasanya kalau develop MVP aplikasi mobile e-commerce awal mending hire freelancer apa pakai software agency ya? Kira-kira kisaran biayanya berapa?",
                "is_potential_lead": 1,
                "intent": "evaluating_solution",
                "industry": "startup_retail",
                "needs": ["Pengembangan Mobile App MVP", "Konsultasi Estimasi Biaya Software"],
                "pain_points": ["Ragu antara freelancer vs agency", "Belum tahu standar estimasi biaya"],
                "recommended_services": [
                    {"product_id": "svc-006", "product_name": "Mobile App MVP Development", "match_score": 80, "reason": "Pengembangan aplikasi Flutter/React Native awal."}
                ],
                "lead_score": 70,
                "confidence": 0.82,
                "evidence": ["develop MVP aplikasi mobile", "agency vs freelancer", "kisaran biaya"],
                "marketing_status": "pending",
                "sales_status": "Belum Dihubungi",
                "notes": "Potensi klien konsultasi pembuatan aplikasi.",
            },
            {
                "lead_id": "lead_demo_005",
                "source": "linkedin",
                "source_url": "https://www.linkedin.com/feed/update/urn:li:activity:DEMO005",
                "author_name": "Rian Ardiansyah",
                "author_profile_url": "https://www.linkedin.com/in/rian-ardiansyah-demo",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "matched_keyword": "jasa programmer web",
                "content": "Open to work! Halo koneksi LinkedIn, saya fresh graduate Teknik Informatika sedang mencari peluang kerja sebagai Junior Web Developer / Frontend Engineer (React, Vue, Tailwind).",
                "is_potential_lead": 0,
                "intent": "job_seeking",
                "industry": None,
                "needs": [],
                "pain_points": [],
                "recommended_services": [],
                "lead_score": 0,
                "confidence": 0.99,
                "evidence": ["open to work", "mencari peluang kerja"],
                "marketing_status": "invalid",
                "sales_status": "Batal",
                "notes": "Pencari kerja, bukan calon klien B2B.",
            },
            {
                "lead_id": "lead_spse_001",
                "source": "spse",
                "source_url": "https://spse.inaproc.id/nasional/lelang/8553802/pengumumanlelang",
                "author_name": "Kementerian Komunikasi dan Informatika",
                "author_profile_url": "https://spse.inaproc.id/nasional",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "matched_keyword": "cloud infrastructure managed service",
                "content": "Nama paket: Pengadaan Layanan Cloud Infrastructure dan Managed Services Server\nTahap tender saat ini: Upload Dokumen Penawaran\nInstansi: Kementerian Komunikasi dan Informatika\nNilai HPS: Rp. 485.000.000,00\nDetail: Pascakualifikasi Dua File | Tender | Harga Terendah Ambang Batas | Jasa Lainnya - TA 2026",
                "is_potential_lead": 1,
                "intent": "looking_for_vendor",
                "industry": "government_it",
                "needs": ["Cloud Infrastructure Managed Services", "Server 24/7 Monitoring", "SLA Support Enterprise"],
                "pain_points": ["Tenggat waktu upload dokumen ketat", "Persyaratan teknis kepatuhan ISO 27001"],
                "recommended_services": [
                    {"product_id": "svc-001", "product_name": "Cloud Managed Services", "match_score": 95, "reason": "Sesuai spesifikasi pengadaan cloud pemerintah."}
                ],
                "lead_score": 92,
                "confidence": 0.95,
                "evidence": ["Pengadaan Cloud Infrastructure", "Nilai HPS Rp 485 Jt", "Tahap Upload Dokumen Penawaran"],
                "marketing_status": "valid",
                "sales_status": "Belum Dihubungi",
                "notes": "Tender aktif — dokumen penawaran perlu disiapkan tim proposal sales.",
            },
            {
                "lead_id": "lead_spse_002",
                "source": "spse",
                "source_url": "https://spse.inaproc.id/nasional/lelang/8553803/pengumumanlelang",
                "author_name": "Dinas Komunikasi, Informatika dan Statistik",
                "author_profile_url": "https://spse.inaproc.id/nasional",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "matched_keyword": "pengembangan aplikasi portal web",
                "content": "Nama paket: Pengembangan Aplikasi Portal Satu Data dan Pemeliharaan Database\nTahap tender saat ini: Pemberian Penjelasan (Aanwijzing)\nInstansi: Dinas Komunikasi, Informatika dan Statistik\nNilai HPS: Rp. 320.000.000,00\nDetail: Pascakualifikasi Satu File | Tender Cepat | Jasa Lainnya - TA 2026",
                "is_potential_lead": 1,
                "intent": "looking_for_vendor",
                "industry": "government_it",
                "needs": ["Aplikasi Web Satu Data", "Integrasi Database Terpusat", "Visualisasi Dashboard Interaktif"],
                "pain_points": ["Data lintas dinas terpecah-pecah", "Perlu integrasi API antar instansi"],
                "recommended_services": [
                    {"product_id": "svc-002", "product_name": "Custom Software & Web Portal", "match_score": 90, "reason": "Solusi portal data pemerintah daerah."}
                ],
                "lead_score": 88,
                "confidence": 0.92,
                "evidence": ["Aplikasi Portal Satu Data", "Tahap Pemberian Penjelasan", "Nilai HPS Rp 320 Jt"],
                "marketing_status": "valid",
                "sales_status": "Sedang Dihubungi",
                "notes": "Tim teknis sedang menyiapkan pertanyaan untuk sesi aanwijzing.",
            },
        ]

        now_str = datetime.now(timezone.utc).isoformat()
        for rec in sample_records:
            # Build score breakdown
            score: int = int(rec.get("lead_score", 0))
            intent_val: str = str(rec.get("intent") or "")
            needs: list[str] = list(rec.get("needs") or [])
            pain_points: list[str] = list(rec.get("pain_points") or [])
            confidence: float = float(rec.get("confidence", 0.0))

            intent_score = 40 if intent_val == "looking_for_vendor" else (35 if intent_val == "requesting_recommendation" else (30 if intent_val == "evaluating_solution" else (20 if intent_val == "problem_identification" else 0)))
            clarity_score = min(20, len(needs) * 5 + len(pain_points) * 5)
            rel_score = 20 if intent_score >= 30 else (10 if intent_score > 0 else 0)
            fit_score = max(0, score - (intent_score + clarity_score + rel_score))
            ai_conf_pct = round(confidence * 100)

            breakdown = {
                "intent_score": intent_score,
                "intent_max": 40,
                "intent_name": intent_val.replace("_", " ").title(),
                "intent_explanation": f"Intent klasifikasi '{intent_val}' menghasilkan bobot {intent_score}/40 poin.",
                "problem_clarity_score": clarity_score,
                "problem_clarity_max": 20,
                "problem_clarity_explanation": f"Terdeteksi {len(needs)} kebutuhan dan {len(pain_points)} kendala operasional ({clarity_score}/20 poin).",
                "it_relevance_score": rel_score,
                "it_relevance_max": 20,
                "it_relevance_explanation": f"Domain kebutuhan selaras dengan jasa software IT ({rel_score}/20 poin).",
                "product_fit_score": fit_score,
                "product_fit_max": 20,
                "product_fit_explanation": f"Kesesuaian dengan katalog layanan SALEP ({fit_score}/20 poin).",
                "total_score": score,
                "ai_confidence": confidence,
                "ai_confidence_pct": ai_conf_pct,
                "ai_confidence_explanation": f"Tingkat kepastian ekstraksi AI sebesar {ai_conf_pct}% dari postingan.",
                "formula_summary": f"{intent_score} (Intent) + {clarity_score} (Kejelasan) + {rel_score} (Relevansi IT) + {fit_score} (Fit) = {score}/100"
            }

            conn.execute(
                """
                INSERT OR REPLACE INTO leads (
                    lead_id, source, source_url, author_name, author_profile_url,
                    published_at, matched_keyword, content, is_potential_lead,
                    intent, industry, needs, pain_points, recommended_services,
                    lead_score, confidence, evidence, score_breakdown, analyzed_at,
                    marketing_status, sales_status, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec["lead_id"],
                    rec["source"],
                    rec["source_url"],
                    rec["author_name"],
                    rec["author_profile_url"],
                    rec["published_at"],
                    rec["matched_keyword"],
                    rec["content"],
                    rec["is_potential_lead"],
                    rec["intent"],
                    rec["industry"],
                    json.dumps(rec["needs"]),
                    json.dumps(rec["pain_points"]),
                    json.dumps(rec["recommended_services"]),
                    rec["lead_score"],
                    rec["confidence"],
                    json.dumps(rec["evidence"]),
                    json.dumps(breakdown),
                    now_str,
                    rec["marketing_status"],
                    rec["sales_status"],
                    rec["notes"],
                    now_str,
                    now_str,
                )
            )
        conn.commit()
        logger.info("Seeded %d realistic sample leads for SALEP RBAC", len(sample_records))

    def save_lead(self, lead: LeadRecord, default_status: str | None = None) -> dict[str, Any]:
        """Insert or update a lead in SQLite."""
        conn = self._get_connection()
        now_str = datetime.now(timezone.utc).isoformat()
        try:
            # Check existing status if already in DB
            cur = conn.cursor()
            cur.execute(
                """SELECT * FROM leads
                   WHERE lead_id = ? OR (source_url != '' AND source_url = ?)
                   OR (source = 'threads' AND canonical_post_id IS NOT NULL AND canonical_post_id = ?)""",
                (lead.lead_id, lead.source_url, lead.canonical_post_id),
            )
            existing = cur.fetchone()

            marketing_status = lead.marketing_status
            sales_status = lead.sales_status

            if existing:
                lead.lead_id = existing["lead_id"]
                changes = scraped_lead_changes(dict(existing), lead.model_dump(mode='json'))
                if changes:
                    json_fields = {'needs', 'pain_points', 'recommended_services', 'evidence', 'score_breakdown', 'quality_flags'}
                    values = {key: json.dumps(value) if key in json_fields and value is not None else value for key, value in changes.items()}
                    values['updated_at'] = now_str
                    with conn:
                        conn.execute(
                            'UPDATE leads SET ' + ', '.join(f'{key} = ?' for key in values) + ' WHERE lead_id = ?',
                            [*values.values(), lead.lead_id],
                        )
                return self.get_lead(lead.lead_id) or {}
            elif default_status:
                marketing_status = default_status
            breakdown_dict = None
            if lead.score_breakdown:
                breakdown_dict = lead.score_breakdown.model_dump()

            with conn:
                conn.execute(
                    """
                    INSERT INTO leads (
                        lead_id, source, source_url, author_name, author_profile_url,
                        published_at, matched_keyword, content, is_potential_lead,
                        intent, industry, needs, pain_points, recommended_services,
                        lead_score, confidence, evidence, score_breakdown, analyzed_at,
                        marketing_status, sales_status, canonical_post_id,
                        deterministic_relevance_score, deterministic_relevance_label,
                        deterministic_relevance_reason, spam_label, spam_score, is_spam,
                        quality_flags, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(lead_id) DO UPDATE SET
                        content = excluded.content,
                        lead_score = excluded.lead_score,
                        confidence = excluded.confidence,
                        score_breakdown = excluded.score_breakdown,
                        marketing_status = excluded.marketing_status,
                        sales_status = excluded.sales_status,
                        canonical_post_id = excluded.canonical_post_id,
                        deterministic_relevance_score = excluded.deterministic_relevance_score,
                        deterministic_relevance_label = excluded.deterministic_relevance_label,
                        deterministic_relevance_reason = excluded.deterministic_relevance_reason,
                        spam_label = excluded.spam_label,
                        spam_score = excluded.spam_score,
                        is_spam = excluded.is_spam,
                        quality_flags = excluded.quality_flags,
                        updated_at = excluded.updated_at
                    """,
                    (
                        lead.lead_id,
                        lead.source,
                        lead.source_url,
                        lead.author_name,
                        lead.author_profile_url,
                        lead.published_at.isoformat() if lead.published_at else None,
                        lead.matched_keyword,
                        lead.content,
                        1 if lead.is_potential_lead else 0,
                        lead.intent.value if hasattr(lead.intent, "value") else str(lead.intent),
                        lead.industry,
                        json.dumps(lead.needs),
                        json.dumps(lead.pain_points),
                        json.dumps([s.model_dump() for s in lead.recommended_services]),
                        lead.lead_score,
                        lead.confidence,
                        json.dumps(lead.evidence),
                        json.dumps(breakdown_dict) if breakdown_dict else None,
                        lead.analyzed_at.isoformat() if lead.analyzed_at else now_str,
                        marketing_status,
                        sales_status,
                        lead.canonical_post_id,
                        lead.deterministic_relevance_score,
                        lead.deterministic_relevance_label,
                        lead.deterministic_relevance_reason,
                        lead.spam_label,
                        lead.spam_score,
                        1 if lead.is_spam else 0,
                        json.dumps(lead.quality_flags),
                        now_str,
                        now_str,
                    )
                )
            return self.get_lead(lead.lead_id) or {}
        finally:
            conn.close()

    def _lead_filter_query(
        self,
        role: str,
        status: str,
        search: str,
        sales_status: str,
        source: str,
    ) -> tuple[str, list[Any]]:
        """Build the shared filtered query used by list and count operations."""

        if role not in {"marketing", "sales"}:
            raise ValueError("Unknown role")

        conditions = []
        params: list[Any] = []

        if role.lower() == "sales":
            conditions.append("marketing_status = 'valid'")
        elif status and status.lower() != "all":
            conditions.append("marketing_status = ?")
            params.append(status.lower())

        if sales_status != "all":
            conditions.append("sales_status = ?")
            params.append(sales_status)

        if source != "all":
            conditions.append("source = ?")
            params.append(source)

        if search:
            kw = f"%{search.strip()}%"
            conditions.append(
                "(content LIKE ? OR author_name LIKE ? OR needs LIKE ? OR matched_keyword LIKE ?)"
            )
            params.extend([kw, kw, kw, kw])

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        return where_clause, params

    def get_leads(
        self,
        role: str = "marketing",
        status: str = "all",
        search: str = "",
        limit: int = 50,
        offset: int = 0,
        sales_status: str = "all",
        source: str = "all",
    ) -> list[dict[str, Any]]:
        """Retrieve leads matching role permissions and optional query filters."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            conditions = []
            params: list[Any] = []

            # RBAC Enforcement: Sales role only sees valid leads
            if role.lower() == "sales":
                conditions.append("marketing_status = 'valid'")
            else:
                if status and status.lower() != "all":
                    conditions.append("marketing_status = ?")
                    params.append(status.lower())

            if sales_status != "all":
                conditions.append("sales_status = ?")
                params.append(sales_status)

            if source == "social_media":
                conditions.append("LOWER(source) IN ('threads', 'linkedin')")
            elif source != "all":
                conditions.append("source = ?")
                params.append(source)

            if search:
                kw = f"%{search.strip()}%"
                conditions.append(
                    "(content LIKE ? OR author_name LIKE ? OR needs LIKE ? OR matched_keyword LIKE ?)"
                )
                params.extend([kw, kw, kw, kw])

            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)

            query = f"""
                SELECT * FROM leads
                {where_clause}
                ORDER BY analyzed_at DESC, lead_score DESC, lead_id
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])

            cur.execute(query, params)
            rows = cur.fetchall()
            return [self._row_to_dict(r) for r in rows]
        finally:
            conn.close()

    def count_leads(
        self,
        role: str = "marketing",
        status: str = "all",
        search: str = "",
        sales_status: str = "all",
        source: str = "all",
    ) -> int:
        """Count leads using exactly the same RBAC and filters as get_leads."""

        conn = self._get_connection()
        try:
            where_clause, params = self._lead_filter_query(
                role=role,
                status=status,
                search=search,
                sales_status=sales_status,
                source=source,
            )
            row = conn.execute(
                f"SELECT COUNT(*) FROM leads {where_clause}",
                params,
            ).fetchone()
            return int(row[0])
        finally:
            conn.close()

    def get_lead(self, lead_id: str) -> dict[str, Any] | None:
        """Fetch a single lead by ID."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM leads WHERE lead_id = ?", (lead_id,))
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_dict(row)
        finally:
            conn.close()

    def delete_lead(self, lead_id: str) -> bool:
        """Delete a lead from the local database."""
        conn = self._get_connection()
        try:
            with conn:
                result = conn.execute(
                    "DELETE FROM leads WHERE lead_id = ?",
                    (lead_id,),
                )
            return result.rowcount > 0
        finally:
            conn.close()

    def update_marketing_status(
        self,
        lead_id: str,
        new_status: str,
        *,
        reviewed_by_user_id: str | None = None,
        reviewed_by_username: str | None = None,
        review_note: str | None = None,
        **_: Any,
    ) -> dict[str, Any] | None:
        """Update qualification status (valid, invalid, pending)."""
        clean_status = new_status.strip().lower()
        if clean_status not in {"valid", "invalid", "pending"}:
            raise ValueError(f"Invalid marketing status: {clean_status}")

        conn = self._get_connection()
        try:
            now_str = datetime.now(timezone.utc).isoformat()
            with conn:
                if reviewed_by_user_id:
                    conn.execute(
                        """
                        UPDATE leads
                        SET marketing_status = ?, marketing_reviewed_by_user_id = ?,
                            marketing_reviewed_by_username = ?, marketing_reviewed_at = ?,
                            marketing_review_note = ?, updated_at = ?
                        WHERE lead_id = ?
                        """,
                        (clean_status, reviewed_by_user_id, reviewed_by_username, now_str, review_note, now_str, lead_id),
                    )
                else:
                    conn.execute(
                        """
                        UPDATE leads
                        SET marketing_status = ?, updated_at = ?
                        WHERE lead_id = ?
                        """,
                        (clean_status, now_str, lead_id),
                    )
            return self.get_lead(lead_id)
        finally:
            conn.close()

    def update_sales_status(
        self,
        lead_id: str,
        new_status: str,
        note: str,
        changed_by: str | None = None,
    ) -> dict[str, Any] | None:
        """Update sales follow-up status and append a timestamped note."""
        conn = self._get_connection()
        try:
            now = datetime.now(timezone.utc)
            now_str = now.isoformat()
            row = conn.execute(
                "SELECT sales_status, marketing_status, sales_status_logs FROM leads WHERE lead_id = ?",
                (lead_id,),
            ).fetchone()
            if not row or row["marketing_status"] != "valid":
                return None
            try:
                logs = json.loads(row["sales_status_logs"] or "[]")
            except (TypeError, json.JSONDecodeError):
                logs = []
            logs.append({
                "id": uuid.uuid4().hex,
                "from_status": row["sales_status"],
                "to_status": new_status.strip(),
                "note": note.strip(),
                "changed_by": changed_by,
                "changed_at": now_str,
            })
            with conn:
                result = conn.execute(
                    """
                    UPDATE leads
                    SET sales_status = ?, sales_status_logs = ?, updated_at = ?
                    WHERE lead_id = ? AND marketing_status = 'valid'
                    """,
                    (new_status.strip(), json.dumps(logs), now_str, lead_id),
                )
            if result.rowcount == 0:
                return None
            return self.get_lead(lead_id)
        finally:
            conn.close()

    def get_stats(self) -> dict[str, int]:
        """Return counts for dashboard metrics."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM leads")
            total = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM leads WHERE marketing_status = 'valid'")
            valid = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM leads WHERE marketing_status = 'pending'")
            pending = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM leads WHERE marketing_status = 'invalid'")
            invalid = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM leads WHERE marketing_status = 'valid' AND sales_status = 'Belum Dihubungi'")
            sales_new = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM leads WHERE marketing_status = 'valid' AND sales_status = 'Sedang Dihubungi'")
            sales_in_progress = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM leads WHERE marketing_status = 'valid' AND sales_status = 'Closing'")
            sales_closed = cur.fetchone()[0]

            return {
                "total": total,
                "valid": valid,
                "pending": pending,
                "invalid": invalid,
                "sales_new": sales_new,
                "sales_in_progress": sales_in_progress,
                "sales_closed": sales_closed,
            }
        finally:
            conn.close()

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        """Convert SQLite row to rich dictionary with parsed JSON fields."""
        d = dict(row)
        for json_col in ("needs", "pain_points", "recommended_services", "evidence", "quality_flags", "sales_status_logs"):
            if d.get(json_col):
                try:
                    d[json_col] = json.loads(d[json_col])
                except Exception:
                    d[json_col] = []
            else:
                d[json_col] = []

        if d.get("score_breakdown"):
            try:
                d["score_breakdown"] = json.loads(d["score_breakdown"])
            except Exception:
                d["score_breakdown"] = None
        else:
            d["score_breakdown"] = None

        d["is_potential_lead"] = bool(d.get("is_potential_lead", 0))
        d["is_spam"] = bool(d.get("is_spam", 0))
        return d


def build_lead_repository() -> Any:
    """Select persistence backend without breaking the SQLite test adapter.

    Production enables PostgreSQL by setting DATABASE_URL. The migration is
    intentionally opt-in so existing local/test SQLite workflows remain
    deterministic until `alembic upgrade head` has been run.
    """

    if settings.database_url.strip():
        from app.db.lead_repository import SqlAlchemyLeadRepository

        return SqlAlchemyLeadRepository(
            settings.database_url,
            create_schema=settings.database_auto_create,
        )
    return LeadRepository()


lead_repository = build_lead_repository()
