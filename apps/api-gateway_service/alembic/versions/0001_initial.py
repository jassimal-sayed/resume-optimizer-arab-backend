"""Initial schema for SmartResume Match"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    resume_source_enum = postgresql.ENUM("upload", "text", name="resume_source_enum")
    resume_source_enum.create(op.get_bind(), checkfirst=True)

    embedding_status_enum = postgresql.ENUM("pending", "indexed", "failed", name="embedding_status_enum")
    embedding_status_enum.create(op.get_bind(), checkfirst=True)

    job_status_enum = postgresql.ENUM("queued", "processing", "complete", "failed", name="job_status_enum")
    job_status_enum.create(op.get_bind(), checkfirst=True)

    task_type_enum = postgresql.ENUM("optimize", "embed_resume", "embed_job", name="task_type_enum")
    task_type_enum.create(op.get_bind(), checkfirst=True)

    task_status_enum = postgresql.ENUM("queued", "processing", "complete", "failed", name="task_status_enum")
    task_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("file_url", sa.Text(), nullable=True),
        sa.Column("active_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source", sa.Enum("upload", "text", name="resume_source_enum"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"])

    op.create_table(
        "resume_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("content_md", sa.Text(), nullable=True),
        sa.Column("parsed_json", sa.JSON(), nullable=True),
        sa.Column("embedding_status", sa.Enum("pending", "indexed", "failed", name="embedding_status_enum"), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_resume_versions_resume_id", "resume_versions", ["resume_id"])

    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column("job_description", sa.Text(), nullable=False),
        sa.Column("parsed_json", sa.JSON(), nullable=True),
        sa.Column("custom_instructions", sa.Text(), nullable=True),
        sa.Column("resume_lang", sa.String(length=4), nullable=False),
        sa.Column("jd_lang", sa.String(length=4), nullable=False),
        sa.Column("desired_output_lang", sa.String(length=4), nullable=False),
        sa.Column("status", sa.Enum("queued", "processing", "complete", "failed", name="job_status_enum"), nullable=False, server_default="queued"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("resume_lang in ('en','ar')", name="chk_resume_lang"),
        sa.CheckConstraint("jd_lang in ('en','ar')", name="chk_jd_lang"),
        sa.CheckConstraint("desired_output_lang in ('en','ar')", name="chk_desired_output_lang"),
    )
    op.create_index("ix_jobs_user_id", "jobs", ["user_id"])
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_index("ix_jobs_created_at", "jobs", ["created_at"])

    op.create_table(
        "optimizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resumes.id"), nullable=False),
        sa.Column("resume_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resume_versions.id"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("report_json", sa.JSON(), nullable=False),
        sa.Column("preview_md", sa.Text(), nullable=False),
        sa.Column("change_log", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_optimizations_user_id", "optimizations", ["user_id"])
    op.create_index("ix_optimizations_resume_id", "optimizations", ["resume_id"])
    op.create_index("ix_optimizations_resume_version_id", "optimizations", ["resume_version_id"])
    op.create_index("ix_optimizations_job_id", "optimizations", ["job_id"])
    op.create_index("ix_optimizations_created_at", "optimizations", ["created_at"])

    op.create_table(
        "task_queue",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("task_type", sa.Enum("optimize", "embed_resume", "embed_job", name="task_type_enum"), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.Enum("queued", "processing", "complete", "failed", name="task_status_enum"), nullable=False, server_default="queued"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_task_queue_status", "task_queue", ["status"])
    op.create_index("ix_task_queue_created_at", "task_queue", ["created_at"])

    op.create_table(
        "workflow_tokens",
        sa.Column("token", sa.String(length=255), primary_key=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Basic RLS policies (Supabase style). Adjust schema if using a schema prefix.
    op.execute("ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE resume_versions ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE optimizations ENABLE ROW LEVEL SECURITY;")

    op.execute("CREATE POLICY resumes_owner_policy ON resumes USING (user_id = auth.uid());")
    op.execute("CREATE POLICY resume_versions_owner_policy ON resume_versions USING (resume_id IN (SELECT id FROM resumes WHERE user_id = auth.uid()));")
    op.execute("CREATE POLICY jobs_owner_policy ON jobs USING (user_id = auth.uid());")
    op.execute("CREATE POLICY optimizations_owner_policy ON optimizations USING (user_id = auth.uid());")


def downgrade() -> None:
    op.drop_table("workflow_tokens")
    op.drop_index("ix_task_queue_created_at", table_name="task_queue")
    op.drop_index("ix_task_queue_status", table_name="task_queue")
    op.drop_table("task_queue")
    op.drop_table("optimizations")
    op.drop_table("jobs")
    op.drop_table("resume_versions")
    op.drop_table("resumes")

    op.execute("DROP POLICY IF EXISTS optimizations_owner_policy ON optimizations;")
    op.execute("DROP POLICY IF EXISTS jobs_owner_policy ON jobs;")
    op.execute("DROP POLICY IF EXISTS resume_versions_owner_policy ON resume_versions;")
    op.execute("DROP POLICY IF EXISTS resumes_owner_policy ON resumes;")

    op.execute("ALTER TABLE resumes DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE resume_versions DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE jobs DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE optimizations DISABLE ROW LEVEL SECURITY;")

    task_status_enum = postgresql.ENUM(name="task_status_enum")
    task_type_enum = postgresql.ENUM(name="task_type_enum")
    job_status_enum = postgresql.ENUM(name="job_status_enum")
    embedding_status_enum = postgresql.ENUM(name="embedding_status_enum")
    resume_source_enum = postgresql.ENUM(name="resume_source_enum")

    task_status_enum.drop(op.get_bind(), checkfirst=True)
    task_type_enum.drop(op.get_bind(), checkfirst=True)
    job_status_enum.drop(op.get_bind(), checkfirst=True)
    embedding_status_enum.drop(op.get_bind(), checkfirst=True)
    resume_source_enum.drop(op.get_bind(), checkfirst=True)
