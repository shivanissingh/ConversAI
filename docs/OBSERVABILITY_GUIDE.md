# ConversAI Observability Guide

## What is Observability in ConversAI?

The observability system automatically records every `/api/explain` request to help you:

- **Debug without re-running models** - Inspect past requests with full context
- **Analyze narration quality** - Review generated explanations and segments
- **Review generated visuals** - Access all images created for each segment
- **Track failures and performance** - Identify bottlenecks and error patterns
- **Improve iteratively** - Make data-driven decisions based on real usage

**Key Feature**: Observability is **ON by default** and records data **without triggering any additional AI calls**.

---

## What Data is Recorded Per Request?

Each request creates a **run record** with the following data:

### 1. User Input Snapshot
- Original text
- Duration setting (`short` | `medium`)
- Custom instruction (if any)
- Avatar enabled flag

### 2. Explanation Engine Data
- Extracted concepts
- Full narration text
- Segments with timing (start/end times)
- Processing time metrics

### 3. Visual Engine Data
- Generated images (stored as files, referenced in DB)
- Image metadata (segment ID, generation time)
- Visual planning prompts (if available)
- Per-segment failures

### 4. Voice & Avatar Data
- Audio file (stored as MP3, referenced in DB)
- Audio duration
- Avatar animation states and cues
- Generation time

### 5. Quality & Performance Metrics
- Total processing time
- Per-engine timing breakdown
- Visual success ratio (generated/requested)
- Audio vs. segment duration delta

### 6. Failures
- Component name (explanation, visual, voice)
- Segment ID (if applicable)
- Failure reason
- Critical flag

---

## Storage Architecture

### Hybrid Storage Strategy

The system uses a **hybrid approach** to balance queryability and storage efficiency:

#### SQLite Database
**Location**: `conversai-backend/observability.db`

**Stores**:
- Run metadata (ID, timestamp, status, total time)
- Truncated base64 previews (~400 chars)
- SHA-256 hashes of full artifacts
- File paths to full artifacts
- All metrics and failure data

#### Artifact Files
**Location**: `conversai-backend/observability_artifacts/`

**Structure**:
```
observability_artifacts/
├── run_<uuid>/
│   ├── audio.mp3
│   ├── segment_0.png
│   ├── segment_1.png
│   └── segment_2.png
```

**Stores**:
- Full base64-decoded images (PNG)
- Full audio files (MP3)

> [!IMPORTANT]
> **Storage Considerations**: A typical request generates 500KB-2MB of data. For 1000 requests, expect ~1-2GB total storage (DB + artifacts).

---

## How to Inspect Runs

### Option 1: SQLite CLI

#### View Recent Runs
```bash
cd conversai-backend

# Interactive shell
sqlite3 observability.db

# Quick query
sqlite3 observability.db "SELECT run_id, status, total_time_ms, created_at FROM explanation_runs ORDER BY created_at DESC LIMIT 10;"
```

#### View Full Run Data
```bash
# Export specific run to JSON
sqlite3 observability.db "SELECT payload_json FROM explanation_runs WHERE run_id='<run-id>';" | jq .
```

#### Common Queries

**Latest runs with status**:
```sql
SELECT 
    run_id, 
    status, 
    total_time_ms, 
    created_at 
FROM explanation_runs 
ORDER BY created_at DESC 
LIMIT 10;
```

**Failed runs only**:
```sql
SELECT 
    run_id, 
    created_at, 
    json_extract(payload_json, '$.failures') as failures
FROM explanation_runs 
WHERE status = 'failed'
ORDER BY created_at DESC;
```

**Visual success ratio**:
```sql
SELECT 
    AVG(json_extract(payload_json, '$.metrics.visual_success_ratio')) as avg_visual_success,
    COUNT(*) as total_runs
FROM explanation_runs 
WHERE status IN ('success', 'partial');
```

**Performance analysis**:
```sql
SELECT 
    AVG(total_time_ms) as avg_time_ms,
    MIN(total_time_ms) as min_time_ms,
    MAX(total_time_ms) as max_time_ms
FROM explanation_runs
WHERE status = 'success';
```

**Runs with visual failures**:
```sql
SELECT 
    run_id,
    created_at,
    json_extract(payload_json, '$.visual.failures') as visual_failures
FROM explanation_runs
WHERE json_array_length(json_extract(payload_json, '$.visual.failures')) > 0
ORDER BY created_at DESC;
```

### Option 2: VS Code SQLite Viewer

1. Install the **SQLite Viewer** extension in VS Code
2. Open `conversai-backend/observability.db`
3. Browse the `explanation_runs` table visually
4. Click on `payload_json` to view formatted JSON

### Option 3: Python Script

```python
import sqlite3
import json

conn = sqlite3.connect('observability.db')
cursor = conn.cursor()

# Get latest run
cursor.execute("""
    SELECT run_id, status, total_time_ms, payload_json 
    FROM explanation_runs 
    ORDER BY created_at DESC 
    LIMIT 1
""")

run_id, status, time_ms, payload_json = cursor.fetchone()
payload = json.loads(payload_json)

print(f"Run ID: {run_id}")
print(f"Status: {status}")
print(f"Time: {time_ms}ms")
print(f"Narration: {payload['explanation']['narration'][:100]}...")
print(f"Visual success: {payload['metrics']['visual_success_ratio']}")
```

