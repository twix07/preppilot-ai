"""Resume ingestion (direct context). Text stored encrypted at rest; PDF parse for E1."""
from __future__ import annotations

import io
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, PayloadTooLargeError, ValidationAppError
from app.core.security import decrypt_text, encrypt_text
from app.models import Resume
from app.repositories.repositories import ResumeRepository

MAX_PDF_BYTES = 5 * 1024 * 1024
MAX_TEXT_CHARS = 20000


class ResumeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ResumeRepository(db)

    async def create_from_text(self, user_id: str, raw_text: str) -> Resume:
        text = (raw_text or "").strip()
        if len(text) < 20:
            raise ValidationAppError("Resume text is too short to be useful.")
        if len(text) > MAX_TEXT_CHARS:
            raise PayloadTooLargeError("Resume text is too long. Please trim it.")
        resume = Resume(
            user_id=user_id, raw_text_enc=encrypt_text(text), source="paste", char_count=len(text)
        )
        await self.repo.add(resume)
        await self.db.commit()
        return resume

    async def create_from_pdf(self, user_id: str, filename: str, data: bytes) -> Resume:
        if not filename.lower().endswith(".pdf"):
            raise ValidationAppError("Only PDF files are supported.")
        if len(data) > MAX_PDF_BYTES:
            raise PayloadTooLargeError("PDF exceeds the 5 MB limit.")
        text = self._extract_pdf_text(data)
        if len(text.strip()) < 20:
            raise ValidationAppError("Could not read enough text from that PDF.")
        resume = Resume(
            user_id=user_id,
            raw_text_enc=encrypt_text(text.strip()),
            source="pdf",
            char_count=len(text.strip()),
        )
        await self.repo.add(resume)
        await self.db.commit()
        return resume

    @staticmethod
    def _extract_pdf_text(data: bytes) -> str:
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(data))
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception as exc:  # noqa: BLE001
            raise ValidationAppError("That PDF could not be parsed (it may be corrupt).") from exc

    async def get_owned_text(self, user_id: str, resume_id: str | None) -> tuple[str | None, str]:
        """Return (resume_id, decrypted_text) for an owned resume, or (None, '')."""
        if not resume_id:
            return None, ""
        resume = await self.repo.get(resume_id)
        if resume is None:
            return None, ""
        if resume.user_id != user_id:
            raise ForbiddenError("You do not have access to that resume.")
        resume.last_used_at = datetime.now(timezone.utc)
        return resume.id, decrypt_text(resume.raw_text_enc)
