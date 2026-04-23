# Observability System - Quick Reference

## What Was Implemented

A complete observability and telemetry system that automatically records every `/api/explain` request.

## Storage Architecture

**Hybrid Storage Strategy**:
- **SQLite Database** (`observability.db`): Metadata, previews, hashes, file paths
- **Artifact Files** (`observability_artifacts/`): Audio files (MP3)

> [!NOTE]
> Visual artifacts are **Pollinations.ai CDN URLs** (not base64 images). The observability system records the URL string for each segment's visual, not a downloaded image file. Only audio is saved as a full artifact file.

## 📁 Files Created

### Observability Module
```
src/observability/
├── __init__.py          # Public interface
├── database.py          # SQLite initialization
├── models.py            # Data structures
├── recorder.py          # Recording logic (hybrid storage)
├── timers.py            # Performance measurement
└── utils.py             # Helper functions
```

### Modified
- `src/engines/aggregation/composer.py` - Integrated observability

### Configuration
- `.gitignore` - Excludes observability data from git

### Documentation
- `docs/OBSERVABILITY_GUIDE.md` - Complete usage guide

## Key Features

- ON by default — No configuration needed
- Hybrid storage — Efficient metadata + full artifacts
- Never crashes — All code wrapped in try/except
- Zero API changes — Response format unchanged
- Records everything — Success, partial, and failed requests
- Queryable via SQL — Standard SQLite tools
- Git-safe — Automatically excluded from version control

## 🔍 Quick Queries

**View recent runs**:
```sql
SELECT run_id, status, total_time_ms, created_at 
FROM explanation_runs 
ORDER BY created_at DESC 
LIMIT 10;
```

**Find failures**:
```sql
SELECT run_id, created_at, json_extract(payload_json, '$.failures') 
FROM explanation_runs 
WHERE status = 'failed';
```

**Performance analysis**:
```sql
SELECT AVG(total_time_ms), MIN(total_time_ms), MAX(total_time_ms)
FROM explanation_runs 
WHERE status = 'success';
```

## 📖 Full Documentation

See [docs/OBSERVABILITY_GUIDE.md](file:///Users/shivanisingh/Desktop/ConversAI-Demo/conversai-backend/docs/OBSERVABILITY_GUIDE.md) for:
- Complete SQL query examples
- Artifact access instructions
- Cleanup and maintenance
- How to disable observability
- Troubleshooting guide

## 🧪 Testing

The system will automatically record data when you make requests:

```bash
curl -X POST http://localhost:8000/api/explain \
  -H "Content-Type: application/json" \
  -d '{"text": "Explain quantum computing", "duration": "short"}'
```

Then inspect:
```bash
sqlite3 observability.db "SELECT run_id, status, total_time_ms FROM explanation_runs ORDER BY created_at DESC LIMIT 5;"
ls observability_artifacts/
```
