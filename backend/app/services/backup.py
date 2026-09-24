from __future__ import annotations

import io
import json
import re
import zipfile
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.models.goal import Goal, GoalEvent, GoalTask, ReviewGoal
from app.models.review import Review, ReviewSection, ReviewSectionPreset, ReviewSnapshot, ReviewTemplate, ReviewTemplateItem
from app.models.user import UserSettings
from app.schemas.data import BackupPayload, ImportSummary


def encoded(value: Any) -> Any:
    if isinstance(value, (UUID, date, datetime)):
        return value.isoformat() if not isinstance(value, UUID) else str(value)
    return value


def record(item: Any, *fields: str) -> dict[str, Any]:
    return {field: encoded(getattr(item, field)) for field in fields}


def slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value[:80] or "goal"


class BackupService:
    def __init__(self, db: AsyncSession, user_id: UUID):
        self.db = db
        self.user_id = user_id

    async def export(self) -> dict[str, Any]:
        settings = await self.db.scalar(select(UserSettings).where(UserSettings.user_id == self.user_id))
        template = await self.db.scalar(select(ReviewTemplate).where(ReviewTemplate.user_id == self.user_id))
        template_items = list(await self.db.scalars(select(ReviewTemplateItem).where(ReviewTemplateItem.template_id == template.id).order_by(ReviewTemplateItem.sort_order)))
        presets = list(await self.db.scalars(select(ReviewSectionPreset).where(ReviewSectionPreset.user_id == self.user_id)))
        reviews = list(await self.db.scalars(select(Review).where(Review.user_id == self.user_id)))
        review_ids = [item.id for item in reviews]
        sections = list(await self.db.scalars(select(ReviewSection).where(ReviewSection.review_id.in_(review_ids)))) if review_ids else []
        snapshots = list(await self.db.scalars(select(ReviewSnapshot).where(ReviewSnapshot.review_id.in_(review_ids)))) if review_ids else []
        goals = list(await self.db.scalars(select(Goal).where(Goal.user_id == self.user_id)))
        goal_ids = [item.id for item in goals]
        tasks = list(await self.db.scalars(select(GoalTask).where(GoalTask.goal_id.in_(goal_ids)))) if goal_ids else []
        events = list(await self.db.scalars(select(GoalEvent).where(GoalEvent.goal_id.in_(goal_ids)))) if goal_ids else []
        relations = list(await self.db.scalars(select(ReviewGoal).where(ReviewGoal.review_id.in_(review_ids)))) if review_ids else []
        common = ("id", "created_at", "updated_at")
        soft = (*common, "deleted_at")
        return {
            "schema_version": 1,
            "exported_at": datetime.now(UTC).isoformat(),
            "user_settings": record(settings, "timezone", "theme", "autosave_seconds", "markdown_view", "show_active_goals", "show_tasks_due_today", "trash_retention_days"),
            "review_template": {
                "items": [record(item, *common, "title", "sort_order") for item in template_items],
            },
            "section_presets": [record(item, *soft, "title") for item in presets],
            "reviews": [record(item, *soft, "review_date", "status") for item in reviews],
            "review_sections": [record(item, *soft, "review_id", "preset_id", "title", "content_markdown", "sort_order") for item in sections],
            "review_snapshots": [record(item, *common, "review_id", "version", "snapshot") for item in snapshots],
            "goals": [record(item, *soft, "title", "description", "status", "start_date", "target_date") for item in goals],
            "goal_tasks": [record(item, *soft, "goal_id", "title", "description", "due_date", "status") for item in tasks],
            "goal_events": [record(item, *common, "goal_id", "event_type", "event_data") for item in events],
            "review_goal_relations": [record(item, *common, "review_id", "goal_id") for item in relations],
        }

    async def markdown_files(self, backup: dict[str, Any]) -> dict[str, str]:
        goals = {item["id"]: item for item in backup["goals"]}
        goal_links: dict[str, list[dict]] = {}
        review_links: dict[str, list[dict]] = {}
        for relation in backup["review_goal_relations"]:
            goal = goals.get(relation["goal_id"])
            if goal:
                goal_links.setdefault(relation["review_id"], []).append(goal)
                review_links.setdefault(relation["goal_id"], []).append(relation)
        sections: dict[str, list[dict]] = {}
        for section in backup["review_sections"]:
            if section["deleted_at"] is None:
                sections.setdefault(section["review_id"], []).append(section)
        files: dict[str, str] = {}
        for review in backup["reviews"]:
            if review["deleted_at"] is not None:
                continue
            linked = ", ".join(item["title"] for item in goal_links.get(review["id"], [])) or "None"
            body = [f"# Daily Review · {review['review_date']}", "", f"- Status: {review['status']}", f"- Related Goals: {linked}", ""]
            for section in sorted(sections.get(review["id"], []), key=lambda item: item["sort_order"]):
                body.extend([f"## {section['title']}", "", section["content_markdown"], ""])
            year, month, _ = review["review_date"].split("-")
            files[f"reviews/{year}/{month}/{review['review_date']}.md"] = "\n".join(body)
        tasks: dict[str, list[dict]] = {}
        for task in backup["goal_tasks"]:
            if task["deleted_at"] is None:
                tasks.setdefault(task["goal_id"], []).append(task)
        review_dates = {item["id"]: item["review_date"] for item in backup["reviews"]}
        for goal in backup["goals"]:
            if goal["deleted_at"] is not None:
                continue
            related = [review_dates.get(item["review_id"]) for item in review_links.get(goal["id"], [])]
            body = [f"# {goal['title']}", "", goal["description"], "", f"- Status: {goal['status']}", f"- Start: {goal['start_date']}", f"- Target: {goal['target_date'] or 'None'}", "", "## Tasks", ""]
            body.extend(f"- [{'x' if task['status'] == 'completed' else ' '}] {task['title']}" for task in tasks.get(goal["id"], []))
            body.extend(["", "## Related Reviews", "", *(f"- {item}" for item in related if item)])
            files[f"goals/{slug(goal['title'])}.md"] = "\n".join(body)
        return files

    async def zip_bytes(self) -> bytes:
        backup = await self.export()
        files = await self.markdown_files(backup)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("auranoise-backup/backup.json", json.dumps(backup, ensure_ascii=False, indent=2))
            for path, content in files.items():
                archive.writestr(f"auranoise-backup/{path}", content)
        return buffer.getvalue()

    def validate(self, raw: dict[str, Any]) -> BackupPayload:
        try:
            payload = BackupPayload.model_validate(raw)
        except ValidationError as error:
            raise AppError(422, "INVALID_BACKUP", "Backup validation failed", error.errors(include_url=False)) from None
        if payload.schema_version != 1:
            raise AppError(422, "UNSUPPORTED_SCHEMA_VERSION", "Only backup schema version 1 is supported")
        return payload

    async def import_json(self, payload: BackupPayload, confirm: bool) -> ImportSummary:
        summary = ImportSummary(
            schema_version=payload.schema_version,
            reviews=len(payload.reviews),
            sections=len(payload.review_sections),
            goals=len(payload.goals),
            tasks=len(payload.goal_tasks),
            confirmed=confirm,
        )
        if not confirm:
            return summary
        try:
            settings = await self.db.scalar(select(UserSettings).where(UserSettings.user_id == self.user_id))
            for key, value in payload.user_settings.items():
                if key in {"timezone", "theme", "autosave_seconds", "markdown_view", "show_active_goals", "show_tasks_due_today", "trash_retention_days"}:
                    setattr(settings, key, value)

            template = await self.db.scalar(select(ReviewTemplate).where(ReviewTemplate.user_id == self.user_id))
            await self.db.execute(delete(ReviewTemplateItem).where(ReviewTemplateItem.template_id == template.id))
            for item in payload.review_template.get("items", []):
                self.db.add(ReviewTemplateItem(id=UUID(item["id"]), template_id=template.id, title=item["title"], sort_order=item["sort_order"]))

            await self._insert(ReviewSectionPreset, payload.section_presets, user_id=self.user_id)
            await self._insert(Review, payload.reviews, user_id=self.user_id, converters={"review_date": date.fromisoformat})
            await self._insert(Goal, payload.goals, user_id=self.user_id, converters={"start_date": date.fromisoformat, "target_date": self._date_or_none})
            await self.db.flush()
            await self._insert(ReviewSection, payload.review_sections, uuid_fields={"review_id", "preset_id"})
            await self._insert(ReviewSnapshot, payload.review_snapshots, uuid_fields={"review_id"})
            await self._insert(GoalTask, payload.goal_tasks, uuid_fields={"goal_id"}, converters={"due_date": self._date_or_none})
            await self._insert(GoalEvent, payload.goal_events, uuid_fields={"goal_id"})
            await self._insert(ReviewGoal, payload.review_goal_relations, uuid_fields={"review_id", "goal_id"})
            await self.db.commit()
        except (KeyError, TypeError, ValueError, IntegrityError) as error:
            await self.db.rollback()
            raise AppError(422, "INVALID_BACKUP_DATA", "Backup data could not be imported", str(error)) from None
        return summary

    async def _insert(
        self,
        model,
        rows: list[dict[str, Any]],
        uuid_fields: set[str] = set(),
        converters: dict[str, Any] = {},
        **fixed,
    ) -> None:
        columns = {column.name for column in model.__table__.columns} - {"created_at", "updated_at"}
        for source in rows:
            item_id = UUID(source["id"])
            if await self.db.get(model, item_id):
                continue
            values = {key: value for key, value in source.items() if key in columns}
            values["id"] = item_id
            values.update(fixed)
            for field in uuid_fields:
                if values.get(field):
                    values[field] = UUID(values[field])
            if values.get("deleted_at"):
                values["deleted_at"] = datetime.fromisoformat(values["deleted_at"])
            for field, converter in converters.items():
                if field in values:
                    values[field] = converter(values[field])
            self.db.add(model(**values))

    @staticmethod
    def _date_or_none(value: str | None) -> date | None:
        return date.fromisoformat(value) if value else None

