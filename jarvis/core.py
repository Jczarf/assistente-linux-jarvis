from __future__ import annotations

import json
import time
from collections import Counter
from typing import Any

from google import genai

from jarvis.config import settings
from jarvis.tools import TOOL_DECLARATIONS, execute_tool


SYSTEM_PROMPT = """Você é J.A.R.V.I.S., um assistente local para Linux.
Responda em português do Brasil e seja objetivo.

Regras operacionais:
- Use ferramenta somente quando necessária para cumprir o pedido.
- Nunca diga que abriu, executou, salvou, encontrou ou alterou algo sem um retorno de ferramenta com ok=true.
- Se uma ferramenta retornar ok=false, explique o erro real. Não converta falha em sucesso.
- Não repita a mesma chamada com os mesmos argumentos esperando resultado diferente.
- Se faltarem dados do usuário, peça apenas o dado necessário.
- Shell e abertura de aplicativos exigem pedido explícito do usuário.
- Não solicite nem exponha senhas, tokens ou chaves de API.
- Para ações destrutivas ou irreversíveis, não improvise: explique o risco e peça confirmação.
- Se uma capacidade estiver desativada, informe a limitação em vez de simular a ação.
"""

FINALIZE_PROMPT = """Conclua esta solicitação agora usando somente os resultados de ferramentas já disponíveis.
Não faça novas chamadas. Se algo falhou ou não foi comprovado, diga isso explicitamente.
Não invente execução, estado, arquivo, aplicativo ou resultado."""


