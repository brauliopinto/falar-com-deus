from unittest.mock import MagicMock, patch

import pytest

from app.services.translator import TranslatorService


@pytest.fixture
def mock_llm_response():
    response = MagicMock()
    response.content = "Texto traduzido"
    return response


@patch("app.services.translator.deepl.Translator")
@patch("app.services.translator.ChatOpenRouter")
class TestTranslatorService:

    def test_openrouter_only_uses_llm(self, mock_chat_cls, mock_deepl_cls, mock_llm_response):
        mock_chat_cls.return_value.invoke.return_value = mock_llm_response

        service = TranslatorService(openrouter_api_key="or-key", llm_model="openai/gpt-5-mini", deepl_api_key="")
        result = service.translate_es_to_pt("Texto en español")

        assert result == "Texto traduzido"
        assert mock_chat_cls.return_value.invoke.call_count == 2
        mock_deepl_cls.assert_not_called()

    def test_deepl_only_uses_deepl(self, mock_chat_cls, mock_deepl_cls):
        mock_deepl_cls.return_value.translate_text.return_value.text = "Texto traduzido"

        service = TranslatorService(openrouter_api_key="", llm_model="openai/gpt-5-mini", deepl_api_key="deepl-key")
        result = service.translate_es_to_pt("Texto en español")

        assert result == "Texto traduzido"
        mock_chat_cls.assert_not_called()
        mock_deepl_cls.return_value.translate_text.assert_called_once_with(
            "Texto en español", source_lang="ES", target_lang="PT-BR"
        )

    def test_openrouter_falha_cai_no_deepl(self, mock_chat_cls, mock_deepl_cls):
        mock_chat_cls.return_value.invoke.side_effect = Exception("timeout")
        mock_deepl_cls.return_value.translate_text.return_value.text = "Texto traduzido pelo DeepL"

        service = TranslatorService(openrouter_api_key="or-key", llm_model="openai/gpt-5-mini", deepl_api_key="deepl-key")
        result = service.translate_es_to_pt("Texto en español")

        assert result == "Texto traduzido pelo DeepL"
        mock_deepl_cls.return_value.translate_text.assert_called_once()

    def test_nenhum_servico_lanca_runtime_error(self, mock_chat_cls, mock_deepl_cls):
        service = TranslatorService(openrouter_api_key="", llm_model="openai/gpt-5-mini", deepl_api_key="")

        with pytest.raises(RuntimeError, match="Nenhum serviço de tradução disponível"):
            service.translate_es_to_pt("Texto en español")

    def test_source_openrouter_quando_key_configurada(self, mock_chat_cls, mock_deepl_cls):
        service = TranslatorService(openrouter_api_key="or-key", llm_model="openai/gpt-5-mini", deepl_api_key="deepl-key")
        assert service.source == "openrouter"

    def test_source_deepl_quando_sem_openrouter(self, mock_chat_cls, mock_deepl_cls):
        service = TranslatorService(openrouter_api_key="", llm_model="openai/gpt-5-mini", deepl_api_key="deepl-key")
        assert service.source == "deepl"

    def test_openrouter_recebe_model_correto(self, mock_chat_cls, mock_deepl_cls):
        TranslatorService(openrouter_api_key="or-key", llm_model="google/gemini-flash", deepl_api_key="")

        mock_chat_cls.assert_called_once_with(api_key="or-key", model="google/gemini-flash")
