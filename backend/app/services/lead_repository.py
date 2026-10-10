"""Lead Repository — SQLite persistence layer for SALEP leads with RBAC status management."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.agent.schemas import LeadRecord, ScoreBreakdown, IntentType
from app.core.logging import logger
from app.services.scoring_service import calculate_score_breakdown

DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_PATH = DB_DIR / "salep_leads.db"


class LeadRepository:
    """Manages SQLite storage for all analyzed leads."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
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
                        notes TEXT,
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
            
            # Check if seeding is needed
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM leads")
            count = cur.fetchone()[0]
            if count == 0:
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
                INSERT INTO leads (
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
            cur.execute("SELECT lead_id, marketing_status, sales_status FROM leads WHERE lead_id = ? OR (source_url != '' AND source_url = ?)", (lead.lead_id, lead.source_url))
            existing = cur.fetchone()

            marketing_status = lead.marketing_status
            sales_status = lead.sales_status

            if existing:
                lead.lead_id = existing["lead_id"]
                marketing_status = existing["marketing_status"]
                sales_status = existing["sales_status"]
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
                        marketing_status, sales_status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(lead_id) DO UPDATE SET
                        content = excluded.content,
                        lead_score = excluded.lead_score,
                        confidence = excluded.confidence,
                        score_breakdown = excluded.score_breakdown,
                        marketing_status = excluded.marketing_status,
                        sales_status = excluded.sales_status,
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

    def update_marketing_status(self, lead_id: str, new_status: str) -> dict[str, Any] | None:
        """Update qualification status (valid, invalid, pending)."""
        clean_status = new_status.strip().lower()
        if clean_status not in {"valid", "invalid", "pending"}:
            raise ValueError(f"Invalid marketing status: {clean_status}")

        conn = self._get_connection()
        try:
            now_str = datetime.now(timezone.utc).isoformat()
            with conn:
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

    def update_sales_status(self, lead_id: str, new_status: str) -> dict[str, Any] | None:
        """Update sales follow-up status (e.g. Belum Dihubungi, Sedang Dihubungi, Closing, Batal)."""
        conn = self._get_connection()
        try:
            now_str = datetime.now(timezone.utc).isoformat()
            with conn:
                result = conn.execute(
                    """
                    UPDATE leads
                    SET sales_status = ?, updated_at = ?
                    WHERE lead_id = ? AND marketing_status = 'valid'
                    """,
                    (new_status.strip(), now_str, lead_id),
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
        for json_col in ("needs", "pain_points", "recommended_services", "evidence"):
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
        return d


lead_repository = LeadRepository()
