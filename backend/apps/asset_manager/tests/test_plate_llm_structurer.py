from unittest.mock import patch

import pytest

from backend.apps.asset_manager.vision.plate_llm_structurer import (
    LlmStructuringError,
    structure_plate_image,
)
from backend.shared_infra import llm_client
from backend.shared_infra.config import settings


def test_structure_plate_image_fails_fast_without_api_key():
    settings.openrouter_api_key = ""  # Forçando erro de config
    
    # Mockando uma imagem
    fake_image_bytes = b"fake_image_content"

    with pytest.raises(LlmStructuringError) as exc_info:
        with patch("backend.shared_infra.llm_client._load_model_ids") as mock_load:
            structure_plate_image(fake_image_bytes)
