import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from nas_core.config import get_settings
from nas_core.domain.programs import OncologyProgramCharter, ResearchQuestionIntake, StudyRole
from nas_core.domain.snapshots import write_dataset_snapshot_schema
from nas_core.governance.registry import SourceRegistry
from nas_core.ingestion.gdc import GDCSnapshotService, build_case_query
from nas_core.storage.layout import DataLayout
from nas_core.storage.object_store import S3ObjectStore
from nas_core.workflows.analysis_plan import load_analysis_plan, write_analysis_plan_schema
from nas_core.workflows.program import (
    load_program_charter,
    load_research_question,
    write_model_schema,
)
from nas_core.workflows.study_scaffold import (
    initialize_study,
    load_study_manifests,
    write_study_schemas,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nas-core")
    commands = parser.add_subparsers(dest="command", required=True)

    storage = commands.add_parser("storage", help="Manage the NaS Core data root")
    storage_commands = storage.add_subparsers(dest="storage_command", required=True)
    storage_commands.add_parser("init", help="Create and validate the data-root layout")
    storage_commands.add_parser("check", help="Validate the existing data-root layout")

    plan = commands.add_parser("plan", help="Manage versioned research analysis plans")
    plan_commands = plan.add_subparsers(dest="plan_command", required=True)
    validate = plan_commands.add_parser("validate", help="Validate a plan and its governance")
    validate.add_argument("path", type=Path, help="Path to analysis_plan.yaml")
    validate.add_argument(
        "--registry",
        type=Path,
        default=Path("data/source-registry.yaml"),
        help="Path to the governed source registry",
    )
    schema = plan_commands.add_parser("schema", help="Write the canonical plan JSON Schema")
    schema.add_argument("path", type=Path, help="Output path for the JSON Schema")

    ingest = commands.add_parser("ingest", help="Create governed dataset snapshots")
    ingest_commands = ingest.add_subparsers(dest="ingest_command", required=True)
    gdc = ingest_commands.add_parser("gdc-plan", help="Prepare or execute a GDC plan")
    gdc.add_argument("path", type=Path, help="Path to analysis_plan.yaml")
    gdc.add_argument(
        "--registry",
        type=Path,
        default=Path("data/source-registry.yaml"),
        help="Path to the governed source registry",
    )
    gdc.add_argument("--data-release", help="Exact GDC data release, for example 45.0")
    gdc.add_argument(
        "--execute",
        action="store_true",
        help="Fetch and persist data; requires a preregistered plan",
    )
    snapshot_schema = ingest_commands.add_parser(
        "schema", help="Write the canonical dataset-snapshot JSON Schema"
    )
    snapshot_schema.add_argument("path", type=Path, help="Output path for the JSON Schema")

    program = commands.add_parser("program", help="Manage research program charters")
    program_commands = program.add_subparsers(dest="program_command", required=True)
    program_validate = program_commands.add_parser("validate", help="Validate a program charter")
    program_validate.add_argument("path", type=Path, help="Path to program_charter.yaml")
    program_schema = program_commands.add_parser("schema", help="Write the program JSON Schema")
    program_schema.add_argument("path", type=Path, help="Output path for the JSON Schema")

    question = commands.add_parser("question", help="Manage decision-led research questions")
    question_commands = question.add_subparsers(dest="question_command", required=True)
    question_validate = question_commands.add_parser(
        "validate", help="Validate a research-question intake"
    )
    question_validate.add_argument("path", type=Path, help="Path to research_question.yaml")
    question_schema = question_commands.add_parser(
        "schema", help="Write the research-question JSON Schema"
    )
    question_schema.add_argument("path", type=Path, help="Output path for the JSON Schema")

    study = commands.add_parser("study", help="Create and validate standardized study workspaces")
    study_commands = study.add_subparsers(dest="study_command", required=True)
    study_init = study_commands.add_parser("init", help="Create a new study scaffold")
    study_init.add_argument("study_id", help="Permanent study ID, for example NAS-BRCA-002")
    study_init.add_argument("--slug", required=True, help="Lowercase underscore directory slug")
    study_init.add_argument("--title", required=True, help="Human-readable study title")
    study_init.add_argument("--program-id", required=True, help="Owning program ID")
    study_init.add_argument(
        "--role",
        required=True,
        choices=[role.value for role in StudyRole],
        help="Study's role in the research program",
    )
    study_init.add_argument(
        "--root",
        type=Path,
        default=Path("workflows/studies"),
        help="Directory that contains standardized study workspaces",
    )
    study_validate = study_commands.add_parser("validate", help="Validate a study workspace")
    study_validate.add_argument("path", type=Path, help="Path to a study workspace")
    study_schema = study_commands.add_parser("schema", help="Write canonical study schemas")
    study_schema.add_argument("study_path", type=Path, help="Output path for study schema")
    study_schema.add_argument("pipeline_path", type=Path, help="Output path for pipeline schema")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "storage" and args.storage_command == "init":
        layout = DataLayout(get_settings().data_root)
        layout.initialize()
        print(f"Initialized NaS Core data root: {layout.root}")
        return 0

    if args.command == "storage" and args.storage_command == "check":
        layout = DataLayout(get_settings().data_root)
        layout.validate()
        print(f"NaS Core data root is valid: {layout.root}")
        return 0

    if args.command == "plan" and args.plan_command == "validate":
        plan = load_analysis_plan(args.path, registry=SourceRegistry.from_yaml(args.registry))
        print(
            f"Analysis plan is valid: {plan.study_id} "
            f"v{plan.protocol_version} ({plan.status.value})"
        )
        return 0

    if args.command == "plan" and args.plan_command == "schema":
        write_analysis_plan_schema(args.path)
        print(f"Wrote analysis-plan schema: {args.path}")
        return 0

    if args.command == "ingest" and args.ingest_command == "gdc-plan":
        plan = load_analysis_plan(args.path, registry=SourceRegistry.from_yaml(args.registry))
        if not args.execute:
            print(json.dumps(build_case_query(plan, page_size=500), indent=2))
            print("Dry run only; no data was requested or stored.")
            return 0
        if not args.data_release:
            raise SystemExit("--data-release is required with --execute")
        snapshot = GDCSnapshotService(store=S3ObjectStore()).capture_cases(
            plan, data_release=args.data_release
        )
        print(
            f"Created immutable snapshot {snapshot.snapshot_id} "
            f"with {snapshot.record_count} records"
        )
        return 0

    if args.command == "ingest" and args.ingest_command == "schema":
        write_dataset_snapshot_schema(args.path)
        print(f"Wrote dataset-snapshot schema: {args.path}")
        return 0

    if args.command == "program" and args.program_command == "validate":
        program = load_program_charter(args.path)
        print(
            f"Program charter is valid: {program.program_id} "
            f"v{program.charter_version} ({program.current_stage.value})"
        )
        return 0

    if args.command == "program" and args.program_command == "schema":
        write_model_schema(args.path, OncologyProgramCharter)
        print(f"Wrote program-charter schema: {args.path}")
        return 0

    if args.command == "question" and args.question_command == "validate":
        question = load_research_question(args.path)
        print(
            f"Research question is valid: {question.question_id} "
            f"({question.status.value}; score {question.selection_scores.total}/40)"
        )
        return 0

    if args.command == "question" and args.question_command == "schema":
        write_model_schema(args.path, ResearchQuestionIntake)
        print(f"Wrote research-question schema: {args.path}")
        return 0

    if args.command == "study" and args.study_command == "init":
        path = initialize_study(
            args.root,
            study_id=args.study_id,
            slug=args.slug,
            title=args.title,
            program_id=args.program_id,
            role=StudyRole(args.role),
        )
        print(f"Created standardized study workspace: {path}")
        return 0

    if args.command == "study" and args.study_command == "validate":
        study, pipeline = load_study_manifests(args.path)
        print(
            f"Study workspace is valid: {study.study_id} "
            f"({study.status.value}; stage {pipeline.current_stage.value})"
        )
        return 0

    if args.command == "study" and args.study_command == "schema":
        write_study_schemas(args.study_path, args.pipeline_path)
        print(f"Wrote study schemas: {args.study_path}, {args.pipeline_path}")
        return 0

    raise AssertionError("Unreachable command")
