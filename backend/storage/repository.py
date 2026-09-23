import json
import logging
import threading
from abc import ABC, abstractmethod
from pathlib import Path

from errors import NotFoundError, UpstreamError

log = logging.getLogger(__name__)

# Columns of the `interviews` table (see db/schema.sql). Everything the
# interview engine needs to resume a session lives in `config` and `state`.
COLUMNS = ["id", "created_at", "updated_at", "status", "is_sample", "candidate_name", "role", "config", "state", "report"]
LIST_COLUMNS = "id,created_at,updated_at,status,is_sample,candidate_name,role,config->num_questions,config->focus_areas,report->overall"


def summarize(row: dict) -> dict:
    """The fields shown in dashboard lists."""
    config = row.get("config") or {}
    report = row.get("report") or {}
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "status": row["status"],
        "is_sample": row.get("is_sample", False),
        "candidate_name": row["candidate_name"],
        "role": row["role"],
        "num_questions": row.get("num_questions", config.get("num_questions")),
        "focus_areas": row.get("focus_areas", config.get("focus_areas", [])),
        "overall": row.get("overall", report.get("overall")),
    }


class InterviewRepository(ABC):
    @abstractmethod
    def get(self, interview_id: str) -> dict: ...

    @abstractmethod
    def save(self, interview: dict) -> None: ...

    @abstractmethod
    def list(self) -> list[dict]: ...

    @abstractmethod
    def count_samples(self) -> int: ...


class SupabaseInterviewRepository(InterviewRepository):
    def __init__(self, client):
        self.client = client

    def _table(self):
        return self.client.table("interviews")

    def _run(self, query, action: str):
        try:
            return query.execute()
        except Exception as e:
            log.exception("Supabase %s failed", action)
            raise UpstreamError("The interview database is temporarily unavailable. Please try again.") from e

    def get(self, interview_id):
        res = self._run(self._table().select("*").eq("id", interview_id).limit(1), "get")
        if not res.data:
            raise NotFoundError("Interview not found.")
        return res.data[0]

    def save(self, interview):
        self._run(self._table().upsert({k: interview.get(k) for k in COLUMNS}), "save")

    def list(self):
        res = self._run(self._table().select(LIST_COLUMNS).order("created_at", desc=True).limit(100), "list")
        return [summarize(r) for r in res.data]

    def count_samples(self):
        res = self._run(self._table().select("id", count="exact").eq("is_sample", True).limit(1), "count")
        return res.count or 0


class LocalInterviewRepository(InterviewRepository):
    """JSON-file store for offline development and tests. Not for concurrent multi-process use."""

    def __init__(self, path: Path | None = None):
        self.path = path
        self._lock = threading.Lock()
        self._rows: dict[str, dict] = {}
        if path and path.exists():
            self._rows = json.loads(path.read_text())

    def _flush(self):
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self._rows, indent=1))

    def get(self, interview_id):
        row = self._rows.get(interview_id)
        if row is None:
            raise NotFoundError("Interview not found.")
        return json.loads(json.dumps(row))

    def save(self, interview):
        with self._lock:
            self._rows[interview["id"]] = json.loads(json.dumps({k: interview.get(k) for k in COLUMNS}))
            self._flush()

    def list(self):
        rows = sorted(self._rows.values(), key=lambda r: r["created_at"], reverse=True)
        return [summarize(r) for r in rows]

    def count_samples(self):
        return sum(1 for r in self._rows.values() if r.get("is_sample"))
