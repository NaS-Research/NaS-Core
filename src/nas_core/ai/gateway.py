"""Replaceable model-provider gateway for governed structured screening output."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, cast

from openai import OpenAI
from openai.types.shared_params.reasoning import Reasoning

from nas_core.domain.advisory import AIAdvisoryBatchOutput, AIModelCall


class ModelGatewayError(RuntimeError):
    """Raised when a model provider cannot return valid structured output."""


@dataclass(frozen=True, slots=True)
class ScreeningGatewayRequest:
    instructions: str
    input_text: str
    safety_identifier: str


@dataclass(frozen=True, slots=True)
class ScreeningGatewayResponse:
    output: AIAdvisoryBatchOutput
    model_call: AIModelCall


class ScreeningModelGateway(Protocol):
    def screen(self, request: ScreeningGatewayRequest) -> ScreeningGatewayResponse: ...


class OpenAIScreeningGateway:
    """OpenAI Responses API adapter; credentials never enter research artifacts."""

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str,
        reasoning_effort: str,
        client: OpenAI | None = None,
    ) -> None:
        if not api_key and client is None:
            raise ModelGatewayError("OPENAI_API_KEY is required for live AI screening")
        self._client = client or OpenAI(api_key=api_key)
        self._model = model
        self._reasoning = cast(Reasoning, {"effort": reasoning_effort})

    def screen(self, request: ScreeningGatewayRequest) -> ScreeningGatewayResponse:
        try:
            response = self._client.responses.parse(
                model=self._model,
                instructions=request.instructions,
                input=request.input_text,
                reasoning=self._reasoning,
                text_format=AIAdvisoryBatchOutput,
                safety_identifier=request.safety_identifier,
                store=False,
                max_output_tokens=6000,
            )
        except Exception as error:
            raise ModelGatewayError("OpenAI screening request failed") from error
        parsed = response.output_parsed
        if parsed is None:
            raise ModelGatewayError("OpenAI returned no parsed screening output")
        usage = response.usage
        return ScreeningGatewayResponse(
            output=parsed,
            model_call=AIModelCall(
                provider="openai",
                model=self._model,
                response_id=response.id,
                input_tokens=usage.input_tokens if usage else 0,
                output_tokens=usage.output_tokens if usage else 0,
            ),
        )
