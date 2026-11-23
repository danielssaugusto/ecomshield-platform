"""Create the final TP4 PDF from the verified repository artifacts."""
from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
METRICS = json.loads((ROOT / "data/processed/tp4_intent_evaluation.json").read_text(encoding="utf-8"))
OUTPUT = ROOT / "output/pdf/nathalia_artigas_PB_TP4.PDF"


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#475569"))
    canvas.drawString(2 * cm, 1.1 * cm, "E-ComShield - PB TP4")
    canvas.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"Página {doc.page}")
    canvas.restoreState()


def p(text: str, style):
    return Paragraph(text, style)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("Title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, leading=27, textColor=colors.HexColor("#0f172a"), alignment=TA_CENTER, spaceAfter=16)
    subtitle = ParagraphStyle("Subtitle", parent=styles["Normal"], fontSize=11, leading=16, alignment=TA_CENTER, textColor=colors.HexColor("#475569"), spaceAfter=28)
    heading = ParagraphStyle("Heading", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=colors.HexColor("#0f4c81"), spaceBefore=12, spaceAfter=8)
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=10, leading=14, spaceAfter=8)
    small = ParagraphStyle("Small", parent=body, fontSize=8.5, leading=11)
    story = [
        p("E-ComShield", title),
        p("PB TP4 - Classificador de intenções, agente autônomo e log parcial de pentest", subtitle),
        p("Autores: Daniel Augusto da Silva e Nathalia Calazans Artigas<br/>Data de entrega: 22/11/2026", body),
        Spacer(1, 8),
        p("Objetivo", heading),
        p("Integrar um classificador de intenções à API FastAPI, expor uma rota autenticada por JWT, preparar um agente de atendimento que usa a classificação como ferramenta e registrar, de modo responsável, o pentest parcial autorizado da API adversária.", body),
        p("1. Classificador de intenções", heading),
        p("O classificador usa TF-IDF de unigramas e bigramas com Regressão Logística. O dataset Bitext Retail eCommerce foi separado por intenção, e a avaliação final usa apenas a partição de teste. O script <font name='Courier'>scripts/train_intent_gridsearch.py</font> serializa o pipeline treinado em Joblib.", body),
    ]
    tuned = METRICS["tuned_model"]
    baseline = METRICS["baseline"]
    grid = METRICS["grid_search"]
    table = Table([
        ["Modelo", "Accuracy", "Macro F1", "ROC-AUC OvR"],
        ["Baseline: classe mais frequente", f"{baseline['accuracy']:.4f}", f"{baseline['macro_f1']:.4f}", "N/A"],
        ["TF-IDF + LogisticRegression", f"{tuned['accuracy']:.4f}", f"{tuned['macro_f1']:.4f}", f"{tuned['roc_auc_ovr_macro']:.4f}"],
    ], colWidths=[7.5 * cm, 2.5 * cm, 2.5 * cm, 2.7 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f4c81")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    story += [table, Spacer(1, 10)]
    story += [
        p(f"O GridSearchCV executou validação cruzada com {grid['cv']} folds, pesquisando <font name='Courier'>tfidf__min_df</font> em [1, 2, 3] e <font name='Courier'>classifier__C</font> em [0.5, 1.0, 2.0]. A melhor combinação foi {grid['best_params']} (macro F1 de validação: {grid['best_cv_macro_f1']:.4f}). O ganho sobre a baseline foi {METRICS['gain_over_baseline_macro_f1']:.4f} em macro F1.", body),
        p("As métricas por classe (precision, recall, F1 e suporte) e a matriz de confusão estão nos artefatos versionados do projeto. Limitação: o Bitext é um corpus em inglês, híbrido/sintético; os resultados não representam desempenho em reclamações reais brasileiras nem em produção.", body),
        p("2. API autenticada", heading),
        p("A API FastAPI expõe <font name='Courier'>POST /classify</font>. A entrada é um JSON com o campo <font name='Courier'>text</font>; a rota exige bearer JWT, carrega o pipeline Joblib e devolve <font name='Courier'>intent</font> e <font name='Courier'>probability</font>. Foram adicionadas as rotas locais de cadastro e emissão de token para viabilizar a demonstração. O teste de integração confirmou 401 sem token e 200 com token válido.", body),
        p("3. Agente autônomo", heading),
        p("O arquivo <font name='Courier'>agents/customer_service_agent.py</font> usa OpenAI Agents SDK: cria um <font name='Courier'>Agent</font>, declara <font name='Courier'>@function_tool</font> para chamar a rota protegida e executa os três turnos com <font name='Courier'>Runner.run</font>. O guia de execução documenta os três turnos. A transcrição depende de uma chave OpenAI fornecida em ambiente e não foi inventada neste relatório.", body),
        PageBreak(),
        p("4. Log parcial de pentest autorizado", heading),
        p("O log em <font name='Courier'>pentest/avaliacao_parcial_fintech_guard.md</font> registra o escopo limitado, técnicas, payloads, respostas e avaliação preliminar. Não foram realizados testes de indisponibilidade, alteração de dados, enumeração em massa ou acesso a dados de terceiros.", body),
    ]
    cell = ParagraphStyle("TableCell", parent=small, spaceAfter=0)
    header_cell = ParagraphStyle("TableHeader", parent=cell, textColor=colors.white, fontName="Helvetica-Bold")
    security = Table([
        [p("Área", header_cell), p("Evidência e conclusão", header_cell)],
        [p("Reconhecimento", cell), p("Nmap identificou a borda publicada. A evidência complementar da dupla registrou Gobuster para /health, /robots.txt, /favicon.ico e resposta 403 para /xmlrpc.php. O comando Kiterunner foi fornecido, mas sem saída verificável.", cell)],
        [p("JWT", cell), p("O token sem assinatura (alg:none) recebeu 401. A mudança de algoritmo também recebeu 401. A dupla forneceu evidência de jwt_tool para alg:none e wordlist RockYou sem chave encontrada; segredos foram removidos.", cell)],
        [p("Fuzzing / SQL", cell), p("Uma sonda SQL-like em /classify não mostrou erro, atraso ou comportamento de banco. O resultado não prova ausência de vulnerabilidade em outras superfícies.", cell)],
        [p("BOLA / BFLA / IDOR", cell), p("Não confirmados: não havia segunda conta autorizada, ID de recurso exposto ou função administrativa testável. O template BFLA recebido não tinha resposta preenchida.", cell)],
    ], colWidths=[3.5 * cm, 11.9 * cm])
    security.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f4c81")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [security, Spacer(1, 10)]
    story += [
        p("5. Reprodutibilidade e fontes", heading),
        p("Dependências: Python, FastAPI, scikit-learn, Joblib, SQLAlchemy, python-jose e OpenAI Agents SDK. Para reproduzir o classificador: <font name='Courier'>python3 scripts/train_intent_gridsearch.py</font>. Para iniciar a API: <font name='Courier'>PYTHONPATH=src uvicorn ecomshield.main:app --reload</font>.", body),
        p("Fontes: Bitext Retail eCommerce Dataset (https://huggingface.co/datasets/bitext/Bitext-retail-ecommerce-llm-chatbot-training-dataset); scikit-learn (https://scikit-learn.org/); FastAPI (https://fastapi.tiangolo.com/); OpenAI Agents SDK (https://openai.github.io/openai-agents-python/); Nmap (https://nmap.org/); Kiterunner (https://github.com/assetnote/kiterunner); Gobuster (https://github.com/OJ/gobuster); jwt_tool (https://github.com/ticarpi/jwt_tool).", small),
        p("Uso de IA: ferramentas de IA foram usadas como apoio à organização, implementação e revisão; todos os resultados apresentados foram verificados contra os artefatos do repositório, e limitações e pendências foram mantidas de forma explícita.", small),
    ]
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=2 * cm, leftMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm, title="PB TP4 - E-ComShield")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == "__main__":
    main()
