import deepl


class TranslatorService:
    def __init__(self, api_key: str) -> None:
        self._client = deepl.Translator(api_key)

    def translate_es_to_pt(self, text: str) -> str:
        result = self._client.translate_text(text, source_lang="ES", target_lang="PT-BR")
        return result.text
