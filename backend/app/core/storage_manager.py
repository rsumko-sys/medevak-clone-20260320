"""Storage manager for disk organization, archival, and space-efficient retention."""
from __future__ import annotations

import os
import shutil
import tarfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


@dataclass
class DirectoryStats:
    bytes_used: int = 0
    files_count: int = 0
    directories_count: int = 0


def _scan_dir(path: Path) -> DirectoryStats:
    stats = DirectoryStats()
    if not path.exists():
        return stats

    for root, dirs, files in os.walk(path):
        stats.directories_count += len(dirs)
        stats.files_count += len(files)
        for name in files:
            fp = Path(root) / name
            try:
                stats.bytes_used += fp.stat().st_size
            except OSError:
                # Ignore files that disappear mid-scan.
                continue
    return stats


def _latest_tree_mtime(path: Path) -> datetime:
    latest = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    for root, _, files in os.walk(path):
        for name in files:
            fp = Path(root) / name
            try:
                ts = datetime.fromtimestamp(fp.stat().st_mtime, tz=timezone.utc)
                if ts > latest:
                    latest = ts
            except OSError:
                continue
    return latest


def get_storage_stats(upload_base: Path, archive_base: Path, export_base: Path | None = None) -> dict:
    upload_stats = _scan_dir(upload_base)
    archive_stats = _scan_dir(archive_base)
    export_stats = _scan_dir(export_base) if export_base else DirectoryStats()

    total = upload_stats.bytes_used + archive_stats.bytes_used + export_stats.bytes_used
    return {
        "total_bytes": total,
        "uploads": {
            "path": str(upload_base),
            "bytes": upload_stats.bytes_used,
            "files": upload_stats.files_count,
            "directories": upload_stats.directories_count,
        },
        "archives": {
            "path": str(archive_base),
            "bytes": archive_stats.bytes_used,
            "files": archive_stats.files_count,
            "directories": archive_stats.directories_count,
        },
        "exports": {
            "path": str(export_base) if export_base else None,
            "bytes": export_stats.bytes_used,
            "files": export_stats.files_count,
            "directories": export_stats.directories_count,
        },
    }


def archive_case_uploads(
    upload_base: Path,
    archive_base: Path,
    older_than_days: int,
    *,
    remove_source: bool,
    dry_run: bool,
) -> dict:
    upload_base.mkdir(parents=True, exist_ok=True)
    archive_base.mkdir(parents=True, exist_ok=True)

    threshold = datetime.now(timezone.utc) - timedelta(days=older_than_days)
    archived_cases: list[dict] = []
    skipped = 0

    for case_dir in sorted(upload_base.iterdir()):
        if not case_dir.is_dir():
            continue

        latest_mtime = _latest_tree_mtime(case_dir)
        if latest_mtime > threshold:
            skipped += 1
            continue

        case_stats = _scan_dir(case_dir)
        dt = datetime.now(timezone.utc)
        shard_dir = archive_base / str(dt.year) / f"{dt.month:02d}"
        shard_dir.mkdir(parents=True, exist_ok=True)
        archive_path = shard_dir / f"{case_dir.name}_{dt.strftime('%Y%m%dT%H%M%SZ')}.tar.gz"

        if not dry_run:
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(case_dir, arcname=case_dir.name)

            if remove_source:
                shutil.rmtree(case_dir, ignore_errors=True)

        archived_cases.append({
            "case_dir": case_dir.name,
            "source_bytes": case_stats.bytes_used,
            "source_files": case_stats.files_count,
            "last_update": latest_mtime.isoformat(),
            "archive_path": str(archive_path),
            "removed_source": remove_source and not dry_run,
            "dry_run": dry_run,
        })

    archived_bytes = sum(item["source_bytes"] for item in archived_cases)
    return {
        "threshold_days": older_than_days,
        "archived_count": len(archived_cases),
        "archived_bytes": archived_bytes,
        "skipped_recent": skipped,
        "remove_source": remove_source,
        "dry_run": dry_run,
        "items": archived_cases,
    }
