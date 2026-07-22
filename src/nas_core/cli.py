import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from nas_core.ai.gateway import OpenAIScreeningGateway
from nas_core.ai.screening import AIAdvisoryScreeningService
from nas_core.analysis.cohort import CohortBuildService
from nas_core.analysis.survival import SurvivalAnalysisService
from nas_core.config import get_settings
from nas_core.domain.advisory import (
    load_ai_advisory_policy,
    write_ai_advisory_receipt,
    write_ai_advisory_schemas,
)
from nas_core.domain.cohorts import (
    load_cohort_receipt,
    load_snapshot_receipt,
    write_cohort_schemas,
)
from nas_core.domain.discovery import load_phase_zero_artifacts, write_discovery_schemas
from nas_core.domain.literature import (
    load_literature_search_receipt,
    load_screening_decision_batch,
    load_screening_progress_receipt,
    load_screening_queue_receipt,
    write_literature_schemas,
    write_screening_progress_receipt,
    write_screening_review_schemas,
)
from nas_core.domain.programs import OncologyProgramCharter, ResearchQuestionIntake, StudyRole
from nas_core.domain.snapshots import write_dataset_snapshot_schema
from nas_core.domain.survival import write_survival_schemas
from nas_core.governance.registry import SourceRegistry
from nas_core.ingestion.gdc import GDCSnapshotService, build_case_query
from nas_core.retrieval.literature import LiteratureSearchService
from nas_core.retrieval.review import ScreeningReviewService
from nas_core.retrieval.screening import ScreeningQueueService
from nas_core.storage.layout import DataLayout
from nas_core.storage.object_store import get_object_store
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
        "--release-notes-url",
        help="Official GDC release-notes URL that identifies the declared Data Release",
    )
    gdc.add_argument(
        "--execute",
        action="store_true",
        help="Fetch and persist data; requires a preregistered plan",
    )
    snapshot_schema = ingest_commands.add_parser(
        "schema", help="Write the canonical dataset-snapshot JSON Schema"
    )
    snapshot_schema.add_argument("path", type=Path, help="Output path for the JSON Schema")

    cohort = commands.add_parser("cohort", help="Build governed analysis-ready cohorts")
    cohort_commands = cohort.add_subparsers(dest="cohort_command", required=True)
    cohort_build = cohort_commands.add_parser("build", help="Prepare or execute cohort build")
    cohort_build.add_argument("plan", type=Path, help="Path to analysis_plan.yaml")
    cohort_build.add_argument("receipt", type=Path, help="Path to snapshot_receipt.yaml")
    cohort_build.add_argument(
        "--registry",
        type=Path,
        default=Path("data/source-registry.yaml"),
        help="Path to the governed source registry",
    )
    cohort_build.add_argument("--code-revision", required=True, help="Exact Git commit SHA")
    cohort_build.add_argument(
        "--execute",
        action="store_true",
        help="Read the frozen snapshot and persist cohort artifacts",
    )
    cohort_schema = cohort_commands.add_parser("schema", help="Write cohort JSON Schemas")
    cohort_schema.add_argument("qa_path", type=Path, help="Output path for QA schema")
    cohort_schema.add_argument("manifest_path", type=Path, help="Output path for manifest schema")
    cohort_schema.add_argument("receipt_path", type=Path, help="Output path for receipt schema")

    analysis = commands.add_parser("analysis", help="Run governed statistical analyses")
    analysis_commands = analysis.add_subparsers(dest="analysis_command", required=True)
    survival = analysis_commands.add_parser("survival", help="Prepare or execute survival models")
    survival.add_argument("plan", type=Path, help="Path to analysis_plan.yaml")
    survival.add_argument("receipt", type=Path, help="Path to cohort_build_receipt.yaml")
    survival.add_argument(
        "--registry",
        type=Path,
        default=Path("data/source-registry.yaml"),
        help="Path to the governed source registry",
    )
    survival.add_argument("--code-revision", required=True, help="Exact Git commit SHA")
    survival.add_argument(
        "--execute",
        action="store_true",
        help="Read the approved cohort and persist statistical artifacts",
    )
    survival_schema = analysis_commands.add_parser(
        "schema", help="Write survival result JSON Schemas"
    )
    survival_schema.add_argument("summary_path", type=Path, help="Output path for result schema")
    survival_schema.add_argument("manifest_path", type=Path, help="Output path for run schema")
    survival_schema.add_argument("receipt_path", type=Path, help="Output path for receipt schema")

    discovery = commands.add_parser("discovery", help="Manage discovery-study Phase 0 audits")
    discovery_commands = discovery.add_subparsers(dest="discovery_command", required=True)
    discovery_validate = discovery_commands.add_parser(
        "validate", help="Validate a Phase 0 novelty and feasibility package"
    )
    discovery_validate.add_argument("plan", type=Path, help="Path to phase_zero_plan.yaml")
    discovery_validate.add_argument("search", type=Path, help="Path to search_strategy.yaml")
    discovery_validate.add_argument("feasibility", type=Path, help="Path to data_feasibility.yaml")
    discovery_schema = discovery_commands.add_parser(
        "schema", help="Write Phase 0 discovery JSON Schemas"
    )
    discovery_schema.add_argument("plan_path", type=Path, help="Output path for plan schema")
    discovery_schema.add_argument("search_path", type=Path, help="Output path for search schema")
    discovery_schema.add_argument(
        "feasibility_path", type=Path, help="Output path for feasibility schema"
    )

    literature = commands.add_parser("literature", help="Capture governed evidence searches")
    literature_commands = literature.add_subparsers(dest="literature_command", required=True)
    literature_search = literature_commands.add_parser(
        "search", help="Prepare or execute a locked bibliographic search"
    )
    literature_search.add_argument("plan", type=Path, help="Path to phase_zero_plan.yaml")
    literature_search.add_argument("search", type=Path, help="Path to search_strategy.yaml")
    literature_search.add_argument("feasibility", type=Path, help="Path to data_feasibility.yaml")
    literature_search.add_argument(
        "--registry",
        type=Path,
        default=Path("data/source-registry.yaml"),
        help="Path to the governed source registry",
    )
    literature_search.add_argument(
        "--contact-email", help="Valid API contact email; hashed in the manifest"
    )
    literature_search.add_argument(
        "--execute", action="store_true", help="Contact APIs and persist immutable search exports"
    )
    literature_search.add_argument(
        "--count-only",
        action="store_true",
        help="Contact each API once for result counts without storing records",
    )
    literature_schema = literature_commands.add_parser(
        "schema", help="Write the literature-search snapshot JSON Schema"
    )
    literature_schema.add_argument("snapshot_path", type=Path, help="Snapshot schema output path")
    literature_schema.add_argument("receipt_path", type=Path, help="Receipt schema output path")
    literature_schema.add_argument(
        "screening_manifest_path", type=Path, help="Screening manifest schema output path"
    )
    literature_schema.add_argument(
        "screening_receipt_path", type=Path, help="Screening receipt schema output path"
    )
    screening_build = literature_commands.add_parser(
        "screening-build", help="Prepare or create an immutable human screening queue"
    )
    screening_build.add_argument("receipt", type=Path, help="Verified search_receipt.yaml")
    screening_build.add_argument("--code-revision", required=True, help="Exact Git commit SHA")
    screening_build.add_argument(
        "--execute", action="store_true", help="Read verified records and persist the queue"
    )
    screening_next = literature_commands.add_parser(
        "screening-next", help="Display the next resumable founder-review batch"
    )
    screening_next.add_argument("receipt", type=Path, help="Verified screening_queue_receipt.yaml")
    screening_next.add_argument(
        "--progress-receipt", type=Path, help="Latest verified screening progress receipt"
    )
    screening_next.add_argument("--batch-size", type=int, default=20, help="Records to display")
    screening_next.add_argument(
        "--include-unclear",
        action="store_true",
        help="Include records whose latest decision is unclear for adjudication",
    )
    screening_record = literature_commands.add_parser(
        "screening-record", help="Record and verify one immutable founder-review batch"
    )
    screening_record.add_argument(
        "receipt", type=Path, help="Verified screening_queue_receipt.yaml"
    )
    screening_record.add_argument(
        "decisions", type=Path, help="Typed screening decision batch YAML"
    )
    screening_record.add_argument(
        "--previous-progress-receipt", type=Path, help="Latest verified progress receipt"
    )
    screening_record.add_argument("--code-revision", required=True, help="Exact Git commit SHA")
    screening_record.add_argument(
        "--receipt-output", type=Path, help="New path for the verified aggregate progress receipt"
    )
    screening_record.add_argument(
        "--execute", action="store_true", help="Persist decision events and verify progress"
    )
    screening_review_schema = literature_commands.add_parser(
        "screening-review-schema", help="Write founder-review JSON Schemas"
    )
    screening_review_schema.add_argument(
        "decision_batch_path", type=Path, help="Decision-batch schema output path"
    )
    screening_review_schema.add_argument(
        "progress_manifest_path", type=Path, help="Progress-manifest schema output path"
    )
    screening_review_schema.add_argument(
        "progress_receipt_path", type=Path, help="Progress-receipt schema output path"
    )
    screening_ai = literature_commands.add_parser(
        "screening-ai", help="Run governed AI advisory screening without final decisions"
    )
    screening_ai.add_argument("receipt", type=Path, help="Verified screening queue receipt")
    screening_ai.add_argument("policy", type=Path, help="Locked AI screening policy YAML")
    screening_ai.add_argument(
        "--progress-receipt", type=Path, help="Latest verified founder progress receipt"
    )
    screening_ai.add_argument("--code-revision", required=True, help="Exact Git commit SHA")
    screening_ai.add_argument(
        "--receipt-output", type=Path, help="New path for the aggregate AI advisory receipt"
    )
    screening_ai.add_argument(
        "--execute", action="store_true", help="Send pending records to the configured provider"
    )
    screening_ai_schema = literature_commands.add_parser(
        "screening-ai-schema", help="Write AI advisory screening JSON Schemas"
    )
    screening_ai_schema.add_argument("output_path", type=Path)
    screening_ai_schema.add_argument("manifest_path", type=Path)
    screening_ai_schema.add_argument("receipt_path", type=Path)

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
        if not args.release_notes_url:
            raise SystemExit("--release-notes-url is required with --execute")
        snapshot = GDCSnapshotService(store=get_object_store()).capture_cases(
            plan,
            data_release=args.data_release,
            release_notes_url=args.release_notes_url,
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

    if args.command == "cohort" and args.cohort_command == "build":
        plan = load_analysis_plan(args.plan, registry=SourceRegistry.from_yaml(args.registry))
        receipt = load_snapshot_receipt(args.receipt)
        if not args.execute:
            print(
                f"Cohort build ready: {plan.study_id} protocol {plan.protocol_version}, "
                f"snapshot {receipt.snapshot_id}, code {args.code_revision}"
            )
            print("Dry run only; no snapshot records were read and no artifacts were stored.")
            return 0
        manifest = CohortBuildService(store=get_object_store()).build(
            plan,
            receipt,
            code_revision=args.code_revision,
        )
        print(
            f"Created immutable cohort build {manifest.build_id}: "
            f"{manifest.included_case_count} included, "
            f"{manifest.excluded_case_count} excluded"
        )
        return 0

    if args.command == "cohort" and args.cohort_command == "schema":
        write_cohort_schemas(args.qa_path, args.manifest_path, args.receipt_path)
        print(f"Wrote cohort schemas: {args.qa_path}, {args.manifest_path}, {args.receipt_path}")
        return 0

    if args.command == "analysis" and args.analysis_command == "survival":
        plan = load_analysis_plan(args.plan, registry=SourceRegistry.from_yaml(args.registry))
        cohort_receipt = load_cohort_receipt(args.receipt)
        if not args.execute:
            print(
                f"Survival analysis ready: {plan.study_id} protocol {plan.protocol_version}, "
                f"cohort {cohort_receipt.build_id}, gate {cohort_receipt.qa_gate_status.value}, "
                f"code {args.code_revision}"
            )
            print("Dry run only; no cohort rows were read and no models were fitted.")
            return 0
        run_manifest = SurvivalAnalysisService(store=get_object_store()).run(
            plan,
            cohort_receipt,
            code_revision=args.code_revision,
        )
        print(f"Created immutable survival run {run_manifest.run_id}")
        return 0

    if args.command == "analysis" and args.analysis_command == "schema":
        write_survival_schemas(args.summary_path, args.manifest_path, args.receipt_path)
        print(
            "Wrote survival schemas: "
            f"{args.summary_path}, {args.manifest_path}, {args.receipt_path}"
        )
        return 0

    if args.command == "discovery" and args.discovery_command == "validate":
        phase_zero, search, feasibility = load_phase_zero_artifacts(
            args.plan,
            args.search,
            args.feasibility,
        )
        print(
            f"Phase 0 package is valid: {phase_zero.study_id} "
            f"question {phase_zero.question_id} v{phase_zero.question_version}; "
            f"search {search.status.value}; feasibility {feasibility.status.value}"
        )
        return 0

    if args.command == "discovery" and args.discovery_command == "schema":
        write_discovery_schemas(args.plan_path, args.search_path, args.feasibility_path)
        print(
            "Wrote discovery schemas: "
            f"{args.plan_path}, {args.search_path}, {args.feasibility_path}"
        )
        return 0

    if args.command == "literature" and args.literature_command == "search":
        phase_zero, search, _ = load_phase_zero_artifacts(
            args.plan,
            args.search,
            args.feasibility,
        )
        if args.execute and args.count_only:
            raise SystemExit("choose either --execute or --count-only")
        if not args.execute and not args.count_only:
            for source in search.sources:
                print(f"{source.source_id}: {source.query}")
            print("Dry run only; no literature API was contacted and nothing was stored.")
            return 0
        if not args.contact_email:
            raise SystemExit("--contact-email is required with --execute or --count-only")
        literature_service = LiteratureSearchService(
            store=get_object_store(),
            registry=SourceRegistry.from_yaml(args.registry),
        )
        if args.count_only:
            counts = literature_service.preview_counts(
                phase_zero,
                search,
                contact_email=args.contact_email,
            )
            print(json.dumps(counts, indent=2, sort_keys=True))
            print("Count preview only; no literature records or manifests were stored.")
            return 0
        literature_snapshot = literature_service.capture(
            phase_zero,
            search,
            contact_email=args.contact_email,
        )
        print(
            f"Created immutable literature search {literature_snapshot.execution_id}: "
            f"{literature_snapshot.unique_record_count} unique records, "
            f"{literature_snapshot.duplicate_record_count} duplicates"
        )
        return 0

    if args.command == "literature" and args.literature_command == "schema":
        write_literature_schemas(
            args.snapshot_path,
            args.receipt_path,
            args.screening_manifest_path,
            args.screening_receipt_path,
        )
        print(
            "Wrote literature schemas: "
            f"{args.snapshot_path}, {args.receipt_path}, "
            f"{args.screening_manifest_path}, {args.screening_receipt_path}"
        )
        return 0

    if args.command == "literature" and args.literature_command == "screening-build":
        screening_receipt = load_literature_search_receipt(args.receipt)
        if not args.execute:
            print(
                f"Screening queue ready: {screening_receipt.study_id}, "
                f"search {screening_receipt.execution_id}, "
                f"{screening_receipt.unique_record_count} records, code {args.code_revision}"
            )
            print("Dry run only; no literature records were read and no queue was stored.")
            return 0
        queue = ScreeningQueueService(store=get_object_store()).build(
            screening_receipt,
            code_revision=args.code_revision,
        )
        print(
            f"Created immutable screening queue {queue.queue_id}: "
            f"{queue.summary.pending_record_count} pending human decisions"
        )
        return 0

    if args.command == "literature" and args.literature_command == "screening-next":
        queue_receipt = load_screening_queue_receipt(args.receipt)
        progress_receipt = (
            load_screening_progress_receipt(args.progress_receipt)
            if args.progress_receipt
            else None
        )
        review_batch = ScreeningReviewService(store=get_object_store()).next_batch(
            queue_receipt,
            progress_receipt=progress_receipt,
            batch_size=args.batch_size,
            include_unclear=args.include_unclear,
        )
        print(json.dumps(review_batch.model_dump(mode="json", exclude_none=True), indent=2))
        return 0

    if args.command == "literature" and args.literature_command == "screening-record":
        queue_receipt = load_screening_queue_receipt(args.receipt)
        decision_batch = load_screening_decision_batch(args.decisions)
        progress_receipt = (
            load_screening_progress_receipt(args.previous_progress_receipt)
            if args.previous_progress_receipt
            else None
        )
        review_service = ScreeningReviewService(store=get_object_store())
        if not args.execute:
            review_service.validate_batch(
                queue_receipt,
                decision_batch,
                code_revision=args.code_revision,
                progress_receipt=progress_receipt,
            )
            print(
                f"Review batch is valid: {len(decision_batch.decisions)} founder decisions "
                f"for queue {decision_batch.queue_id}, code {args.code_revision}"
            )
            print("Dry run only; no queue records were read and no decisions were stored.")
            return 0
        if args.receipt_output is None:
            raise SystemExit("--receipt-output is required with --execute")
        progress = review_service.record_batch(
            queue_receipt,
            decision_batch,
            code_revision=args.code_revision,
            progress_receipt=progress_receipt,
        )
        verified_receipt = review_service.verify(queue_receipt, progress)
        write_screening_progress_receipt(args.receipt_output, verified_receipt)
        print(
            f"Recorded immutable screening progress {progress.progress_id}: "
            f"{progress.summary.decided_record_count}/"
            f"{progress.summary.total_record_count} records decided"
        )
        print(f"Wrote verified aggregate receipt: {args.receipt_output}")
        return 0

    if args.command == "literature" and args.literature_command == "screening-review-schema":
        write_screening_review_schemas(
            args.decision_batch_path,
            args.progress_manifest_path,
            args.progress_receipt_path,
        )
        print(
            "Wrote screening-review schemas: "
            f"{args.decision_batch_path}, {args.progress_manifest_path}, "
            f"{args.progress_receipt_path}"
        )
        return 0

    if args.command == "literature" and args.literature_command == "screening-ai":
        queue_receipt = load_screening_queue_receipt(args.receipt)
        ai_policy = load_ai_advisory_policy(args.policy)
        ai_prompt = Path(ai_policy.prompt_path).read_text(encoding="utf-8")
        progress_receipt = (
            load_screening_progress_receipt(args.progress_receipt)
            if args.progress_receipt
            else None
        )
        if not args.execute:
            print(
                f"AI advisory screening ready: queue {queue_receipt.queue_id}, "
                f"policy {ai_policy.policy_version}, {ai_policy.model}, "
                f"up to {ai_policy.max_records_per_call} records"
            )
            print("Dry run only; no queue records were read and no provider was contacted.")
            return 0
        if args.receipt_output is None:
            raise SystemExit("--receipt-output is required with --execute")
        settings = get_settings()
        gateway = OpenAIScreeningGateway(
            api_key=settings.openai_api_key,
            model=ai_policy.model,
            reasoning_effort=ai_policy.reasoning_effort,
        )
        ai_service = AIAdvisoryScreeningService(
            store=get_object_store(settings),
            gateway=gateway,
        )
        advisory_manifest = ai_service.run(
            queue_receipt,
            ai_policy,
            prompt_text=ai_prompt,
            code_revision=args.code_revision,
            progress_receipt=progress_receipt,
        )
        verified = ai_service.verify(advisory_manifest)
        write_ai_advisory_receipt(args.receipt_output, verified)
        print(
            f"Created verified AI advisory run {advisory_manifest.advisory_run_id}: "
            f"{advisory_manifest.summary.recommendation_count} recommendations, "
            "zero final decisions"
        )
        return 0

    if args.command == "literature" and args.literature_command == "screening-ai-schema":
        write_ai_advisory_schemas(args.output_path, args.manifest_path, args.receipt_path)
        print(
            f"Wrote AI advisory schemas: {args.output_path}, "
            f"{args.manifest_path}, {args.receipt_path}"
        )
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
