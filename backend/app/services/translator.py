import logging

import deepl
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
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

_FEW_SHOT_EXAMPLES = (
    (
        "Hoy te invito a poner tu mirada en Jesús, que camina contigo en medio de las pruebas de la vida "
        "y no te abandona ni por un instante.",
        "Hoje te convido a fixar teu olhar em Jesus, que caminha contigo em meio às provações da vida "
        "e não te abandona nem por um instante.",
    ),
    (
        "María, Madre de Misericordia, intercede por nosotros ante tu Hijo, para que hallemos consuelo "
        "en nuestra aflicción y crezcamos en la fe.",
        "Maria, Mãe de Misericórdia, intercede por nós diante de teu Filho, para que encontremos consolo "
        "em nossa aflição e cresçamos na fé.",
    ),
)

_REVIEW_SYSTEM_PROMPT = (
    "Você é um revisor especializado em textos religiosos católicos. Você receberá um texto original em "
    "espanhol e um rascunho de tradução para o português do Brasil. Revise o rascunho, corrigindo erros de "
    "tom devocional, fluidez, terminologia litúrgica ou fidelidade ao original em espanhol. "
    "Se o rascunho já estiver excelente, retorne-o sem alterações. "
    "Retorne apenas a versão final da tradução, sem comentários ou explicações."
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
                messages = [SystemMessage(content=_SYSTEM_PROMPT)]
                for es_example, pt_example in _FEW_SHOT_EXAMPLES:
                    messages.append(HumanMessage(content=es_example))
                    messages.append(AIMessage(content=pt_example))
                messages.append(HumanMessage(content=text))
                draft = self._llm.invoke(messages).content

                review_messages = [
                    SystemMessage(content=_REVIEW_SYSTEM_PROMPT),
                    HumanMessage(
                        content=f"Texto original (espanhol):\n{text}\n\nRascunho de tradução (português):\n{draft}"
                    ),
                ]
                return self._llm.invoke(review_messages).content
            except Exception:
                logger.warning("Falha na tradução via OpenRouter, usando DeepL como fallback.", exc_info=True)

        if self._deepl is not None:
            result = self._deepl.translate_text(text, source_lang="ES", target_lang="PT-BR")
            return result.text

        raise RuntimeError("Nenhum serviço de tradução disponível. Configure OPENROUTER_API_KEY ou DEEPL_API_KEY.")
