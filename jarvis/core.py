from __future__ import annotations

from google import genai
from google.genai import types

from jarvis.config import settings
from jarvis.tools import TOOL_DECLARATIONS, execute_tool


SYSTEM_PROMPT = """Você é um assistente local para Linux.
Responda em português do Brasil.
Use ferramentas somente quando elas forem necessárias para atender ao pedido do usuário.
Nunca afirme que executou uma ação sem receber um resultado da ferramenta.
Não solicite nem exponha senhas, tokens ou chaves de API.
Para ações potencialmente destrutivas, explique o risco e peça confirmação antes de prosseguir.
Se uma ferramenta estiver desativada, explique a limitação em vez de tentar contorná-la.
"""


class JarvisAssistant:
    def __init__(self) -> None:
        settings.validate()
        self.client = genai.Client(api_key=settings.api_key)
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

    def ask(self, text: str) -> str:
        self.history.append(
            types.Content(role="user", parts=[types.Part(text=text)])
        )

        # Mantém a edição pública simples e previsível.
        self.history = self.history[-24:]

        for _ in range(6):
            response = self.client.models.generate_content(
                model=settings.model,
                contents=self.history,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.4,
                    max_output_tokens=2048,
                    tools=[self.tools],
                ),
            )

            candidate = response.candidates[0] if response.candidates else None
            content = candidate.content if candidate else None
            parts = content.parts if content and content.parts else []
            function_parts = [part for part in parts if part.function_call]

            if not function_parts:
                answer = response.text or "Não consegui produzir uma resposta."
                self.history.append(
                    types.Content(role="model", parts=[types.Part(text=answer)])
                )
                return answer

            self.history.append(content)
            tool_responses: list[types.Part] = []

            for part in function_parts:
                call = part.function_call
                args = dict(call.args) if call.args else {}
                result = execute_tool(call.name, args)
                tool_responses.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=call.name,
                            response={"result": result},
                        )
                    )
                )

            self.history.append(types.Content(role="user", parts=tool_responses))

        return "A tarefa excedeu o número máximo de etapas permitido nesta edição."