---

## Accessing Artifact Files

### Images

```bash
# List all images for a specific run
ls observability_artifacts/run_<uuid>/

# View image
open observability_artifacts/run_<uuid>/segment_0.png
```

### Audio

```bash
# Play audio
afplay observability_artifacts/run_<uuid>/audio.mp3
```

### Programmatic Access

```python
from pathlib import Path

# Get artifact path from DB
run_id = "550e8400-e29b-41d4-a716-446655440000"
artifact_dir = Path(f"observability_artifacts/run_{run_id}")

# Read audio
audio_path = artifact_dir / "audio.mp3"
audio_bytes = audio_path.read_bytes()

# Read image
image_path = artifact_dir / "segment_0.png"
image_bytes = image_path.read_bytes()
```

---

## Storage & Cleanup Guidance

### Database Growth

- **Per request**: ~10-50 KB in SQLite (metadata only)
- **Per request**: ~500KB-2MB in artifact files
- **1000 requests**: ~1-2 GB total

### Manual Cleanup

#### Delete old runs
```sql
-- Delete runs older than 30 days
DELETE FROM explanation_runs 
WHERE created_at < datetime('now', '-30 days');

-- Reclaim disk space
VACUUM;
```

#### Delete artifact files
```bash
# Delete artifacts for runs older than 30 days
find observability_artifacts -type d -name "run_*" -mtime +30 -exec rm -rf {} \;
```

### Automated Cleanup (Optional)

Create a cleanup script:

```python
# cleanup_observability.py
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import shutil

# Delete runs older than 30 days
conn = sqlite3.connect('observability.db')
cutoff = (datetime.now() - timedelta(days=30)).isoformat()

# Get run IDs to delete
cursor = conn.cursor()
cursor.execute("SELECT run_id FROM explanation_runs WHERE created_at < ?", (cutoff,))
old_runs = [row[0] for row in cursor.fetchall()]

# Delete from DB
cursor.execute("DELETE FROM explanation_runs WHERE created_at < ?", (cutoff,))
conn.commit()

# Delete artifact directories
for run_id in old_runs:
    artifact_dir = Path(f"observability_artifacts/run_{run_id}")
    if artifact_dir.exists():
        shutil.rmtree(artifact_dir)

print(f"Cleaned up {len(old_runs)} old runs")
```

---

## How to Disable Observability

If you need to disable observability (e.g., for testing or privacy):

### Method 1: Environment Variable (Recommended)

```bash
# In .env file
OBSERVABILITY_ENABLED=false
```

Then update `src/observability/recorder.py`:

```python
import os

def record_run(run_data: Dict[str, Any]) -> bool:
    # Check if observability is disabled
    if os.getenv("OBSERVABILITY_ENABLED", "true").lower() == "false":
        return False
    
    # ... rest of the function
```

### Method 2: Comment Out Integration

In `src/engines/aggregation/composer.py`, comment out the observability import and recording calls:

```python
# from src.observability import record_run

# ... later in the code ...

# try:
#     record_run({...})
# except Exception as obs_error:
#     logger.warning(f"Failed to record observability data: {obs_error}")
```

> [!WARNING]
> Disabling observability means you lose the ability to debug past requests without re-running them.

---

## Git Safety

The following paths are automatically excluded from version control via `.gitignore`:

```
observability.db
observability.db-shm
observability.db-wal
observability_artifacts/
```

> [!CAUTION]
> **Never commit observability data** - it may contain sensitive user inputs and large binary files.

### Verify Git Exclusion

```bash
# Check that observability files are ignored
git status

# Should NOT show:
# - observability.db
# - observability_artifacts/
```

---

## Troubleshooting

### Database locked error

**Cause**: Multiple processes accessing the database simultaneously.

**Solution**: The database uses WAL mode which supports concurrent reads. If you still see errors, close any open SQLite connections.

### Artifact files missing

**Cause**: Artifact directory was deleted or moved.

**Solution**: The DB still has metadata. You can query the DB for truncated previews and hashes, but full artifacts are lost.

### Observability recording failed

**Cause**: Disk space, permissions, or serialization error.

**Effect**: Main request continues successfully (observability never crashes the app).

**Solution**: Check logs for warnings like:
```
WARNING: Observability recording failed: [error details]
```

### Large database size

**Cause**: Many recorded runs.

**Solution**: Run cleanup queries (see Storage & Cleanup section).

---

## Best Practices

1. **Regular Cleanup**: Set up automated cleanup for runs older than 30-60 days
2. **Monitor Disk Space**: Check `observability_artifacts/` size periodically
3. **Query Efficiently**: Use indexes (already created on `created_at` and `status`)
4. **Backup Important Runs**: Export critical runs to JSON before cleanup
5. **Privacy**: Ensure observability data is not exposed via APIs or committed to git

---

## Summary

The ConversAI observability system provides:

✅ **Automatic recording** of all requests (success, partial, failed)  
✅ **Hybrid storage** (SQLite + local files) for efficiency  
✅ **Zero impact** on API response format  
✅ **Failure resilience** - never crashes main request flow  
✅ **Rich queryability** via standard SQL  
✅ **Full artifact access** - images and audio preserved  
✅ **Git-safe** - excluded from version control

Use it to debug, analyze, and improve ConversAI iteratively without re-running expensive AI models.
