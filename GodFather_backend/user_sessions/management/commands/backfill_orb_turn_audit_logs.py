from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from user_sessions.models import BrandMemory, OrbTurnAuditLog, Question


class Command(BaseCommand):
    help = "Backfill ORB turn audit logs from BrandMemory confidence history."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Backfill confidence history entries created/updated within this many days. Default: 7.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be created without writing rows.",
        )
        parser.add_argument(
            "--session-id",
            type=int,
            default=None,
            help="Limit backfill to one session id.",
        )
        parser.add_argument(
            "--discovery-id",
            default="",
            help="Limit backfill to one associated_discovery_id.",
        )

    def handle(self, *args, **options):
        days = max(1, int(options["days"] or 7))
        since = timezone.now() - timezone.timedelta(days=days)
        dry_run = bool(options["dry_run"])
        discovery_filter = str(options.get("discovery_id") or "").strip()

        memories = BrandMemory.objects.filter(
            key__startswith="orb:",
            key__endswith=":confidence_history",
        ).select_related("session", "session__created_by")

        if options.get("session_id"):
            memories = memories.filter(session_id=options["session_id"])
        if discovery_filter:
            memories = memories.filter(key=f"orb:{discovery_filter}:confidence_history")

        scanned = 0
        created = 0
        skipped = 0
        out_of_window = 0
        missing_question = 0

        for memory in memories.iterator():
            scanned += 1
            value = memory.value if isinstance(memory.value, dict) else {}
            history = value.get("confidence_history")
            if not isinstance(history, list):
                skipped += 1
                continue

            associated_discovery_id = str(value.get("associated_discovery_id") or "")
            if not associated_discovery_id and memory.key.startswith("orb:"):
                associated_discovery_id = memory.key[len("orb:"):-len(":confidence_history")]

            for entry in history:
                if not isinstance(entry, dict):
                    skipped += 1
                    continue

                entry_created_at = self._parse_entry_datetime(entry.get("created_at")) or memory.updated_at or memory.created_at
                if entry_created_at < since:
                    out_of_window += 1
                    continue

                question_id = self._as_int(entry.get("conversation_question_id") or value.get("question_id"))
                question = Question.objects.filter(id=question_id).first() if question_id else None
                if not question:
                    missing_question += 1

                turn_index = self._as_int(entry.get("turn_index")) or 1
                answer_preview = str(entry.get("answer_preview") or "").strip()[:500]
                status = str(entry.get("status") or value.get("latest_status") or "").lower()

                duplicate = OrbTurnAuditLog.objects.filter(
                    session=memory.session,
                    question=question,
                    associated_discovery_id=associated_discovery_id,
                    turn_index=turn_index,
                    answer_preview=answer_preview,
                ).exists()
                if duplicate:
                    skipped += 1
                    continue

                user = memory.session.created_by if memory.session else None
                row_kwargs = {
                    "user": user,
                    "user_email": getattr(user, "email", "") or "",
                    "session": memory.session,
                    "question": question,
                    "conversation": None,
                    "conversation_id_snapshot": None,
                    "turn_index": turn_index,
                    "conversation_question_id": question_id,
                    "question_text": str(entry.get("question_text") or value.get("question_text") or ""),
                    "latest_answer": answer_preview,
                    "previous_score": self._as_int(entry.get("previous_score") or value.get("previous_score")),
                    "delta_score": self._as_int(entry.get("delta_score") or value.get("delta_score")),
                    "confidence_score": self._as_int(entry.get("confidence_score") or value.get("latest_confidence_score")),
                    "target_confidence_threshold": self._as_int(entry.get("target_confidence_threshold") or value.get("target_confidence_threshold")),
                    "answer_preview": answer_preview,
                    "response_preview": str(entry.get("response_preview") or "").strip()[:500],
                    "status": status,
                    "associated_discovery_id": associated_discovery_id,
                    "view_api_response": {},
                    "metadata": {
                        "backfilled_from": "BrandMemory.confidence_history",
                        "brand_memory_id": memory.id,
                        "brand_memory_key": memory.key,
                    },
                    "guardrail": {},
                    "crux_context": {},
                    "confidence_tracking": {
                        "previous_score": self._as_int(entry.get("previous_score") or value.get("previous_score")),
                        "delta_score": self._as_int(entry.get("delta_score") or value.get("delta_score")),
                        "latest_confidence_score": self._as_int(entry.get("confidence_score") or value.get("latest_confidence_score")),
                        "target_confidence_threshold": self._as_int(entry.get("target_confidence_threshold") or value.get("target_confidence_threshold")),
                        "confidence_history_entry": entry,
                    },
                    "conversation_dropped": False,
                    "source": "backfill_brandmemory_confidence_history",
                }

                if dry_run:
                    created += 1
                    continue

                audit_log = OrbTurnAuditLog.objects.create(**row_kwargs)
                if entry_created_at:
                    OrbTurnAuditLog.objects.filter(pk=audit_log.pk).update(created_at=entry_created_at)
                created += 1

        mode = "DRY RUN" if dry_run else "DONE"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: scanned={scanned}, created={created}, skipped={skipped}, "
            f"out_of_window={out_of_window}, missing_question={missing_question}, days={days}"
        ))

    def _parse_entry_datetime(self, value):
        if not value:
            return None
        parsed = parse_datetime(str(value))
        if not parsed:
            return None
        if timezone.is_naive(parsed):
            return timezone.make_aware(parsed, timezone.get_current_timezone())
        return parsed

    def _as_int(self, value):
        try:
            if value is None or value == "":
                return None
            return int(float(value))
        except (TypeError, ValueError):
            return None
