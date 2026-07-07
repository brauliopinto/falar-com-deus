import logging

import deepl
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openrouter import ChatOpenRouter

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Você é um tradutor especializado em textos religiosos católicos, com profundo conhecimento "
    "da linguagem sacra, litúrgica e espiritual em espanhol e português do Brasil. "
    "Ao traduzir, preserve fielmente o tom devocional, a solenidade e o vocabulário próprio da tradição católica "
    "(termos litúrgicos, nomes de santos, referências bíblicas e expressões de espiritualidade). "
    "Prefira construções em português do Brasil consagradas pelo uso católico. "
    "Retorne apenas o texto traduzido, sem explicações."
)


class TranslatorService:
    def __init__(self, openrouter_api_key: str, llm_model: str, deepl_api_key: str) -> None:
        self._llm = (
            ChatOpenRouter(
                api_key=openrouter_api_key,
                model=llm_model,
            )
            if openrouter_api_key
            else None
        )
        self._deepl = deepl.Translator(deepl_api_key) if deepl_api_key else None
        self.source = "openrouter" if openrouter_api_key else "deepl"

    def translate_es_to_pt(self, text: str) -> str:
        if self._llm is not None:
            try:
                messages = [
                    SystemMessage(content=_SYSTEM_PROMPT),
                    HumanMessage(content=text),
                ]
                return self._llm.invoke(messages).content
            except Exception:
                logger.warning("Falha na tradução via OpenRouter, usando DeepL como fallback.", exc_info=True)

        if self._deepl is not None:
            result = self._deepl.translate_text(text, source_lang="ES", target_lang="PT-BR")
            return result.text

        raise RuntimeError("Nenhum serviço de tradução disponível. Configure OPENROUTER_API_KEY ou DEEPL_API_KEY.")
