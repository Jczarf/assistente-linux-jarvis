from __future__ import annotations

import json
import time
from collections import Counter
from typing import Any

from google import genai
from google.genai import types

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
        self.client = client or genai.Client(
            api_key=settings.api_key,
            http_options=types.HttpOptions(
                timeout=settings.request_timeout_seconds * 1000
            ),
        )
        self.history: list[types.Content] = []
        self.tools = types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name=tool["name"],
                    description=tool["description"],
                    parameters=tool.get("parameters"),
                )
                for tool in TOOL_DECLARATIONS
            ]
        )

    def _generate(
        self,
        contents: list[types.Content],
        *,
        allow_tools: bool,
        finalizing: bool = False,
    ):
        last_error: Exception | None = None
        for attempt in range(settings.agent_retries + 1):
            try:
                return self.client.models.generate_content(
                    model=settings.model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=(
                            f"{SYSTEM_PROMPT}\n\n{FINALIZE_PROMPT}"
                            if finalizing
                            else SYSTEM_PROMPT
                        ),
                        temperature=0.25,
                        max_output_tokens=2048,
                        tools=[self.tools] if allow_tools else None,
                    ),
                )
            except Exception as exc:  # API/network boundary
                last_error = exc
                if attempt >= settings.agent_retries:
                    break
                time.sleep(min(0.4 * (2**attempt), 1.5))
        raise RuntimeError(
            f"Falha ao consultar o modelo após {settings.agent_retries + 1} tentativa(s): {last_error}"
        ) from last_error

    @staticmethod
    def _response_parts(response: Any) -> list[Any]:
        candidate = response.candidates[0] if getattr(response, "candidates", None) else None
        content = candidate.content if candidate else None
        return list(content.parts or []) if content and content.parts else []

    @staticmethod
    def _call_signature(name: str, args: dict[str, Any]) -> str:
        return json.dumps(
            {"name": name, "args": args},
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )

    def ask(self, text: str) -> str:
        text = text.strip()
        if not text:
            return "Digite uma solicitação."

        self.history.append(
            types.Content(role="user", parts=[types.Part(text=text)])
        )
        self.history = self.history[-24:]

        repeated_calls: Counter[str] = Counter()

        for _step in range(settings.max_agent_steps):
            response = self._generate(self.history, allow_tools=True)
            parts = self._response_parts(response)
            function_parts = [part for part in parts if getattr(part, "function_call", None)]

            if not function_parts:
                answer = (response.text or "").strip() or "Não consegui produzir uma resposta."
                self.history.append(
                    types.Content(role="model", parts=[types.Part(text=answer)])
                )
                return answer

            candidate = response.candidates[0]
            self.history.append(candidate.content)
            tool_responses: list[types.Part] = []

            for part in function_parts:
                call = part.function_call
                args = dict(call.args) if call.args else {}
                signature = self._call_signature(call.name, args)
                repeated_calls[signature] += 1

                if repeated_calls[signature] > settings.tool_repeat_limit:
                    result = {
                        "ok": False,
                        "tool": call.name,
                        "error": "repeated_call",
                        "message": (
                            "Chamada idêntica não executada novamente. "
                            "Use o resultado anterior ou explique a limitação."
                        ),
                    }
                else:
                    result = execute_tool(call.name, args)

                tool_responses.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=call.name,
                            response=result,
                        )
                    )
                )

            self.history.append(types.Content(role="user", parts=tool_responses))

        response = self._generate(
            self.history,
            allow_tools=False,
            finalizing=True,
        )
        answer = (response.text or "").strip()
        if not answer:
            answer = (
                "A tarefa atingiu o limite seguro de etapas e não houve "
                "resultado final verificável."
            )
        self.history.append(
            types.Content(role="model", parts=[types.Part(text=answer)])
        )
        return answer
