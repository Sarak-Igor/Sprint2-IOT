import base64
import io
from PIL import Image
from langchain_core.messages import HumanMessage, SystemMessage

from backend.apps.asset_manager.vision.schemas import PlateExtractionResult
from backend.shared_infra.llm_client import (
    invoke_vision_with_fallback,
    LlmConfigError,
    LlmAllModelsFailedError,
)

from backend.shared_infra.config import settings

def _get_vision_models_config():
    configs = []
    
    # 1. OpenRouter Models (Primary)
    if settings.openrouter_api_key:
        openrouter_models = [
            "google/gemma-4-26b-a4b-it:free",
            "google/gemma-4-31b-it:free",
            "nvidia/nemotron-nano-12b-v2-vl:free",
        ]
        for m in openrouter_models:
            configs.append({
                "api_key": settings.openrouter_api_key,
                "base_url": settings.openrouter_base_url,
                "model": m
            })
            
    # 2. Groq Models (Fallback Provider)
    if settings.groq_api_key:
        groq_models = [
            "qwen/qwen3.6-27b",
        ]
        for m in groq_models:
            configs.append({
                "api_key": settings.groq_api_key,
                "base_url": settings.groq_base_url,
                "model": m
            })
            
    return configs

_MAX_OUTPUT_TOKENS = 1500


class LlmStructuringError(Exception):
    """Levantada quando a estruturação via LLM falha."""


def _optimize_image_for_llm(image_bytes: bytes, max_size: int = 1024) -> bytes:
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        # Resize if larger than max_size while maintaining aspect ratio
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=85)
        return output.getvalue()
    except Exception:
        # Em caso de falha no PIL, retorna os bytes originais
        return image_bytes

def structure_plate_image(image_bytes: bytes) -> PlateExtractionResult:
    """Estrutura os dados diretamente da imagem usando um modelo Multimodal."""
    optimized_bytes = _optimize_image_for_llm(image_bytes)
    base64_image = base64.b64encode(optimized_bytes).decode('utf-8')

    def _run(llm):
        structured_llm = llm.with_structured_output(PlateExtractionResult, method="json_mode")
        return structured_llm.invoke(
            [
                SystemMessage(
                    content=(
                        "Você é um especialista em extração de dados de placas de motores elétricos. "
                        "Analise a imagem fornecida e extraia as informações com extrema precisão. "
                        "ATENÇÃO: A 'marca' ou fabricante costuma estar no logotipo (ex: WEG, Siemens). O 'modelo' costuma estar em destaque no topo (ex: W22, W21). "
                        "A 'tensao' e 'corrente' costumam estar em tabelas (ex: 220/380V). "
                        "Se algum campo estiver completamente ilegível, responda 'Não legível'. "
                        "Responda EXCLUSIVAMENTE em formato JSON contendo exatamente estas chaves: "
                        '{"marca": "", "modelo": "", "potencia": "", "rpm": "", "carcaca": "", "tensao": "", "corrente": "", "ip": "", "classe_isol": "", "confianca": 100.0}'
                    )
                ),
                HumanMessage(
                    content=[
                        {"type": "text", "text": "Extraia as informações da placa nesta imagem:"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                    ]
                ),
            ]
        )

    try:
        return invoke_vision_with_fallback(
            _run, models_config=_get_vision_models_config(), temperature=0, max_tokens=_MAX_OUTPUT_TOKENS
        )
    except (LlmConfigError, LlmAllModelsFailedError) as exc:
        raise LlmStructuringError(
            f"Falha ao consultar o LLM multimodal via OpenRouter: {exc}"
        ) from exc

