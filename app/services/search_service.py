"""Search service — orchestrates keyword expansion, source search, and deduplication."""

from __future__ import annotations

import hashlib
from typing import Any

from app.agent.schemas import RawLead
from app.core.logging import logger
from app.sources.mock_source import MockSourceAdapter
from app.sources.threads_source import ThreadsSourceAdapter
from app.sources.linkedin_source import LinkedInSourceAdapter

# Keyword expansion groups for MVP (static synonyms)
KEYWORD_GROUPS: dict[str, list[str]] = {
    "website": [
        "website", "web app", "web application", "company website",
        "web development", "jasa website", "bikin website", "buat website",
        "jasa web", "toko online", "landing page", "redesign web",
        "maintenance website", "company profile web", "portal web",
        "frontend", "backend", "fullstack",
    ],
    "managed_service": [
        "managed service", "managed IT", "IT managed service",
        "jasa managed service", "IT outsourcing", "IT support",
        "outsourcing IT", "IT maintenance", "server monitoring",
        "infrastructure monitoring", "NOC", "helpdesk", "technical support",
        "SLA support", "24/7 IT support", "jasa maintenance server",
        "manage cloud server", "remote sysadmin",
    ],
    "cloud_iaas": [
        "cloud", "IaaS", "cloud migration", "migrasi cloud", "AWS", "GCP",
        "Google Cloud", "Azure", "Alibaba Cloud", "VPS", "dedicated server",
        "setup VPS", "sewa server", "Kubernetes", "Docker", "DevOps",
        "sysadmin", "infrastructure as code", "Terraform", "server down",
    ],
    "saas": [
        "SaaS", "software as a service", "aplikasi berbasis cloud",
        "aplikasi subscription", "multi-tenant", "B2B SaaS", "micro saas",
        "cloud application", "langganan software",
    ],
    "cybersecurity": [
        "cybersecurity", "cyber security", "keamanan cyber", "pentest",
        "penetration testing", "uji penetrasi", "audit keamanan",
        "vulnerability assessment", "ISO 27001", "SOC", "hardening server",
        "security audit", "firewall", "data breach", "ransomware prevention",
    ],
    "data_analytics_bi": [
        "data analytics", "business intelligence", "BI", "dashboard BI",
        "Power BI", "Tableau", "data warehouse", "data engineering",
        "ETL", "reporting system", "dashboard KPI", "visualisasi data",
        "big data", "data pipeline",
    ],
    "erp": [
        "ERP", "enterprise resource planning", "sistem ERP",
        "software ERP", "aplikasi ERP", "custom ERP", "Odoo",
        "SAP", "ERP manufaktur", "ERP distribusi", "ERP retail",
    ],
    "crm": [
        "CRM", "customer relationship management", "sistem CRM",
        "aplikasi CRM", "pipeline sales", "leads tracking",
        "WhatsApp CRM", "omnichannel", "follow up leads",
    ],
    "hris": [
        "HRIS", "HR system", "human resource", "payroll",
        "sistem HR", "absensi", "attendance", "software payroll",
        "aplikasi HRD", "slip gaji", "sistem cuti", "KPI karyawan",
    ],
    "pos": [
        "POS", "point of sale", "kasir", "sistem kasir",
        "aplikasi kasir", "kasir online", "kasir restoran",
        "kasir retail", "printer thermal", "integrasi QRIS",
    ],
    "inventory": [
        "inventory", "stock management", "warehouse management",
        "sistem stok", "aplikasi gudang", "software inventory",
        "ERP inventory", "manajemen gudang", "tracking stok",
    ],
    "mobile": [
        "mobile app", "android app", "ios app", "aplikasi mobile",
        "aplikasi android", "aplikasi iOS", "flutter", "react native",
        "jasa bikin aplikasi hp", "developer mobile", "Play Store",
    ],
    "custom_software": [
        "custom software", "software house", "jasa pembuatan software",
        "jasa software", "bikin aplikasi custom", "sistem informasi",
        "aplikasi internal", "integrasi API", "web service",
        "jasa programmer", "software development agency",
    ],
    "automation": [
        "automation", "otomatisasi", "RPA", "workflow automation",
        "chatbot", "AI agent", "ChatGPT integration", "LLM",
        "bot WhatsApp", "n8n", "LangChain", "otomasi proses",
    ],
    "iot_embedded": [
        "IoT", "internet of things", "smart home", "telemetry",
        "sensor IoT", "SCADA", "tracking GPS", "fleet management",
        "monitoring sensor", "hardware integration",
    ],
    "network_infrastructure": [
        "jaringan kantor", "network infrastructure", "setting mikrotik",
        "cisco", "kabel LAN", "wifi kantor", "VPN kantor",
        "SD-WAN", "firewall mikrotik", "instalasi server",
    ],
    "ecommerce": [
        "ecommerce", "e-commerce", "toko online", "marketplace",
        "payment gateway", "Midtrans", "Xendit", "shopping cart",
        "katalog online",
    ],
    "intent_vendor": [
        "butuh jasa", "cari vendor", "rekomendasi vendor", "cari software house",
        "butuh developer", "hire programmer", "cari agency IT",
        "ada yang bisa bikinin", "tender IT", "project website",
        "butuh tim IT", "project software",
    ],
}

