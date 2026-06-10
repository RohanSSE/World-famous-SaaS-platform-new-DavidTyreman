from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from brandgodfather.tasks import ingest_pdf_task
from brandgodfather.services.pdf_ingestion import PDFIngestionService


class Command(BaseCommand):
    help = "Dispatch Celery ingestion tasks for all BrandGodFather PDFs in a directory"

    def add_arguments(self, parser):
        parser.add_argument("--dir", default=None, help="Directory containing PDF files")
        parser.add_argument("--dry-run", action="store_true", help="List files without dispatching/ingesting")
        parser.add_argument(
            "--sync",
            action="store_true",
            help="Run ingestion inline instead of dispatching Celery tasks",
        )

    def handle(self, *args, **options):
        source = options.get("dir") or str(Path.cwd() / "RAG-docsv2")
        source_dir = Path(source).expanduser().resolve()
        if not source_dir.exists() or not source_dir.is_dir():
            raise CommandError(f"Invalid directory: {source_dir}")

        pdfs = sorted(
            path for path in source_dir.rglob("*") if path.is_file() and path.suffix.lower() == ".pdf"
        )
        if not pdfs:
            self.stdout.write(self.style.WARNING(f"No PDF files found under: {source_dir}"))
            return

        if options.get("dry_run"):
            self.stdout.write(self.style.MIGRATE_HEADING(f"Dry run for {len(pdfs)} PDFs"))
            for pdf_path in pdfs:
                self.stdout.write(f"- {pdf_path}")
            self.stdout.write(self.style.SUCCESS("Dry run complete."))
            return

        self.stdout.write(self.style.MIGRATE_HEADING(f"BrandGodFather ingest for {len(pdfs)} PDFs"))

        dispatched = 0
        indexed = 0
        failed = 0
        service = PDFIngestionService() if options.get("sync") else None
        for pdf_path in pdfs:
            metadata = {
                "source_dir": str(source_dir),
                "source_file": pdf_path.name,
            }
            if options.get("sync"):
                chunks = service.chunk_document(str(pdf_path), metadata=metadata)
                chunks = service.embed_chunks(chunks)
                result = service.ingest_to_es(chunks)
                indexed += int(result.get("success", 0))
                failed += int(result.get("failed", 0))
                dispatched += 1
                self.stdout.write(self.style.SUCCESS(f"Ingested: {pdf_path.name} ({result.get('success', 0)} chunks)"))
            else:
                ingest_pdf_task.delay(str(pdf_path), metadata)
                dispatched += 1
                self.stdout.write(self.style.SUCCESS(f"Queued: {pdf_path.name}"))

        self.stdout.write(self.style.MIGRATE_LABEL("\nBrandGodFather ingest dispatch summary"))
        self.stdout.write(f"- Directory: {source_dir}")
        self.stdout.write(f"- PDF files found: {len(pdfs)}")
        self.stdout.write(f"- Files processed: {dispatched}")
        if options.get("sync"):
            self.stdout.write(f"- Chunks indexed: {indexed}")
            self.stdout.write(f"- Chunks failed: {failed}")
