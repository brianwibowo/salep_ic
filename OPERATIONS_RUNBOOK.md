# SALEP operational runbook

Dokumen ini dipakai untuk deployment staging/production, pengecekan harian, dan penanganan kegagalan ingestion.

## Topologi proses

- `backend-staging` hanya menjalankan API dan tidak memiliki scheduler.
- `worker-staging` menjalankan scheduler 30 menit dan ingestion Si-RUP/SPSE.
- Kedua proses memakai database yang sama. Scheduler mengambil PostgreSQL advisory lock; jika PostgreSQL belum tersedia, worker memakai file lock di `SCHEDULER_LOCK_PATH`.
- API boleh direplikasi. Worker cukup satu container aktif; lock mencegah eksekusi ganda ketika ada proses worker kedua.

## Deployment checklist

1. Set `DATABASE_URL` dan jalankan `alembic upgrade head` sebelum container baru menerima traffic.
2. Pastikan `SALEP_PROCESS_ROLE=api` pada API dan `SALEP_PROCESS_ROLE=worker` pada worker. `AUTO_SEARCH_ENABLED=false` pada API.
3. Pastikan `APIFY_API_TOKEN`, kredensial LLM, dan service account Sheets ada.
4. Periksa `GET /health`, `GET /ready`, dan `GET /metrics`.
5. Pastikan hanya satu worker yang melaporkan `salep_scheduler_lock_held 1`.

## Pemeriksaan rutin

```bash
docker compose -f deploy/docker-compose.staging.yml ps
curl -fsS http://127.0.0.1:8101/health
curl -fsS http://127.0.0.1:8101/ready
curl -fsS http://127.0.0.1:8101/metrics | grep -E 'scheduler|circuit|alert'
docker logs --since=45m salep-worker-staging
```

Indikator normal: cycle scheduler berstatus `success`, tidak ada kenaikan `salep_circuit_tripped_total`, dan `salep_external_requests_total` memiliki outcome `success` untuk source yang aktif.

## Incident: scheduler tidak berjalan

1. Cek `docker logs salep-worker-staging` dan `GET /api/v1/scheduler/status`.
2. Jika status `locked`, cari worker/container lama dan cek proses yang masih hidup. Advisory lock dilepas ketika koneksi PostgreSQL ditutup; file lock dilepas saat proses mati.
3. Pastikan `AUTO_SEARCH_ENABLED=true`, `SALEP_PROCESS_ROLE=worker`, dan interval tidak lebih kecil dari lima menit.
4. Jalankan satu cycle manual setelah penyebab diperbaiki:

   ```bash
   curl -X POST http://127.0.0.1:8101/api/v1/scheduler/trigger
   ```

## Incident: source circuit terbuka

1. Lihat `salep_circuit_tripped_total` dan nama `source:<name>` pada metrics.
2. Periksa status provider, HTTP 401/403, quota, dan perubahan markup.
3. Retry otomatis memakai exponential backoff untuk timeout, network error, HTTP 429, dan HTTP 5xx. Credential error tidak diulang terus-menerus.
4. Setelah provider pulih, circuit masuk half-open setelah `CIRCUIT_RECOVERY_SECONDS` dan kembali closed setelah satu request sukses.
5. Jangan menghapus data hasil scrape terakhir; jalankan ingestion ulang dengan keyword/tahun yang sama setelah source sehat.

## Incident: data PostgreSQL tidak tersedia

1. `GET /ready` harus dianggap degraded ketika `database_ready=false`.
2. Cek konektivitas, kredensial, kapasitas disk, dan status migration.
3. API boleh tetap hidup untuk endpoint yang tidak memerlukan database, tetapi worker harus dihentikan sampai database pulih agar tidak membuat backlog palsu.
4. Jalankan `alembic upgrade head` hanya setelah backup terakhir tervalidasi.

## Backup dan restore

Buat backup PostgreSQL menggunakan `pg_dump` dan simpan checksum:

```bash
cd backend
PYTHONPATH=. python scripts/backup.py --database-url "$DATABASE_URL"
PYTHONPATH=. python scripts/backup.py --database-url "$DATABASE_URL" --dry-run
```

Default retention backup adalah 14 hari (`BACKUP_RETENTION_DAYS`). Retention record operational tidak menghapus lead atau procurement package:

```bash
cd backend
PYTHONPATH=. python scripts/retention.py --database-url "$DATABASE_URL" --dry-run
PYTHONPATH=. python scripts/retention.py --database-url "$DATABASE_URL"
```

Retention default: source snapshot 90 hari dan cache LLM 90 hari. Restore PostgreSQL dilakukan ke database baru terlebih dahulu, validasi `alembic current`, `/ready`, jumlah package/lead, lalu ubah `DATABASE_URL` secara terkontrol. Jangan restore langsung menimpa database produksi tanpa validasi.

## Alerting

Set `ALERT_WEBHOOK_URL` untuk menerima event scheduler failure, retry exhaustion, atau kondisi operasional lain yang dihubungkan oleh service. Alert memiliki cooldown (`ALERT_COOLDOWN_SECONDS`) agar outage panjang tidak membanjiri channel. Tanpa webhook, alert tetap dicatat sebagai log `ERROR`.

## Rollback

Rollback aplikasi dilakukan dengan mengembalikan image tag sebelumnya dan menjaga database pada revision yang kompatibel. Migration downgrade hanya dilakukan setelah backup dan review; untuk incident data gunakan restore ke database baru, bukan menghapus tabel produksi secara manual.

