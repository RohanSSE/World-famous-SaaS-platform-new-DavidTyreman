import pgvector.django.indexes
import pgvector.django.vector
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai_knowledge", "0001_enable_pgvector"),
    ]

    operations = [
        migrations.CreateModel(
            name="AIKnowledgeChunk",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("chunk_id", models.IntegerField(db_index=True, unique=True)),
                ("title", models.CharField(blank=True, default="", max_length=500)),
                ("content", models.TextField()),
                ("embedding", pgvector.django.vector.VectorField(dimensions=1536)),
                ("category", models.CharField(db_index=True, default="knowledge", max_length=100)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("document_id", models.IntegerField(blank=True, null=True)),
                ("page_number", models.IntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "ai_knowledge_chunk",
                "ordering": ["chunk_id"],
                "indexes": [
                    pgvector.django.indexes.HnswIndex(
                        ef_construction=64,
                        fields=["embedding"],
                        m=16,
                        name="ai_knowledge_embedding_idx",
                        opclasses=["vector_cosine_ops"],
                    ),
                ],
            },
        ),
    ]
