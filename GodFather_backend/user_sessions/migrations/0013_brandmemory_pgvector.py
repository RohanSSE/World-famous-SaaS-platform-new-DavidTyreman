import pgvector.django.indexes
import pgvector.django.vector
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user_sessions", "0012_aiusagelog_brandmemory"),
    ]

    operations = [
        migrations.AddField(
            model_name="brandmemory",
            name="agent_id",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
        migrations.AddField(
            model_name="brandmemory",
            name="embedding",
            field=pgvector.django.vector.VectorField(blank=True, dimensions=1536, null=True),
        ),
        migrations.AddField(
            model_name="brandmemory",
            name="importance_score",
            field=models.FloatField(default=0.5),
        ),
        migrations.AddIndex(
            model_name="brandmemory",
            index=pgvector.django.indexes.HnswIndex(
                ef_construction=64,
                fields=["embedding"],
                m=16,
                name="brand_memory_embedding_idx",
                opclasses=["vector_cosine_ops"],
            ),
        ),
    ]
