from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from brandgodfather.tasks import ingest_pdf_task


class Command(BaseCommand):
    help = "Dispatch Celery ingestion tasks for all BrandGodFather PDFs in a directory"

    def add_arguments(self, parser):
        parser.add_argument("--dir", required=True, help="Directory containing PDF files")

    def handle(self, *args, **options):
        source_dir = Path(options["dir"]).expanduser().resolve()
        if not source_dir.exists() or not source_dir.is_dir():
            raise CommandError(f"Invalid directory: {source_dir}")

        pdfs = sorted(
            path for path in source_dir.rglob("*") if path.is_file() and path.suffix.lower() == ".pdf"
        )
        if not pdfs:
            self.stdout.write(self.style.WARNING(f"No PDF files found under: {source_dir}"))
            return

        self.stdout.write(self.style.MIGRATE_HEADING(f"Dispatching BrandGodFather ingest for {len(pdfs)} PDFs"))

        dispatched = 0
        for pdf_path in pdfs:
            metadata = {
                "source_dir": str(source_dir),
                "source_file": pdf_path.name,
            }
            ingest_pdf_task.delay(str(pdf_path), metadata)
            dispatched += 1
            self.stdout.write(self.style.SUCCESS(f"Queued: {pdf_path.name}"))

        self.stdout.write(self.style.MIGRATE_LABEL("\nBrandGodFather ingest dispatch summary"))
        self.stdout.write(f"- Directory: {source_dir}")
        self.stdout.write(f"- PDF files found: {len(pdfs)}")
        self.stdout.write(f"- Tasks dispatched: {dispatched}")
