"""
Build or refresh the AI knowledge vector index from utils knowledge files.
Usage: python manage.py build_ai_knowledge
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Build/refresh the AI knowledge Elasticsearch index from utils/training-AI-tool.txt and after-manifesto-ai-tool.txt"

    def handle(self, *args, **options):
        from utils.build_ai_knowledge_index import run_build
        success, message = run_build()
        if success:
            self.stdout.write(self.style.SUCCESS(message))
        else:
            self.stderr.write(self.style.ERROR(message))
