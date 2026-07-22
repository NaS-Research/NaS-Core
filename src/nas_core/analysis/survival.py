"""Governed deterministic survival analysis for the NAS-BRCA-001 pilot."""

from __future__ import annotations

import io
import json
import platform
import warnings
from collections.abc import Callable
from datetime import UTC, datetime
from importlib.metadata import version
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter  # type: ignore[import-untyped]
from lifelines.exceptions import ConvergenceError  # type: ignore[import-untyped]
from lifelines.statistics import (  # type: ignore[import-untyped]
    logrank_test,
    proportional_hazard_test,
)
from matplotlib import pyplot as plt

from nas_core.domain.cohorts import CohortBuildManifest, CohortBuildReceipt, CohortGateStatus
from nas_core.domain.research import AnalysisPlan, PlanStatus, ReviewDecision
from nas_core.domain.survival import (
    AnalysisArtifact,
    AnalysisStatus,
    CoefficientEstimate,
    EditionDistribution,
    GroupSummary,
    InfluenceObservation,
    LogRankResult,
    ModelResult,
    PHDiagnostic,
    QualificationDecision,
    RiskTableRow,
    SurvivalAnalysisSummary,
    SurvivalRunManifest,
)
from nas_core.ingestion.gdc import canonical_json, sha256
from nas_core.storage.object_store import ObjectStore

matplotlib.use("Agg")

ALGORITHM_VERSION = "tcga-brca-survival-1.0.0"
RANDOM_SEED = 20260721
FIVE_YEARS_DAYS = 365.25 * 5
MINIMUM_GROUP_EVENTS = 10
PH_ALPHA = 0.05
JSON_MEDIA_TYPE = "application/json"
CSV_MEDIA_TYPE = "text/csv"
PNG_MEDIA_TYPE = "image/png"


class SurvivalAnalysisError(RuntimeError):
    """Raised when a governed analysis cannot safely execute."""


