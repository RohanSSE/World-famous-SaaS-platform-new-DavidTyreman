from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from AdminAITuning.service import (
    get_train_bgf_state,
    load_default_tuning,
    save_section_tuning,
    train_section_tuning,
)


def _user_is_admin(user):
    return user.is_superuser or getattr(user, "has_role", lambda r: False)("admin")


section_key_param = openapi.Parameter(
    name="section_key",
    in_=openapi.IN_PATH,
    type=openapi.TYPE_STRING,
    enum=[
        "phase_1_master_prompt",
        "phase_2_master_prompt",
        "phase_3_master_prompt",
        "phase_4_master_prompt",
    ],
    required=True,
    description="Fine-tuning section identifier.",
)

limit_param = openapi.Parameter(
    name="limit",
    in_=openapi.IN_QUERY,
    type=openapi.TYPE_INTEGER,
    required=False,
    default=20,
    description="Max number of historical versions to return (1-100).",
)

section_payload_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=["prompt", "goal", "criteria"],
    properties={
        "active_pipeline": openapi.Schema(
            type=openapi.TYPE_STRING,
            enum=["rag_v1", "rag_v2"],
            description="BGF engine selector. rag_v1=engine1, rag_v2=engine2.",
        ),
        "prompt": openapi.Schema(type=openapi.TYPE_STRING),
        "goal": openapi.Schema(type=openapi.TYPE_STRING),
        "criteria": openapi.Schema(type=openapi.TYPE_STRING),
    },
)

version_item_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "id": openapi.Schema(type=openapi.TYPE_INTEGER),
        "version_number": openapi.Schema(type=openapi.TYPE_INTEGER),
        "action": openapi.Schema(type=openapi.TYPE_STRING, enum=["save", "train", "load_default"]),
        "section_key": openapi.Schema(type=openapi.TYPE_STRING),
        "active_pipeline": openapi.Schema(type=openapi.TYPE_STRING, enum=["rag_v1", "rag_v2"]),
        "snapshot": openapi.Schema(type=openapi.TYPE_OBJECT, additional_properties=True),
        "is_default_template": openapi.Schema(type=openapi.TYPE_BOOLEAN),
        "created_at": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
        "created_by": openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
    },
)

state_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "config": openapi.Schema(type=openapi.TYPE_OBJECT, additional_properties=True),
        "sections": openapi.Schema(type=openapi.TYPE_OBJECT, additional_properties=True),
        "default_template": version_item_schema,
        "versions": openapi.Schema(type=openapi.TYPE_ARRAY, items=version_item_schema),
    },
)


@swagger_auto_schema(
    method="get",
    tags=["Admin AI Tuning"],
    operation_id="admin_ai_tuning_state",
    operation_description="Get Train BGF state including current config, parsed section fields, DB default template, and version history.",
    manual_parameters=[limit_param],
    responses={
        200: openapi.Response("Train BGF state", state_response_schema),
        403: "Admin only",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_ai_tuning_state(request):
    if not _user_is_admin(request.user):
        return Response({"detail": "Admin only"}, status=status.HTTP_403_FORBIDDEN)

    limit = min(max(int(request.query_params.get("limit", 20)), 1), 100)
    return Response(get_train_bgf_state(limit=limit))


@swagger_auto_schema(
    method="post",
    tags=["Admin AI Tuning"],
    operation_id="admin_ai_tuning_load_default",
    operation_description="Load DB default fine-tuning template into active config and create a versioned audit entry.",
    responses={
        200: openapi.Response(
            "Default loaded",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "config": openapi.Schema(type=openapi.TYPE_OBJECT, additional_properties=True),
                    "version": version_item_schema,
                    "default_template": version_item_schema,
                },
            ),
        ),
        403: "Admin only",
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def admin_ai_tuning_load_default(request):
    if not _user_is_admin(request.user):
        return Response({"detail": "Admin only"}, status=status.HTTP_403_FORBIDDEN)

    result = load_default_tuning(updated_by=getattr(request.user, "email", "admin"))
    return Response(result)


@swagger_auto_schema(
    method="post",
    tags=["Admin AI Tuning"],
    operation_id="admin_ai_tuning_save_section",
    operation_description="Save one fine-tuning section and create a versioned snapshot entry in DB.",
    manual_parameters=[section_key_param],
    request_body=section_payload_schema,
    responses={
        200: openapi.Response(
            "Section saved",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "config": openapi.Schema(type=openapi.TYPE_OBJECT, additional_properties=True),
                    "version": version_item_schema,
                },
            ),
        ),
        400: "Invalid section_key",
        403: "Admin only",
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def admin_ai_tuning_save_section(request, section_key: str):
    if not _user_is_admin(request.user):
        return Response({"detail": "Admin only"}, status=status.HTTP_403_FORBIDDEN)

    section_data = {
        "prompt": request.data.get("prompt", ""),
        "goal": request.data.get("goal", ""),
        "criteria": request.data.get("criteria", ""),
    }
    active_pipeline = request.data.get("active_pipeline")

    try:
        result = save_section_tuning(
            section_key=section_key,
            section_data=section_data,
            active_pipeline=active_pipeline,
            updated_by=getattr(request.user, "email", "admin"),
        )
        return Response(result)
    except ValueError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method="post",
    tags=["Admin AI Tuning"],
    operation_id="admin_ai_tuning_train_section",
    operation_description="Section-specific AI training: save section, then trigger training flow and persist version history.",
    manual_parameters=[section_key_param],
    request_body=section_payload_schema,
    responses={
        200: openapi.Response(
            "Training started",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "section_key": openapi.Schema(type=openapi.TYPE_STRING),
                    "trained": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    "message": openapi.Schema(type=openapi.TYPE_STRING),
                    "config": openapi.Schema(type=openapi.TYPE_OBJECT, additional_properties=True),
                    "version": version_item_schema,
                },
            ),
        ),
        400: "Invalid section_key",
        403: "Admin only",
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def admin_ai_tuning_train_section(request, section_key: str):
    if not _user_is_admin(request.user):
        return Response({"detail": "Admin only"}, status=status.HTTP_403_FORBIDDEN)

    section_data = {
        "prompt": request.data.get("prompt", ""),
        "goal": request.data.get("goal", ""),
        "criteria": request.data.get("criteria", ""),
    }
    active_pipeline = request.data.get("active_pipeline")

    try:
        result = train_section_tuning(
            section_key=section_key,
            section_data=section_data,
            active_pipeline=active_pipeline,
            updated_by=getattr(request.user, "email", "admin"),
        )
        return Response(result)
    except ValueError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
