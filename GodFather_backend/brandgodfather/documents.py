from django.conf import settings
from elasticsearch_dsl import (
    Boolean,
    Date,
    DenseVector,
    Document,
    Float,
    Integer,
    Keyword,
    Nested,
    Object,
    Text,
    connections,
)

BRANDGODFATHER_NODE_2_ALIAS = "brandgodfather_node_2"


# Use a dedicated alias so BrandGodFather mappings can be created on Node 2 only.
connections.create_connection(alias=BRANDGODFATHER_NODE_2_ALIAS, hosts=[settings.ES_NODE_2])


class BrandGodFatherBrandChunkDocument(Document):
    chunk_id = Keyword()
    text = Text(fields={"keyword": Keyword()})
    dense_vector = DenseVector(dims=1536)
    chunk_type = Keyword()
    phase = Keyword()
    question_id = Keyword()
    brand_type = Keyword()
    emotional_register = Keyword()

    class Index:
        name = "brandgodfather_brand_chunks"


# Backward-compatible alias for existing references.
BrandGodFatherChunk = BrandGodFatherBrandChunkDocument


class BrandGodFatherSessionDocument(Document):
    session_id = Keyword()
    user_id = Keyword()
    current_phase = Keyword()
    current_q_id = Keyword()
    brand_seed = Keyword()
    tension = Text()
    three_word_foundation = Object(
        properties={
            "value1": Keyword(),
            "value2": Keyword(),
            "value3": Keyword(),
        }
    )
    line_in_sand = Text()
    wom_trigger = Text()
    brand_promise = Text()
    shadow_profile = Object(
        properties={
            "self_image": Keyword(),
            "actual_signal": Keyword(),
            "gap_score": Float(),
            "fear_pattern": Keyword(),
            "avoidance_topic": Keyword(),
            "readiness_estimate": Float(),
        }
    )
    thread_index = Object(dynamic=True)
    all_answers = Nested(
        properties={
            "q_id": Keyword(),
            "raw_answer": Text(),
            "status": Keyword(),
            "timestamp": Date(),
        }
    )
    created_at = Date()
    updated_at = Date()

    class Index:
        name = "brandgodfather_sessions"


class BrandGodFatherEpisodicDocument(Document):
    session_id = Keyword()
    q_id = Keyword()
    raw_answer = Text()
    emotional_weight = Float()
    resistance_level = Keyword()
    resistance_count = Integer()
    prosody_flags = Keyword(multi=True)
    key_phrase = Keyword()
    contradiction_flags = Keyword(multi=True)
    pressure_level_used = Integer()
    brand_seed_echo = Boolean()
    timestamp = Date()

    class Index:
        name = "brandgodfather_episodic"


class BrandGodFatherOutputContentDocument(Document):
    session_id = Keyword()
    content_type = Keyword()
    content = Object(dynamic=True)
    week_number = Integer()
    brand_filter_result = Object(dynamic=True)
    created_at = Date()

    class Index:
        name = "brandgodfather_output_content"