class SurvivalAnalysisService:
    """Execute the locked analysis plan and persist content-addressed outputs."""

    def __init__(
        self,
        *,
        store: ObjectStore,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store
        self._clock = clock or (lambda: datetime.now(UTC))

    def run(
        self,
        plan: AnalysisPlan,
        receipt: CohortBuildReceipt,
        *,
        code_revision: str,
    ) -> SurvivalRunManifest:
        self._validate_gate(plan, receipt, code_revision)
        cohort = self._load_verified_cohort(receipt)
        self._validate_cohort(cohort, receipt)

        parameters: dict[str, object] = {
            "alpha": plan.primary_model.alpha,
            "five_years_days": FIVE_YEARS_DAYS,
            "minimum_group_events": MINIMUM_GROUP_EVENTS,
            "ph_alpha": PH_ALPHA,
            "random_seed": RANDOM_SEED,
            "spline_percentiles": [5, 35, 65, 95],
        }
        identity = {
            "algorithm_version": ALGORITHM_VERSION,
            "code_revision": code_revision,
            "cohort_build_id": receipt.build_id,
            "cohort_manifest_sha256": receipt.manifest_sha256,
            "parameters": parameters,
            "protocol_version": plan.protocol_version,
            "study_id": plan.study_id,
        }
        run_id = sha256(canonical_json(identity))
        prefix = f"analysis-runs/{plan.study_id}/{receipt.build_id}/{run_id}"

        summary, tables, figure = self._analyze(plan, receipt, cohort)
        artifact_payloads = (
            (
                "analysis-summary.json",
                canonical_json(summary.model_dump(mode="json")),
                JSON_MEDIA_TYPE,
            ),
            ("baseline-table.csv", tables["baseline"], CSV_MEDIA_TYPE),
            ("model-coefficients.csv", tables["coefficients"], CSV_MEDIA_TYPE),
            ("risk-table.csv", tables["risk"], CSV_MEDIA_TYPE),
            ("kaplan-meier.png", figure, PNG_MEDIA_TYPE),
        )
        artifacts: list[AnalysisArtifact] = []
        for name, body, media_type in artifact_payloads:
            key = f"{prefix}/{name}"
            self._put_immutable(key, body, content_type=media_type)
            artifacts.append(
                AnalysisArtifact(
                    object_key=key,
                    media_type=media_type,
                    size_bytes=len(body),
                    sha256=sha256(body),
                )
            )

        manifest = SurvivalRunManifest(
            run_id=run_id,
            study_id=plan.study_id,
            protocol_version=plan.protocol_version,
            protocol_tag=receipt.protocol_tag,
            cohort_build_id=receipt.build_id,
            cohort_manifest_sha256=receipt.manifest_sha256,
            algorithm_version=ALGORITHM_VERSION,
            code_revision=code_revision,
            executed_at=self._clock(),
            random_seed=RANDOM_SEED,
            parameters=parameters,
            environment=self._environment(),
            artifacts=artifacts,
        )
        unhashed = canonical_json(manifest.model_dump(mode="json", exclude_none=True))
        manifest = manifest.model_copy(update={"manifest_sha256": sha256(unhashed)})
        self._put_immutable(
            f"{prefix}/manifest.json",
            canonical_json(manifest.model_dump(mode="json", exclude_none=True)),
            content_type=JSON_MEDIA_TYPE,
        )
        return manifest

    @staticmethod
    def _validate_gate(
        plan: AnalysisPlan,
        receipt: CohortBuildReceipt,
        code_revision: str,
    ) -> None:
        if plan.status is not PlanStatus.PREREGISTERED:
            raise SurvivalAnalysisError("survival analysis requires a preregistered plan")
        if receipt.qa_gate_status is not CohortGateStatus.APPROVED:
            raise SurvivalAnalysisError("survival analysis requires an approved cohort QA gate")
        required = [review for review in receipt.reviews if review.required_for_gate]
        if not required or any(
            review.decision is not ReviewDecision.APPROVED for review in required
        ):
            raise SurvivalAnalysisError("all required cohort reviews must be approved")
        if plan.study_id != receipt.study_id or plan.protocol_version != receipt.protocol_version:
            raise SurvivalAnalysisError("plan and cohort receipt identify different protocols")
        if not 7 <= len(code_revision) <= 40 or any(
            c not in "0123456789abcdef" for c in code_revision
        ):
            raise SurvivalAnalysisError("code revision must be a 7-to-40 character Git SHA")

    def _load_verified_cohort(self, receipt: CohortBuildReceipt) -> pd.DataFrame:
        manifest_body = self._store.get_bytes(receipt.manifest_object_key)
        try:
            manifest = CohortBuildManifest.model_validate_json(manifest_body)
        except (ValueError, json.JSONDecodeError) as error:
            raise SurvivalAnalysisError("cohort manifest is not valid") from error
        payload = manifest.model_dump(mode="json", exclude_none=True)
        recorded_hash = payload.pop("manifest_sha256", None)
        actual_hash = sha256(canonical_json(payload))
        if recorded_hash != actual_hash or actual_hash != receipt.manifest_sha256:
            raise SurvivalAnalysisError("cohort manifest checksum does not match its receipt")
        if manifest.build_id != receipt.build_id:
            raise SurvivalAnalysisError("cohort manifest build ID does not match its receipt")

        receipt_artifacts = {artifact.object_key: artifact for artifact in receipt.artifacts}
        manifest_artifacts = {artifact.object_key: artifact for artifact in manifest.artifacts}
        if receipt_artifacts != manifest_artifacts:
            raise SurvivalAnalysisError("cohort artifact lists differ between manifest and receipt")
        cohort_body: bytes | None = None
        for key, artifact in receipt_artifacts.items():
            body = self._store.get_bytes(key)
            if len(body) != artifact.size_bytes or sha256(body) != artifact.sha256:
                raise SurvivalAnalysisError(f"cohort artifact checksum mismatch: {key}")
            if key.endswith("/cohort.csv"):
                cohort_body = body
        if cohort_body is None:
            raise SurvivalAnalysisError("cohort receipt has no cohort.csv artifact")
        try:
            return pd.read_csv(io.BytesIO(cohort_body))
        except (UnicodeDecodeError, pd.errors.ParserError) as error:
            raise SurvivalAnalysisError("cohort.csv is not parseable") from error

    @staticmethod
    def _validate_cohort(frame: pd.DataFrame, receipt: CohortBuildReceipt) -> None:
        required = {
            "case_id",
            "pathologic_stage",
            "advanced_pathologic_stage",
            "ajcc_staging_system_edition",
            "age_at_diagnosis_years",
            "duration_days",
            "event",
        }
        if not required.issubset(frame.columns):
            raise SurvivalAnalysisError("cohort.csv is missing analysis columns")
        if len(frame) != receipt.included_case_count or frame["case_id"].duplicated().any():
            raise SurvivalAnalysisError("cohort row identity or count is invalid")
        if not frame["pathologic_stage"].isin(["I", "II", "III", "IV"]).all():
            raise SurvivalAnalysisError("cohort contains an invalid normalized stage")
        if not frame["advanced_pathologic_stage"].isin([0, 1]).all():
            raise SurvivalAnalysisError("cohort contains an invalid exposure")
        expected_advanced = frame["pathologic_stage"].isin(["III", "IV"]).astype(int)
        if not expected_advanced.equals(frame["advanced_pathologic_stage"].astype(int)):
            raise SurvivalAnalysisError("binary exposure is inconsistent with pathologic stage")
        if not frame["event"].isin([0, 1]).all():
            raise SurvivalAnalysisError("cohort contains an invalid event indicator")
        numeric = frame[["age_at_diagnosis_years", "duration_days"]].apply(pd.to_numeric)
        if not np.isfinite(numeric.to_numpy()).all():
            raise SurvivalAnalysisError("cohort contains non-finite analysis values")
        if (numeric["age_at_diagnosis_years"] < 18).any() or (numeric["duration_days"] <= 0).any():
            raise SurvivalAnalysisError("cohort violates age or positive-duration rules")

    def _analyze(
        self,
        plan: AnalysisPlan,
        receipt: CohortBuildReceipt,
        frame: pd.DataFrame,
    ) -> tuple[SurvivalAnalysisSummary, dict[str, bytes], bytes]:
        data = frame.copy()
        data["stage_ordinal"] = data["pathologic_stage"].map({"I": 1, "II": 2, "III": 3, "IV": 4})
        groups = self._group_summaries(data)
        early = data[data["advanced_pathologic_stage"] == 0]
        advanced = data[data["advanced_pathologic_stage"] == 1]
        log_rank_raw = logrank_test(
            early["duration_days"],
            advanced["duration_days"],
            event_observed_A=early["event"],
            event_observed_B=advanced["event"],
        )
        log_rank = LogRankResult(
            test_statistic=float(log_rank_raw.test_statistic),
            p_value=float(log_rank_raw.p_value),
        )

        primary, fitter = self._fit_cox(
            data,
            analysis_id="H1",
            label="Age-adjusted advanced versus early stage",
            formula="advanced_pathologic_stage + age_at_diagnosis_years",
            require_group_events=True,
        )
        ph = self._ph_diagnostics(fitter, data) if fitter is not None else []
        influence = self._influence_diagnostics(fitter, data) if fitter is not None else []
        unadjusted, _ = self._fit_cox(
            data,
            analysis_id="secondary_unadjusted",
            label="Unadjusted advanced versus early stage",
            formula="advanced_pathologic_stage",
        )
        stage_categorical, _ = self._fit_stage_categorical(data)
        secondary = self._apply_bh([unadjusted, stage_categorical])

        sensitivity = [
            self._fit_cox(
                data,
                analysis_id="S1",
                label="Ordinal stage with age adjustment",
                formula="stage_ordinal + age_at_diagnosis_years",
            )[0],
            self._fit_five_year(data),
            self._fit_time_interaction(data, ph),
            self._fit_age_spline(data),
            self._fit_common_edition(data),
        ]
        sensitivity = self._apply_bh(sensitivity)
        risk_table = self._risk_table(data)
        reproduction, decision, reasons = self._classify(primary, ph)
        summary = SurvivalAnalysisSummary(
            study_id=plan.study_id,
            protocol_version=plan.protocol_version,
            cohort_build_id=receipt.build_id,
            participant_count=len(data),
            event_count=int(data["event"].sum()),
            groups=groups,
            log_rank=log_rank,
            primary_model=primary,
            secondary_models=secondary,
            sensitivity_models=sensitivity,
            ph_diagnostics=ph,
            influential_observations=influence,
            ajcc_edition_distribution=self._edition_distribution(data),
            risk_table=risk_table,
            scientific_reproduction=reproduction,
            qualification_decision=decision,
            qualification_reasons=reasons,
            warnings=[
                warning
                for model in [primary, *secondary, *sensitivity]
                for warning in model.warnings
            ],
        )
        tables = {
            "baseline": self._baseline_csv(groups),
            "coefficients": self._coefficients_csv([primary, *secondary, *sensitivity]),
            "risk": self._risk_csv(risk_table),
        }
        return summary, tables, self._km_figure(data, risk_table)

    @staticmethod
    def _group_summaries(data: pd.DataFrame) -> list[GroupSummary]:
        results: list[GroupSummary] = []
        for value, label in ((0, "early"), (1, "advanced")):
            group = data[data["advanced_pathologic_stage"] == value]
            results.append(
                GroupSummary(
                    group=label,
                    participants=len(group),
                    events=int(group["event"].sum()),
                    censored=int((1 - group["event"]).sum()),
                    mean_age_years=float(group["age_at_diagnosis_years"].mean()),
                    median_age_years=float(group["age_at_diagnosis_years"].median()),
                    median_follow_up_days=float(group["duration_days"].median()),
                )
            )
        return results

    def _fit_cox(
        self,
        data: pd.DataFrame,
        *,
        analysis_id: str,
        label: str,
        formula: str,
        require_group_events: bool = False,
    ) -> tuple[ModelResult, CoxPHFitter | None]:
        if require_group_events:
            events = data.groupby("advanced_pathologic_stage")["event"].sum().to_dict()
            if any(int(events.get(group, 0)) < MINIMUM_GROUP_EVENTS for group in (0, 1)):
                return (
                    ModelResult(
                        analysis_id=analysis_id,
                        label=label,
                        status=AnalysisStatus.NOT_INTERPRETABLE,
                        participants=len(data),
                        events=int(data["event"].sum()),
                        formula=formula,
                        warnings=["Fewer than 10 deaths in at least one exposure group."],
                    ),
                    None,
                )
        fitter = CoxPHFitter()
        captured: list[str] = []
        try:
            with warnings.catch_warnings(record=True) as records:
                warnings.simplefilter("always")
                fitter.fit(data, duration_col="duration_days", event_col="event", formula=formula)
            captured = sorted({str(record.message) for record in records})
        except (ConvergenceError, ValueError, np.linalg.LinAlgError) as error:
            return (
                ModelResult(
                    analysis_id=analysis_id,
                    label=label,
                    status=AnalysisStatus.FAILED,
                    participants=len(data),
                    events=int(data["event"].sum()),
                    formula=formula,
                    warnings=[f"{type(error).__name__}: {error}"],
                ),
                None,
            )
        estimates = [self._coefficient(str(term), row) for term, row in fitter.summary.iterrows()]
        status = AnalysisStatus.COMPLETE if not captured else AnalysisStatus.NOT_INTERPRETABLE
        return (
            ModelResult(
                analysis_id=analysis_id,
                label=label,
                status=status,
                participants=len(data),
                events=int(data["event"].sum()),
                formula=formula,
                concordance_index=float(fitter.concordance_index_),
                log_likelihood=float(fitter.log_likelihood_),
                coefficients=estimates,
                warnings=captured,
            ),
            fitter,
        )

    @staticmethod
    def _coefficient(term: str, row: pd.Series) -> CoefficientEstimate:
        return CoefficientEstimate(
            term=term,
            coefficient=float(row["coef"]),
            hazard_ratio=float(row["exp(coef)"]),
            confidence_interval_lower=float(row["exp(coef) lower 95%"]),
            confidence_interval_upper=float(row["exp(coef) upper 95%"]),
            standard_error=float(row["se(coef)"]),
            z=float(row["z"]),
            p_value=float(row["p"]),
        )

    @staticmethod
    def _ph_diagnostics(fitter: CoxPHFitter, data: pd.DataFrame) -> list[PHDiagnostic]:
        result = proportional_hazard_test(fitter, data, time_transform="rank")
        diagnostics: list[PHDiagnostic] = []
        for term, row in result.summary.iterrows():
            p_value = float(row["p"])
            diagnostics.append(
                PHDiagnostic(
                    term=str(term),
                    test_statistic=float(row["test_statistic"]),
                    p_value=p_value,
                    assumption_violated=p_value < PH_ALPHA,
                )
            )
        return diagnostics

    @staticmethod
    def _influence_diagnostics(
        fitter: CoxPHFitter,
        data: pd.DataFrame,
    ) -> list[InfluenceObservation]:
        residuals = fitter.compute_residuals(data, kind="delta_beta")
        candidates: list[InfluenceObservation] = []
        for index, row in residuals.iterrows():
            absolute = row.abs()
            term = str(absolute.idxmax())
            candidates.append(
                InfluenceObservation(
                    case_id=str(data.loc[index, "case_id"]),
                    term=term,
                    delta_beta_absolute=float(absolute[term]),
                )
            )
        return sorted(candidates, key=lambda item: (-item.delta_beta_absolute, item.case_id))[:5]

    @staticmethod
    def _edition_distribution(data: pd.DataFrame) -> list[EditionDistribution]:
        prepared = data.assign(
            edition=data["ajcc_staging_system_edition"]
            .fillna("")
            .astype(str)
            .str.strip()
            .replace("", "missing"),
            stage_group=np.where(data["advanced_pathologic_stage"] == 1, "advanced", "early"),
        )
        counts = (
            prepared.groupby(["edition", "stage_group"], dropna=False)
            .size()
            .reset_index(name="participants")
            .sort_values(["edition", "stage_group"])
        )
        return [
            EditionDistribution(
                edition=str(row.edition),
                stage_group=str(row.stage_group),
                participants=int(str(row.participants)),
            )
            for row in counts.itertuples(index=False)
        ]

    def _fit_stage_categorical(self, data: pd.DataFrame) -> tuple[ModelResult, CoxPHFitter | None]:
        stage = pd.get_dummies(data["pathologic_stage"], prefix="stage", dtype=int)
        prepared = pd.concat([data, stage], axis=1)
        terms = [name for name in ("stage_II", "stage_III", "stage_IV") if name in prepared]
        if not terms:
            return self._skipped(
                "secondary_stage", "Categorical stage model", "No non-reference stage"
            )
        return self._fit_cox(
            prepared,
            analysis_id="secondary_stage",
            label="Age-adjusted categorical stage with stage I reference",
            formula=" + ".join([*terms, "age_at_diagnosis_years"]),
        )

    def _fit_five_year(self, data: pd.DataFrame) -> ModelResult:
        prepared = data.copy()
        prepared["event"] = (
            (prepared["event"] == 1) & (prepared["duration_days"] <= FIVE_YEARS_DAYS)
        ).astype(int)
        prepared["duration_days"] = prepared["duration_days"].clip(upper=FIVE_YEARS_DAYS)
        return self._fit_cox(
            prepared,
            analysis_id="S2",
            label="Five-year administrative censoring",
            formula="advanced_pathologic_stage + age_at_diagnosis_years",
            require_group_events=True,
        )[0]

    def _fit_time_interaction(self, data: pd.DataFrame, ph: list[PHDiagnostic]) -> ModelResult:
        exposure_failed = any(
            item.term == "advanced_pathologic_stage" and item.assumption_violated for item in ph
        )
        if not exposure_failed:
            return self._skipped(
                "S3", "Exposure by log-time interaction", "Exposure PH test did not fail"
            )[0]
        prepared = data.copy()
        prepared["advanced_log_time"] = prepared["advanced_pathologic_stage"] * np.log(
            prepared["duration_days"].clip(lower=1)
        )
        return self._fit_cox(
            prepared,
            analysis_id="S3",
            label="Advanced-stage by log-time interaction",
            formula="advanced_pathologic_stage + age_at_diagnosis_years + advanced_log_time",
        )[0]

    def _fit_age_spline(self, data: pd.DataFrame) -> ModelResult:
        percentiles = np.percentile(data["age_at_diagnosis_years"], [5, 35, 65, 95])
        lower, knot1, knot2, upper = (float(value) for value in percentiles)
        formula = (
            "advanced_pathologic_stage + "
            f"cr(age_at_diagnosis_years, knots=[{knot1}, {knot2}], "
            f"lower_bound={lower}, upper_bound={upper})"
        )
        return self._fit_cox(
            data,
            analysis_id="S4",
            label="Restricted cubic spline age sensitivity",
            formula=formula,
        )[0]

    def _fit_common_edition(self, data: pd.DataFrame) -> ModelResult:
        reported = data[
            data["ajcc_staging_system_edition"].fillna("").astype(str).str.strip() != ""
        ]
        if reported.empty:
            return self._skipped("S5", "Most common AJCC edition", "No reported AJCC edition")[0]
        edition = str(reported["ajcc_staging_system_edition"].value_counts().index[0])
        subset = reported[reported["ajcc_staging_system_edition"] == edition]
        return self._fit_cox(
            subset,
            analysis_id="S5",
            label=f"Most common AJCC edition ({edition})",
            formula="advanced_pathologic_stage + age_at_diagnosis_years",
            require_group_events=True,
        )[0]

    @staticmethod
    def _skipped(analysis_id: str, label: str, reason: str) -> tuple[ModelResult, None]:
        return (
            ModelResult(
                analysis_id=analysis_id,
                label=label,
                status=AnalysisStatus.SKIPPED,
                participants=0,
                events=0,
                formula="",
                warnings=[reason],
            ),
            None,
        )

    @staticmethod
    def _apply_bh(models: list[ModelResult]) -> list[ModelResult]:
        positions: list[tuple[int, int, float]] = []
        for model_index, model in enumerate(models):
            for coefficient_index, coefficient in enumerate(model.coefficients):
                positions.append((model_index, coefficient_index, coefficient.p_value))
        if not positions:
            return models
        ranked = sorted(enumerate(positions), key=lambda item: item[1][2])
        adjusted: dict[int, float] = {}
        running = 1.0
        count = len(ranked)
        for reverse_index in range(count - 1, -1, -1):
            original_index, (_, _, p_value) = ranked[reverse_index]
            rank = reverse_index + 1
            running = min(running, p_value * count / rank)
            adjusted[original_index] = min(1.0, running)
        replacements: dict[tuple[int, int], float] = {}
        for original_index, value in adjusted.items():
            model_index, coefficient_index, _ = positions[original_index]
            replacements[(model_index, coefficient_index)] = value
        output: list[ModelResult] = []
        for model_index, model in enumerate(models):
            coefficients = [
                coefficient.model_copy(
                    update={"adjusted_p_value": replacements[(model_index, index)]}
                )
                for index, coefficient in enumerate(model.coefficients)
            ]
            output.append(model.model_copy(update={"coefficients": coefficients}))
        return output

    @staticmethod
    def _risk_table(data: pd.DataFrame) -> list[RiskTableRow]:
        times = [0.0, 365.25, 3 * 365.25, FIVE_YEARS_DAYS]
        rows: list[RiskTableRow] = []
        for time in times:
            early = data[data["advanced_pathologic_stage"] == 0]
            advanced = data[data["advanced_pathologic_stage"] == 1]
            rows.append(
                RiskTableRow(
                    time_days=time,
                    early_at_risk=int((early["duration_days"] >= time).sum()),
                    advanced_at_risk=int((advanced["duration_days"] >= time).sum()),
                )
            )
        return rows

    @staticmethod
    def _classify(
        primary: ModelResult,
        ph: list[PHDiagnostic],
    ) -> tuple[str, QualificationDecision, list[str]]:
        exposure = next(
            (item for item in primary.coefficients if item.term == "advanced_pathologic_stage"),
            None,
        )
        if primary.status is AnalysisStatus.FAILED or exposure is None:
            return "not_estimable", QualificationDecision.FAIL, ["Primary model is not estimable."]
        if exposure.hazard_ratio > 1 and exposure.confidence_interval_lower > 1:
            reproduction = "supported"
        elif exposure.hazard_ratio > 1:
            reproduction = "directionally_consistent"
        else:
            reproduction = "not_reproduced"
        diagnostic_failure = any(item.assumption_violated for item in ph)
        if reproduction == "not_reproduced":
            return (
                reproduction,
                QualificationDecision.FAIL,
                ["Scientific association was not reproduced."],
            )
        if (
            primary.status is not AnalysisStatus.COMPLETE
            or diagnostic_failure
            or reproduction != "supported"
        ):
            return (
                reproduction,
                QualificationDecision.CONDITIONAL_PASS,
                [
                    "Governance passed, but the result or diagnostics require "
                    "qualified interpretation."
                ],
            )
        return (
            reproduction,
            QualificationDecision.PASS,
            ["Governance, reproduction, and diagnostics passed."],
        )

    @staticmethod
    def _baseline_csv(groups: list[GroupSummary]) -> bytes:
        return (
            pd.DataFrame([group.model_dump() for group in groups])
            .to_csv(index=False, lineterminator="\n")
            .encode()
        )

    @staticmethod
    def _coefficients_csv(models: list[ModelResult]) -> bytes:
        rows: list[dict[str, Any]] = []
        for model in models:
            if not model.coefficients:
                rows.append(
                    {
                        "analysis_id": model.analysis_id,
                        "status": model.status.value,
                        "warning": " | ".join(model.warnings),
                    }
                )
            for coefficient in model.coefficients:
                rows.append(
                    {
                        "analysis_id": model.analysis_id,
                        "status": model.status.value,
                        **coefficient.model_dump(),
                    }
                )
        return pd.DataFrame(rows).to_csv(index=False, lineterminator="\n").encode()

    @staticmethod
    def _risk_csv(rows: list[RiskTableRow]) -> bytes:
        return (
            pd.DataFrame([row.model_dump() for row in rows])
            .to_csv(index=False, lineterminator="\n")
            .encode()
        )

    @staticmethod
    def _km_figure(data: pd.DataFrame, risk_table: list[RiskTableRow]) -> bytes:
        figure, axis = plt.subplots(figsize=(8, 6), constrained_layout=True)
        for value, label, color in (
            (0, "Early (I/II)", "#2f6f9f"),
            (1, "Advanced (III/IV)", "#b24a3b"),
        ):
            group = data[data["advanced_pathologic_stage"] == value]
            fitter = KaplanMeierFitter(label=label)
            fitter.fit(group["duration_days"], event_observed=group["event"])
            fitter.plot_survival_function(ax=axis, ci_show=True, color=color)
        axis.set(
            title="Overall survival by pathologic stage group",
            xlabel="Days from diagnosis",
            ylabel="Estimated survival probability",
            ylim=(0, 1.02),
        )
        risk_text = "At risk (early / advanced): " + "; ".join(
            f"{row.time_days / 365.25:g}y {row.early_at_risk}/{row.advanced_at_risk}"
            for row in risk_table
        )
        figure.text(0.5, 0.01, risk_text, ha="center", fontsize=8)
        output = io.BytesIO()
        figure.savefig(output, format="png", dpi=150, metadata={"Software": "NaS Core"})
        plt.close(figure)
        return output.getvalue()

    @staticmethod
    def _environment() -> dict[str, str]:
        packages = ("lifelines", "matplotlib", "numpy", "pandas", "scipy")
        return {"python": platform.python_version(), **{name: version(name) for name in packages}}

    def _put_immutable(self, key: str, data: bytes, *, content_type: str) -> None:
        if self._store.exists(key):
            if self._store.get_bytes(key) != data:
                raise SurvivalAnalysisError(f"immutable analysis-object conflict: {key}")
            return
        self._store.put_bytes(key, data, content_type=content_type)
