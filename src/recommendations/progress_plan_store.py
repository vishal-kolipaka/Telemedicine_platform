"""
progress_plan_store.py — Persistent Storage & Progress Tracking for Progress Plans

Maintains persistent progress state across page refreshes, browser reloads, and navigation.
File-backed JSON store with thread synchronization.
"""

from __future__ import annotations

import os
import json
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional

STORE_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "progress_plans.json"))


class ProgressPlanStore:
    """Thread-safe, file-backed persistent store for personalized progress plans."""

    _lock = threading.Lock()
    _cache: Dict[str, Dict[str, Any]] = {}
    _initialized = False

    @classmethod
    def _ensure_initialized(cls):
        if cls._initialized:
            return
        os.makedirs(os.path.dirname(STORE_FILE_PATH), exist_ok=True)
        if os.path.exists(STORE_FILE_PATH):
            try:
                with open(STORE_FILE_PATH, "r", encoding="utf-8") as f:
                    cls._cache = json.load(f)
            except Exception:
                cls._cache = {}
        else:
            cls._cache = {}
            with open(STORE_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=2)
        cls._initialized = True

    @classmethod
    def _save_to_disk(cls):
        try:
            os.makedirs(os.path.dirname(STORE_FILE_PATH), exist_ok=True)
            with open(STORE_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(cls._cache, f, indent=2)
        except Exception as e:
            print(f"[ERROR] Failed to save progress plans to disk: {e}")

    @classmethod
    def save_plan(cls, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves a newly generated plan and initializes its progress record."""
        with cls._lock:
            cls._ensure_initialized()
            plan_id = plan_data["plan_id"]
            patient_id = plan_data.get("patient_info", {}).get("patient_id", "P001")
            duration = plan_data.get("duration", "1_week")
            total_tasks = plan_data.get("total_tasks", 0)

            record = {
                "plan_id": plan_id,
                "patient_id": patient_id,
                "duration": duration,
                "plan_data": plan_data,
                "total_tasks": total_tasks,
                "current_day": 1,
                "completed_tasks": [],
                "completed_days": [],
                "overall_progress": 0.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            cls._cache[plan_id] = record
            cls._save_to_disk()
            return record

    @classmethod
    def get_plan(cls, plan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a progress plan record by plan_id."""
        with cls._lock:
            cls._ensure_initialized()
            return cls._cache.get(plan_id)

    @classmethod
    def get_plans_for_patient(cls, patient_id: str) -> List[Dict[str, Any]]:
        """Retrieves all plans associated with a patient."""
        with cls._lock:
            cls._ensure_initialized()
            return [p for p in cls._cache.values() if p.get("patient_id") == patient_id]

    @classmethod
    def toggle_task(
        cls,
        plan_id: str,
        task_id: str,
        completed: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """Toggles a task's completion status, recalculates daily and overall completion, and unlocks days."""
        with cls._lock:
            cls._ensure_initialized()
            if plan_id not in cls._cache:
                return None

            record = cls._cache[plan_id]
            completed_tasks_set = set(record.get("completed_tasks", []))

            # Determine new state
            if completed is True:
                completed_tasks_set.add(task_id)
            elif completed is False:
                completed_tasks_set.discard(task_id)
            else:
                if task_id in completed_tasks_set:
                    completed_tasks_set.remove(task_id)
                else:
                    completed_tasks_set.add(task_id)

            record["completed_tasks"] = list(completed_tasks_set)

            # Recalculate day completions
            plan_data = record.get("plan_data", {})
            days_list = plan_data.get("days", [])

            completed_days = []
            max_unlocked_day = 1

            for day_obj in days_list:
                d_num = day_obj["day_number"]
                day_task_ids = [t["id"] for t in day_obj.get("tasks", [])]
                all_done = len(day_task_ids) > 0 and all(tid in completed_tasks_set for tid in day_task_ids)

                day_obj["is_completed"] = all_done
                if all_done:
                    completed_days.append(d_num)
                    max_unlocked_day = max(max_unlocked_day, d_num + 1)

            # Update unlocks in all days
            for day_obj in days_list:
                d_num = day_obj["day_number"]
                day_obj["is_unlocked"] = (d_num <= max_unlocked_day)

            record["completed_days"] = completed_days
            record["current_day"] = min(max_unlocked_day, len(days_list))

            # Recalculate overall progress
            total_tasks = record.get("total_tasks", len(completed_tasks_set) or 1)
            record["overall_progress"] = round((len(completed_tasks_set) / max(1, total_tasks)) * 100, 1)
            record["updated_at"] = datetime.now().isoformat()

            cls._save_to_disk()
            return record

    @classmethod
    def reset_plan(cls, plan_id: str) -> Optional[Dict[str, Any]]:
        """Resets all progress back to Day 1, with 0 completed tasks and re-locked future days."""
        with cls._lock:
            cls._ensure_initialized()
            if plan_id not in cls._cache:
                return None

            record = cls._cache[plan_id]
            record["completed_tasks"] = []
            record["completed_days"] = []
            record["current_day"] = 1
            record["overall_progress"] = 0.0
            record["updated_at"] = datetime.now().isoformat()

            plan_data = record.get("plan_data", {})
            for day_obj in plan_data.get("days", []):
                day_obj["is_completed"] = False
                day_obj["is_unlocked"] = (day_obj["day_number"] == 1)

            cls._save_to_disk()
            return record