# Source adapter registry
SOURCE_REGISTRY: dict[str, Any] = {
    "mock": MockSourceAdapter(),
    "threads": ThreadsSourceAdapter(),
    "linkedin": LinkedInSourceAdapter(),
}


def expand_keywords(keywords: list[str]) -> list[str]:
    """Expand input keywords with related/synonym terms.

    Given ["butuh aplikasi inventory"], this might expand to include
    "stock management", "warehouse management", etc.

    Returns:
        Expanded list of unique keywords (original + related).
    """
    expanded = set()
    for kw in keywords:
        expanded.add(kw)
        kw_lower = kw.lower()
        for group_key, synonyms in KEYWORD_GROUPS.items():
            if group_key in kw_lower or any(s.lower() in kw_lower for s in synonyms):
                expanded.update(synonyms)

    result = list(expanded)
    if len(result) > len(keywords):
        logger.info(
            "Expanded %d keywords to %d (added %d synonyms)",
            len(keywords), len(result), len(result) - len(keywords),
        )
    return result


def _dedup_key(lead: RawLead) -> str:
    """Generate a deduplication key for a lead.

    Primary: source + source_url
    Fallback: hash(content + author + published_at)
    """
    if lead.source_url:
        return f"{lead.source}:{lead.source_url}"

    raw = f"{lead.content}:{lead.author_name}:{lead.published_at}"
    return hashlib.sha256(raw.encode()).hexdigest()


def deduplicate(leads: list[RawLead]) -> list[RawLead]:
    """Remove duplicate leads based on source + source_url."""
    seen: set[str] = set()
    unique: list[RawLead] = []

    for lead in leads:
        key = _dedup_key(lead)
        if key not in seen:
            seen.add(key)
            unique.append(lead)

    removed = len(leads) - len(unique)
    if removed > 0:
        logger.info("Deduplication: %d → %d (removed %d)", len(leads), len(unique), removed)

    return unique


async def search_sources(
    keywords: list[str],
    start_date: str,
    end_date: str,
    sources: list[str],
    limit: int,
) -> list[RawLead]:
    """Search configured sources for matching leads.

    Args:
        keywords: Expanded keyword list.
        start_date: ISO date string.
        end_date: ISO date string.
        sources: List of source adapter names to query.
        limit: Max results per source.

    Returns:
        Aggregated list of RawLead from all requested sources.
    """
    all_results: list[RawLead] = []

    for source_name in sources:
        adapter = SOURCE_REGISTRY.get(source_name)
        if adapter is None:
            logger.warning("Source '%s' not found in registry — skipping", source_name)
            continue

        try:
            results = await adapter.search(
                keywords=keywords,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )
            logger.info("Source '%s' returned %d results", source_name, len(results))
            all_results.extend(results)

        except Exception as e:
            logger.error("Source '%s' failed: %s", source_name, e)

    return all_results
