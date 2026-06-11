from django.urls import path

from AdminAITuning.views import (
    admin_ai_tuning_activate_engine,
    admin_ai_tuning_load_default,
    admin_ai_tuning_save_section,
    admin_ai_tuning_state,
    admin_ai_tuning_train_section,
)

urlpatterns = [
    path("", admin_ai_tuning_state, name="admin-ai-tuning-state"),
    path("load-default/", admin_ai_tuning_load_default, name="admin-ai-tuning-load-default"),
    path("engine/", admin_ai_tuning_activate_engine, name="admin-ai-tuning-activate-engine"),
    path("sections/<str:section_key>/save/", admin_ai_tuning_save_section, name="admin-ai-tuning-save-section"),
    path("sections/<str:section_key>/train/", admin_ai_tuning_train_section, name="admin-ai-tuning-train-section"),
]
