"""Mock source adapter — generates realistic dummy data for development and testing."""

from __future__ import annotations

import random
from datetime import datetime

from app.agent.schemas import RawLead

MOCK_POSTS = [
    {
        "content": "Ada rekomendasi vendor yang bisa bikin aplikasi inventory? Bisnis kami masih menggunakan Excel dan mulai kesulitan tracking stok beberapa gudang.",
        "author": "Pak Budi",
        "keyword_hint": "inventory",
    },
    {
        "content": "Kami sedang mencari vendor untuk membangun sistem ERP yang terintegrasi. Perusahaan distribusi kami punya 5 cabang dan masih pakai sistem terpisah-pisah.",
        "author": "Diana Retail",
        "keyword_hint": "ERP",
    },
    {
        "content": "Butuh developer untuk bikin aplikasi mobile buat sales team kami. Harus bisa tracking order, cek stok, dan input data customer di lapangan.",
        "author": "Andi Manager",
        "keyword_hint": "mobile",
    },
    {
        "content": "Perusahaan kami ingin mengotomatisasi proses approval dokumen. Saat ini masih manual pakai email dan WhatsApp, sering terlewat.",
        "author": "HR Linda",
        "keyword_hint": "automation",
    },
    {
        "content": "Ada yang pernah pakai software HRIS untuk perusahaan 200+ karyawan? Kami butuh yang bisa handle payroll, cuti, dan absensi.",
        "author": "Finance Rudi",
        "keyword_hint": "HRIS",
    },
    {
        "content": "Mau tanya, ada yang bisa bikin website company profile plus portal customer? Budget sekitar 50-80 juta.",
        "author": "Owner Toko",
        "keyword_hint": "website",
    },
    {
        "content": "Saya sedang belajar membuat aplikasi inventory menggunakan Python. Ada tutorial yang bagus?",
        "author": "Student Adi",
        "keyword_hint": "inventory",
    },
    {
        "content": "Jual laptop gaming murah! RTX 4060, RAM 16GB. Harga nego. COD Jakarta.",
        "author": "Seller123",
        "keyword_hint": "jual",
    },
    {
        "content": "Lowongan kerja: Dibutuhkan programmer Python untuk project internal. Pengalaman minimal 2 tahun. Kirim CV ke email.",
        "author": "HRD PT ABC",
        "keyword_hint": "programmer",
    },
    {
        "content": "Kami perusahaan F&B yang ingin go digital. Butuh sistem POS yang terintegrasi dengan inventory dan accounting. Ada rekomendasi vendor?",
        "author": "Owner Resto",
        "keyword_hint": "POS",
    },
    {
        "content": "Ada yang bisa buatkan chatbot untuk customer service kami? Volume chat makin tinggi dan tim CS kewalahan.",
        "author": "CS Manager",
        "keyword_hint": "chatbot",
    },
    {
        "content": "Diskusi: menurut kalian, lebih baik pakai SaaS atau custom development untuk sistem warehouse management?",
        "author": "Logistic Head",
        "keyword_hint": "warehouse",
    },
    {
        "content": "Perusahaan kami butuh aplikasi tracking pengiriman real-time. Driver bisa update status, customer bisa cek posisi barang.",
        "author": "Direktur Logistik",
        "keyword_hint": "tracking",
    },
    {
        "content": "Looking for an IT consultant to help us migrate from on-premise to cloud. We have 3 legacy systems that need to be integrated.",
        "author": "CTO Startup",
        "keyword_hint": "cloud",
    },
    {
        "content": "Kantor kami butuh jasa managed service IT untuk handle 50 workstation dan 3 server. Butuh SLA response 1 jam dan 24/7 monitoring.",
        "author": "Ops Director PT Maju",
        "keyword_hint": "managed service",
    },
    {
        "content": "Ada vendor yang melayani penetration testing dan audit keamanan ISO 27001 untuk aplikasi fintech kami? Butuh sertifikasi resmi untuk OJK.",
        "author": "SecOps Lead",
        "keyword_hint": "cybersecurity",
    },
    {
        "content": "Perusahaan kami butuh jasa pembuatan website baru dan portal e-commerce B2B. Desain modern, integrasi payment gateway Midtrans dan ERP kami.",
        "author": "Marketing Manager MegaCorp",
        "keyword_hint": "website",
    },
    {
        "content": "Kami butuh dashboard Business Intelligence (Power BI / Tableau) untuk menggabungkan data penjualan dari 20 cabang ritel secara real-time.",
        "author": "Head of Data PT Retail Nusantara",
        "keyword_hint": "data analytics",
    },
    {
        "content": "Ada rekomendasi software house yang bisa build platform SaaS multi-tenant untuk manajemen klinik? Budget tersedia.",
        "author": "Dr. Hendra HealthTech",
        "keyword_hint": "saas",
    },
    {
        "content": "Server VPS kami di DigitalOcean sering down saat traffic spike. Butuh DevOps engineer / sysadmin untuk setup Kubernetes atau Docker auto-scaling dan migrasi ke AWS.",
        "author": "Tech Lead MediaGroup",
        "keyword_hint": "cloud",
    },
    {
        "content": "Butuh tim IT infrastructure untuk penarikan kabel LAN, setup Mikrotik, dan VPN site-to-site untuk kantor baru 3 lantai di BSD.",
        "author": "General Affairs PT Indo",
        "keyword_hint": "network",
    },
    {
        "content": "Sales team kami kewalahan handle leads masuk dari WhatsApp dan iklan Meta. Butuh sistem CRM omnichannel WhatsApp yang bisa auto-assign dan follow up otomatis.",
        "author": "VP Sales Properti",
        "keyword_hint": "crm",
    },
    {
        "content": "Hari ini cuaca cerah sekali ya. Enak buat jalan-jalan ke mall.",
        "author": "RandomUser",
        "keyword_hint": "none",
    },
]


class MockSourceAdapter:
    """Mock source adapter that returns dummy prospect data for testing."""

    @property
    def source_name(self) -> str:
        return "mock"

    async def search(
        self,
        keywords: list[str],
        start_date: str,
        end_date: str,
        limit: int,
    ) -> list[RawLead]:
        results: list[RawLead] = []
        keywords_lower = [kw.lower() for kw in keywords]

        for post in MOCK_POSTS:
            if len(results) >= limit:
                break

            content_lower = post["content"].lower()
            matched_keyword = None
            for kw in keywords_lower:
                if kw in content_lower or kw in post.get("keyword_hint", "").lower():
                    matched_keyword = kw
                    break

            if matched_keyword:
                post_id = random.randint(1000, 9999)
                results.append(RawLead(
                    source="mock",
                    source_url=f"https://mock-source.example.com/post/{post_id}",
                    author_name=post["author"],
                    author_profile_url=f"https://mock-source.example.com/user/{post['author'].lower().replace(' ', '_')}",
                    published_at=datetime.utcnow(),
                    content=post["content"],
                    matched_keyword=matched_keyword,
                ))

        return results

    async def health_check(self) -> dict:
        return {"status": "ok", "source": "mock"}
