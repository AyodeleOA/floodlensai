"""Initial schema for FloodLens AI

Revision ID: 0001_initial
Revises:
Create Date: 2024-11-01
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- organisations ---
    op.create_table(
        "organisations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("organisation_type", sa.String(100), nullable=True),
        sa.Column("city", sa.String(255), nullable=True),
        sa.Column("country_code", sa.String(2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("auth_subject", sa.String(255), nullable=True, index=True),
        sa.Column("role", sa.String(50), nullable=False, server_default="public", index=True),
        sa.Column("organisation_id", UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- reports ---
    op.create_table(
        "reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("reporter_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("organisation_id", UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=True),
        sa.Column("report_type", sa.String(100), nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("latitude", sa.Float, nullable=False, index=True),
        sa.Column("longitude", sa.Float, nullable=False, index=True),
        sa.Column("reported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("status", sa.String(50), nullable=False, server_default="submitted", index=True),
        sa.Column("source_channel", sa.String(50), nullable=False, server_default="web"),
        sa.Column("is_synthetic", sa.Boolean, server_default=sa.text("false")),
        sa.Column("duplicate_of_report_id", UUID(as_uuid=True), sa.ForeignKey("reports.id"), nullable=True),
        sa.Column("hazard_type", sa.String(100), nullable=True),
        sa.Column("severity", sa.String(50), nullable=True),
        sa.Column("landmark", sa.String(255), nullable=True),
        sa.Column("water_level", sa.String(50), nullable=True),
        sa.Column("affects_roads", sa.Boolean, nullable=True),
        sa.Column("affects_homes", sa.Boolean, nullable=True),
        sa.Column("affects_shops", sa.Boolean, nullable=True),
        sa.Column("affects_facilities", sa.Boolean, nullable=True),
        sa.Column("reporter_contact", sa.String(255), nullable=True),
        sa.Column("privacy_consent", sa.Boolean, server_default=sa.text("false")),
        sa.Column("voice_transcript", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- media_assets ---
    op.create_table(
        "media_assets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("report_id", UUID(as_uuid=True), sa.ForeignKey("reports.id"), nullable=False, index=True),
        sa.Column("s3_key", sa.String(512), nullable=False),
        sa.Column("media_type", sa.String(50), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False, index=True),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("exif_removed", sa.Boolean, server_default=sa.text("false")),
        sa.Column("processing_status", sa.String(50), server_default="pending", index=True),
        sa.Column("public_thumbnail_key", sa.String(512), nullable=True),
    )

    # --- ai_analyses ---
    op.create_table(
        "ai_analyses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("report_id", UUID(as_uuid=True), sa.ForeignKey("reports.id"), nullable=False, index=True),
        sa.Column("media_asset_id", UUID(as_uuid=True), sa.ForeignKey("media_assets.id"), nullable=False, index=True),
        sa.Column("provider", sa.String(100), nullable=False, index=True),
        sa.Column("model_id", sa.String(100), nullable=False),
        sa.Column("model_version", sa.String(100), nullable=True),
        sa.Column("prompt_version", sa.String(50), nullable=True),
        sa.Column("status", sa.String(50), server_default="pending", index=True),
        sa.Column("scene_summary", sa.Text, nullable=True),
        sa.Column("structured_result", JSONB, nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("limitations", JSONB, nullable=True),
        sa.Column("request_id", sa.String(255), nullable=True),
        sa.Column("processing_ms", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- segmentation_assets ---
    op.create_table(
        "segmentation_assets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("media_asset_id", UUID(as_uuid=True), sa.ForeignKey("media_assets.id"), nullable=False, index=True),
        sa.Column("provider", sa.String(100), nullable=False, index=True),
        sa.Column("model_id", sa.String(100), nullable=False),
        sa.Column("prompt_text", sa.Text, nullable=True),
        sa.Column("mask_s3_key", sa.String(512), nullable=True),
        sa.Column("bounding_boxes", JSONB, nullable=True),
        sa.Column("object_labels", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- data_sources ---
    op.create_table(
        "data_sources",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("source_type", sa.String(100), nullable=False),
        sa.Column("licence", sa.String(255), nullable=True),
        sa.Column("attribution", sa.Text, nullable=True),
        sa.Column("source_url", sa.String(512), nullable=True),
        sa.Column("spatial_coverage", sa.String(255), nullable=True),
        sa.Column("temporal_coverage", sa.String(255), nullable=True),
        sa.Column("update_frequency", sa.String(100), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(50), server_default="unknown", index=True),
        sa.Column("limitations", sa.Text, nullable=True),
        sa.Column("metadata", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- environmental_observations ---
    op.create_table(
        "environmental_observations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", UUID(as_uuid=True), sa.ForeignKey("data_sources.id"), nullable=False, index=True),
        sa.Column("observation_type", sa.String(100), nullable=False, index=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("value", sa.Float, nullable=True),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("quality_flag", sa.String(50), nullable=True),
        sa.Column("raw_s3_key", sa.String(512), nullable=True),
        sa.Column("metadata", JSONB, nullable=True),
        sa.Column("geometry_wkt", sa.String(2048), nullable=True),
        sa.Column("latitude", sa.Float, nullable=True),
        sa.Column("longitude", sa.Float, nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- risk_cells ---
    op.create_table(
        "risk_cells",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("grid_system", sa.String(50), server_default="h3", index=True),
        sa.Column("grid_index", sa.String(255), nullable=False, index=True),
        sa.Column("geometry_wkt", sa.String(2048), nullable=True),
        sa.Column("latitude", sa.Float, nullable=False, index=True),
        sa.Column("longitude", sa.Float, nullable=False, index=True),
        sa.Column("risk_score", sa.Float, server_default="0", index=True),
        sa.Column("risk_band", sa.String(50), server_default="low", index=True),
        sa.Column("confidence_score", sa.Float, server_default="0"),
        sa.Column("data_completeness", sa.Float, server_default="0"),
        sa.Column("contributing_factors", JSONB, nullable=True),
        sa.Column("missing_inputs", JSONB, nullable=True),
        sa.Column("source_ids", JSONB, nullable=True),
        sa.Column("calculation_version", sa.String(50), server_default="0.1.0"),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_illustrative", sa.Boolean, server_default=sa.text("false")),
    )

    # --- risk_cell_evidence ---
    op.create_table(
        "risk_cell_evidence",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("risk_cell_id", UUID(as_uuid=True), sa.ForeignKey("risk_cells.id"), nullable=False, index=True),
        sa.Column("evidence_type", sa.String(100), nullable=False),
        sa.Column("evidence_id", sa.String(255), nullable=False),
        sa.Column("contribution", sa.Float, nullable=True),
        sa.Column("source_timestamp", sa.DateTime(timezone=True), nullable=True),
    )

    # --- moderation_actions ---
    op.create_table(
        "moderation_actions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("report_id", UUID(as_uuid=True), sa.ForeignKey("reports.id"), nullable=False, index=True),
        sa.Column("moderator_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("previous_status", sa.String(50), nullable=False),
        sa.Column("new_status", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- audit_logs ---
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("actor_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(255), nullable=False, index=True),
        sa.Column("resource_type", sa.String(100), nullable=False, index=True),
        sa.Column("resource_id", sa.String(255), nullable=True, index=True),
        sa.Column("metadata", JSONB, nullable=True),
        sa.Column("ip_hash", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- notifications ---
    op.create_table(
        "notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("recipient_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("message_template", sa.String(255), nullable=False),
        sa.Column("payload", JSONB, nullable=True),
        sa.Column("status", sa.String(50), server_default="pending", index=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("audit_logs")
    op.drop_table("moderation_actions")
    op.drop_table("risk_cell_evidence")
    op.drop_table("risk_cells")
    op.drop_table("environmental_observations")
    op.drop_table("data_sources")
    op.drop_table("segmentation_assets")
    op.drop_table("ai_analyses")
    op.drop_table("media_assets")
    op.drop_table("reports")
    op.drop_table("users")
    op.drop_table("organisations")
