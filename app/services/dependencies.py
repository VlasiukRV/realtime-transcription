from app.services.translators.translator import ITranslator, TranslatorFactory

def get_translator() -> ITranslator:
    from app.config import TRANSLATOR_TYPE

    translator_factory = TranslatorFactory()
    translator_class = translator_factory.get_translator(TRANSLATOR_TYPE)
    return translator_class()
