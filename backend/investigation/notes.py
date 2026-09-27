"""
TRINETRA Phase 6 — Analyst Notes Repository
Provides persistent storage and retrieval for human analyst annotations attached
to investigations, findings, or specific evidence items.
"""

import os
import json
import logging
from typing import List, Optional
from config.settings import settings
from investigation.models import AnalystNote

logger = logging.getLogger("trinetra.investigation.notes")


class AnalystNoteStore:
    """
    Stores analyst annotations as JSON records per investigation.
    """

    def __init__(self, notes_dir: Optional[str] = None):
        self.notes_dir = notes_dir or str(settings.investigation_notes_dir)
        os.makedirs(self.notes_dir, exist_ok=True)

    def _get_path(self, investigation_id: str) -> str:
        clean_id = investigation_id.replace("/", "_").replace("\\", "_")
        return os.path.join(self.notes_dir, f"{clean_id}.json")

    def add_note(self, note: AnalystNote) -> AnalystNote:
        notes = self.get_notes(note.investigation_id)
        notes.append(note)
        filepath = self._get_path(note.investigation_id)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump([n.dict() for n in notes], f, indent=2)
            logger.info("Added analyst note %s to investigation %s", note.note_id, note.investigation_id)
        except Exception as e:
            logger.error("Failed to persist analyst note: %s", e)
        return note

    def get_notes(self, investigation_id: str) -> List[AnalystNote]:
        filepath = self._get_path(investigation_id)
        if not os.path.exists(filepath):
            return []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [AnalystNote(**item) for item in data]
        except Exception as e:
            logger.error("Failed to load analyst notes from %s: %s", filepath, e)
            return []

    def delete_note(self, investigation_id: str, note_id: str) -> bool:
        notes = self.get_notes(investigation_id)
        filtered = [n for n in notes if n.note_id != note_id]
        if len(filtered) == len(notes):
            return False
        filepath = self._get_path(investigation_id)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump([n.dict() for n in filtered], f, indent=2)
            return True
        except Exception as e:
            logger.error("Failed to update notes after deletion: %s", e)
            return False


analyst_notes_store = AnalystNoteStore()
