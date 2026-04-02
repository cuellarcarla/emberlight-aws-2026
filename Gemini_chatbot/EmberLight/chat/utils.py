from openai import OpenAI
from django.conf import settings
import time

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENROUTER_API_KEY,
)

MODELS_FALLBACK = [
    "google/gemma-3-4b-it:free",
    "google/gemma-3n-e4b-it:free",
    "google/gemma-3n-e2b-it:free",
    "liquid/lfm-2.5-1.2b-instruct:free",
    "nvidia/nemotron-nano-9b-v2:free",
]

SYSTEM_PROMPT = """Eres un asistente de salud mental en español. Sigue estas reglas:
1. **Contexto del Diario**: Usa las entradas del diario para respuestas personalizadas. Destaca patrones emocionales.
2. **Reflexión Emocional**: Nombra la emoción. Valida la experiencia.
3. **Formato**: 3-4 oraciones máximo. Termina con pregunta abierta. Usa **negritas**.
4. **Memoria**: Recuerda la conversación anterior. Mantén coherencia."""

def send_message_with_history(chat_history: list, journal_context: str, user_message: str) -> str:
    # Gemma no soporta role "system" — lo fusionamos en el primer mensaje de usuario
    first_user_content = f"{SYSTEM_PROMPT}\n\n{journal_context}"

    messages = [
        {"role": "user", "content": first_user_content},
        {"role": "assistant", "content": "Entendido. He revisado las entradas del diario. ¿En qué puedo ayudarte?"},
    ]

    for entry in chat_history:
        role = "user" if entry["role"] == "user" else "assistant"
        messages.append({"role": role, "content": entry["parts"]})

    messages.append({"role": "user", "content": user_message})

    last_error = None
    for model in MODELS_FALLBACK:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
            )
            return response.choices[0].message.content
        except Exception as e:
            last_error = e
            if "429" in str(e) or "rate" in str(e).lower():
                time.sleep(2)
                continue
            raise

    raise Exception(f"Todos los modelos fallaron. Último error: {last_error}")