class JarvisAssistant:
    def __init__(self, client: Any | None = None) -> None:
        settings.validate()
        self.client = client or genai.Client(api_key=settings.api_key)
        self.history: list[dict[str, Any]] = []
        self.tools = [dict(tool) for tool in TOOL_DECLARATIONS]

    @staticmethod
    def _call_signature(name: str, args: dict[str, Any]) -> str:
        return json.dumps(
            {"name": name, "args": args},
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )

    @staticmethod
    def _step_to_dict(step: Any) -> dict[str, Any]:
        if isinstance(step, dict):
            return step
        if hasattr(step, "model_dump"):
            return step.model_dump(mode="json", exclude_none=True)
        raise RuntimeError("A API retornou uma etapa em formato desconhecido.")

    @staticmethod
    def _function_args(step: Any) -> dict[str, Any]:
        raw = getattr(step, "arguments", None)
        if raw is None:
            return {}
        if isinstance(raw, dict):
            return dict(raw)
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                return {}
            return dict(parsed) if isinstance(parsed, dict) else {}
        try:
            return dict(raw)
        except (TypeError, ValueError):
            return {}

    @staticmethod
    def _should_retry(exc: Exception) -> bool:
        status = getattr(exc, "status_code", None)
        if status is None:
            status = getattr(exc, "code", None)
        try:
            if status is not None:
                return int(status) in {408, 409, 429, 500, 502, 503, 504}
        except (TypeError, ValueError):
            pass

        text = str(exc).lower()
        non_retryable = (
            "400 ",
            "401 ",
            "403 ",
            "404 ",
            "invalid_argument",
            "unauthenticated",
            "permission_denied",
            "not_found",
        )
        return not any(marker in text for marker in non_retryable)

    @staticmethod
    def _friendly_error(exc: Exception) -> str:
        raw = str(exc).strip()
        text = raw.lower()
        if "no longer available" in text or ("not_found" in text and "model" in text):
            return (
                f"O modelo '{settings.model}' não está disponível para esta conta. "
                "Use um modelo atual em JARVIS_MODEL; o padrão do projeto é gemini-3.6-flash."
            )
        if "unauthenticated" in text or "401" in text or "api key" in text and "invalid" in text:
            return "A GEMINI_API_KEY não foi aceita pela API do Gemini."
        if "permission_denied" in text or "403" in text:
            return "A API do Gemini recusou esta solicitação por permissão ou disponibilidade da conta."
        if "429" in text or "resource_exhausted" in text:
            return "A API do Gemini atingiu o limite de requisições ou cota disponível."
        return raw[:900] or exc.__class__.__name__

    def _trim_history(self, max_user_turns: int = 12) -> None:
        starts = [
            index
            for index, step in enumerate(self.history)
            if step.get("type") == "user_input"
        ]
        if len(starts) > max_user_turns:
            self.history = self.history[starts[-max_user_turns] :]

    def _generate(self, *, allow_tools: bool, finalizing: bool = False) -> Any:
        last_error: Exception | None = None
        attempts = 0

        for attempt in range(settings.agent_retries + 1):
            attempts = attempt + 1
            try:
                kwargs: dict[str, Any] = {
                    "model": settings.model,
                    "input": self.history,
                    "store": False,
                    "system_instruction": (
                        f"{SYSTEM_PROMPT}\n\n{FINALIZE_PROMPT}"
                        if finalizing
                        else SYSTEM_PROMPT
                    ),
                    "generation_config": {"max_output_tokens": 2048},
                    "timeout": settings.request_timeout_seconds,
                }
                if allow_tools:
                    kwargs["tools"] = self.tools
                return self.client.interactions.create(**kwargs)
            except Exception as exc:  # fronteira de rede/provider
                last_error = exc
                if not self._should_retry(exc) or attempt >= settings.agent_retries:
                    break
                time.sleep(min(0.4 * (2**attempt), 1.5))

        detail = self._friendly_error(last_error or RuntimeError("erro desconhecido"))
        raise RuntimeError(
            f"Falha ao consultar o Gemini após {attempts} tentativa(s): {detail}"
        ) from last_error

    def ask(self, text: str) -> str:
        text = text.strip()
        if not text:
            return "Digite uma solicitação."

        self._trim_history()
        self.history.append(
            {
                "type": "user_input",
                "content": [{"type": "text", "text": text}],
            }
        )

        repeated_calls: Counter[str] = Counter()

        for _step in range(settings.max_agent_steps):
            interaction = self._generate(allow_tools=True)
            steps = list(getattr(interaction, "steps", None) or [])
            self.history.extend(self._step_to_dict(step) for step in steps)

            function_steps = [
                step for step in steps if getattr(step, "type", None) == "function_call"
            ]
            if not function_steps:
                answer = (getattr(interaction, "output_text", "") or "").strip()
                return answer or "Não consegui produzir uma resposta."

            for call in function_steps:
                name = str(getattr(call, "name", "") or "")
                call_id = str(getattr(call, "id", "") or "")
                if not name or not call_id:
                    raise RuntimeError("A API retornou uma chamada de ferramenta incompleta.")

                args = self._function_args(call)
                signature = self._call_signature(name, args)
                repeated_calls[signature] += 1

                if repeated_calls[signature] > settings.tool_repeat_limit:
                    result = {
                        "ok": False,
                        "tool": name,
                        "error": "repeated_call",
                        "message": (
                            "Chamada idêntica não executada novamente. "
                            "Use o resultado anterior ou explique a limitação."
                        ),
                    }
                else:
                    result = execute_tool(name, args)

                self.history.append(
                    {
                        "type": "function_result",
                        "name": name,
                        "call_id": call_id,
                        "result": [
                            {
                                "type": "text",
                                "text": json.dumps(
                                    result,
                                    ensure_ascii=False,
                                    default=str,
                                ),
                            }
                        ],
                    }
                )

        interaction = self._generate(allow_tools=False, finalizing=True)
        steps = list(getattr(interaction, "steps", None) or [])
        self.history.extend(self._step_to_dict(step) for step in steps)

        answer = (getattr(interaction, "output_text", "") or "").strip()
        if not answer:
            answer = (
                "A tarefa atingiu o limite seguro de etapas e não houve "
                "resultado final verificável."
            )
        return answer
