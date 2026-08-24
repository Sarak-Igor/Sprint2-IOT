import json
from typing import Callable, TypeVar

from langchain_openai import ChatOpenAI

from backend.shared_infra.config import ROOT_DIR, settings

T = TypeVar("T")

_MODELS_PATH = ROOT_DIR / "backend" / "shared_infra" / "llm_models.json"


class LlmConfigError(Exception):
    """Levantada quando a chave de API ou o arquivo de modelos LLM está ausente/malformado
    — erro de configuração, nunca cai num default oculto (Fail-Fast, `00-contexto.md §2`)."""


class LlmAllModelsFailedError(Exception):
    """Levantada quando todos os modelos da lista de fallback falharam para uma chamada."""


def _load_model_ids() -> list[str]:
    if not _MODELS_PATH.exists():
        raise LlmConfigError(f"Arquivo de modelos LLM não encontrado: {_MODELS_PATH}")

    try:
        data = json.loads(_MODELS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LlmConfigError(f"Arquivo de modelos LLM malformado: {exc}") from exc

    models = data.get("models") if isinstance(data, dict) else None
    if not isinstance(models, list) or not models:
        raise LlmConfigError(
            f"Arquivo de modelos LLM sem lista 'models' válida: {_MODELS_PATH}"
        )
    return models


def invoke_with_fallback(run: Callable[[ChatOpenAI], T], **llm_kwargs) -> T:
    """Tenta, em ordem, cada modelo da lista versionada (`llm_models.json`), chamando
    `run(llm)` para cada um e devolvendo o primeiro resultado que não levantar exceção
    (inclui falha de chamada e resposta cortada pelo teto de tokens). Fail-Fast imediato
    (`LlmConfigError`) se a chave de API ou o arquivo de modelos estiverem ausentes ou
    malformados — antes de tentar qualquer modelo. Só levanta `LlmAllModelsFailedError`
    se todos os modelos da lista falharem."""
    if not settings.openrouter_api_key:
        raise LlmConfigError("OPENROUTER_API_KEY não configurada — defina no .env")

    model_ids = _load_model_ids()
    last_error: Exception | None = None

    configs = []
    for model_id in model_ids:
        configs.append({
            "api_key": settings.openrouter_api_key,
            "base_url": settings.openrouter_base_url,
            "model": model_id
        })
        
    if settings.groq_api_key:
        groq_models = [
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant"
        ]
        for m in groq_models:
            configs.append({
                "api_key": settings.groq_api_key,
                "base_url": settings.groq_base_url,
                "model": m
            })

    for config in configs:
        llm = ChatOpenAI(
            api_key=config["api_key"],
            base_url=config.get("base_url"),
            model=config["model"],
            **llm_kwargs,
        )
        try:
            return run(llm)
        except Exception as exc:  # tenta o próximo modelo da lista
            last_error = exc

    raise LlmAllModelsFailedError(
        f"Todos os {len(configs)} modelos da lista falharam. Último erro: {last_error}"
    ) from last_error


def invoke_vision_with_fallback(run: Callable[[ChatOpenAI], T], models_config: list[dict], **llm_kwargs) -> T:
    """Tenta, em ordem, cada modelo fornecido na lista de configuração para tarefas multimodais (visão).
    models_config deve ser uma lista de dicionários com chaves 'api_key', 'base_url' e 'model'."""
    if not models_config:
        raise LlmConfigError("Nenhum modelo de visão foi fornecido para a lista de fallback.")

    last_error: Exception | None = None

    for config in models_config:
        llm = ChatOpenAI(
            api_key=config["api_key"],
            base_url=config.get("base_url"),
            model=config["model"],
            **llm_kwargs,
        )
        try:
            return run(llm)
        except Exception as exc:
            last_error = exc

    raise LlmAllModelsFailedError(
        f"Todos os {len(models_config)} modelos de visão falharam. Último erro: {last_error}"
    ) from last_error
