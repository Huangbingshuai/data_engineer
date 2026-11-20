"""Focused unit tests for scheduler tool result handling."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from dataengineer.tools.func_tool.scheduler_tools import SchedulerTools


def test_build_scheduler_envelope_known_total_has_next_offset():
    result = SchedulerTools._build_scheduler_envelope(
        [{"job_id": "job-1"}, {"job_id": "job-2"}], total=5, offset=2, limit=2
    )

    assert result.success == 1
    assert result.result == {
        "items": [{"job_id": "job-1"}, {"job_id": "job-2"}],
        "total": 5,
        "has_more": True,
        "extra": {"next_offset": 4},
    }


def test_build_scheduler_envelope_known_total_last_page():
    result = SchedulerTools._build_scheduler_envelope([{"job_id": "job-3"}], total=3, offset=2, limit=2)

    assert result.result["has_more"] is False
    assert result.result["extra"] is None


@pytest.mark.parametrize(
    ("rows", "limit", "expected"),
    [([{"id": 1}, {"id": 2}], 2, True), ([{"id": 1}], 2, False), ([], 0, None)],
)
def test_build_scheduler_envelope_unknown_total_uses_page_size(rows, limit, expected):
    result = SchedulerTools._build_scheduler_envelope(rows, total=None, offset=0, limit=limit)

    assert result.result["has_more"] is expected


def test_list_scheduler_jobs_closes_adapter_and_formats_rows():
    config = MagicMock()
    tools = SchedulerTools(config)
    job = SimpleNamespace(job_id="daily", job_name="Daily", status=SimpleNamespace(value="active"), schedule="0 8 * * *")
    adapter = MagicMock()
    adapter.list_jobs.return_value = SimpleNamespace(items=[job], total=1)
    tools._get_adapter = MagicMock(return_value=adapter)

    result = tools.list_scheduler_jobs(limit=20, offset=0)

    assert result.success == 1
    assert result.result["items"] == [{"job_id": "daily", "job_name": "Daily", "status": "active", "schedule": "0 8 * * *"}]
    adapter.list_jobs.assert_called_once_with(limit=20, offset=0)
    adapter.close.assert_called_once_with()


def test_list_scheduler_jobs_reports_adapter_failure_and_closes():
    tools = SchedulerTools(MagicMock())
    adapter = MagicMock()
    adapter.list_jobs.side_effect = RuntimeError("scheduler unavailable")
    tools._get_adapter = MagicMock(return_value=adapter)

    result = tools.list_scheduler_jobs()

    assert result.success == 0
    assert "scheduler unavailable" in result.error
    adapter.close.assert_called_once_with()
