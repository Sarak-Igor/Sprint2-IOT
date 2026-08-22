from unittest.mock import patch

import pytest

from backend.apps.asset_manager.vision import plate_llm_structurer
from backend.apps.asset_manager.vision.plate_llm_structurer import (
    LlmStructuringError,
    structure_plate_text,
)


def test_structure_plate_text_fails_fast_without_api_key():
    detections = [("W22 1750 RPM", 90.0)]

    with (
        patch.object(plate_llm_structurer.settings, "openrouter_api_key", ""),
        patch.object(plate_llm_structurer, "ChatOpenAI") as mock_chat_openai,
    ):
        with pytest.raises(LlmStructuringError):
            structure_plate_text(detections)

    mock_chat_openai.assert_not_called()
