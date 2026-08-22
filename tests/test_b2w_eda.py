import importlib.util
from pathlib import Path

import pandas as pd


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "generate_b2w_eda.py"
SPEC = importlib.util.spec_from_file_location("b2w_eda", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_eda_generates_all_artifacts(tmp_path, monkeypatch):
    dataset = pd.DataFrame(
        {
            "submission_date": ["2018-01-01", "2018-01-02", "2018-02-01"],
            "text": ["Entrega rápida", "Quero estorno", "Produto excelente"],
            "intent": ["entrega_antecipada", "estorno_reembolso", "avaliacao_positiva"],
            "intent_matches": ["entrega_antecipada|avaliacao_positiva", "estorno_reembolso", "avaliacao_positiva"],
            "label_source": ["keyword_heuristic_v4", "keyword_heuristic_v4", "generic_topic_fallback_v1"],
            "sentiment": ["positivo", "negativo", "positivo"],
            "sentiment_source": ["keyword_heuristic_v1", "rating_fallback_v1", "rating_fallback_v1"],
            "overall_rating": [5, 1, 5],
        }
    )
    input_path = tmp_path / "input.parquet"
    output_dir = tmp_path / "report"
    dataset.to_parquet(input_path, index=False)
    monkeypatch.setattr("sys.argv", ["generate_b2w_eda.py", "--input", str(input_path), "--output-dir", str(output_dir)])

    MODULE.main()

    expected = {
        "01_cobertura_rotulos.png",
        "02_distribuicao_intencoes.png",
        "03_notas_por_intencao.png",
        "04_tamanho_texto_por_origem.png",
        "05_coocorrencias.png",
        "06_evolucao_mensal.png",
        "07_distribuicao_sentimento.png",
        "relatorio.md",
    }
    assert {path.name for path in output_dir.iterdir()} == expected
