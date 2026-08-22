import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "build_b2w_intent_dataset.py"
SPEC = importlib.util.spec_from_file_location("b2w_dataset", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_normalize_text_redacts_common_personal_identifiers():
    text = MODULE.normalize_text("  Fale com maria@example.com, CPF 123.456.789-00 e 11 91234-5678.  ")

    assert text == "Fale com [EMAIL], CPF [CPF] e [TELEFONE]."


def test_topic_classification_prioritizes_refund_and_keeps_all_matches():
    primary, matches = MODULE.classify_topics(
        "Pedido cancelado, atrasou muito e quero estorno do dinheiro."
    )

    assert primary == "estorno_reembolso"
    assert matches == "estorno_reembolso|cancelamento|atraso_entrega"


def test_topic_classification_is_accent_insensitive():
    primary, matches = MODULE.classify_topics("A entrega não chegou e está fora do prazo.")

    assert primary == "atraso_entrega"
    assert matches == "atraso_entrega"


def test_product_quality_is_classified_from_text():
    assert MODULE.classify_topics("Produto bonito e de boa qualidade.") == ("qualidade_produto", "qualidade_produto")


def test_unmatched_text_has_no_textual_intent_match():
    assert MODULE.classify_topics("Gostei.") == ("", "")


def test_rating_fallback_labels_non_operational_reviews_transparently():
    assert MODULE.fallback_intent_from_rating(5) == "avaliacao_geral"
    assert MODULE.fallback_intent_from_rating(3) == "avaliacao_geral"
    assert MODULE.fallback_intent_from_rating(1) == "avaliacao_geral"


def test_sentiment_is_separate_from_topic_and_detects_mixed_feedback():
    assert MODULE.classify_sentiment("Produto ótimo, mas não gostei da tela.", 3) == ("misto", "keyword_heuristic_v1")
    assert MODULE.classify_sentiment("Gostei.", 5) == ("positivo", "rating_fallback_v1")
