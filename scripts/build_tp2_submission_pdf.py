"""Build the TP2 submission PDF from the versioned analysis and evidence."""

from __future__ import annotations

from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "nathalia_artigas_PB_TP2.PDF"
BRANCH_URL = (
    "https://github.com/danielssaugusto/ecomshield-platform/tree/"
    "feature/integracao-tp2-dados-seguranca"
)
REPORT_URL = (
    "https://github.com/danielssaugusto/ecomshield-platform/blob/"
    "feature/integracao-tp2-dados-seguranca/reports/relatorio_owasp_zap.md"
)
ZAP_HTML_URL = REPORT_URL.replace("relatorio_owasp_zap.md", "zap_report.html")


def register_fonts() -> None:
    font_pairs = [
        (
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        ),
        (
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ),
    ]
    regular, bold = next(
        ((regular, bold) for regular, bold in font_pairs
         if regular.is_file() and bold.is_file()),
        (None, None),
    )
    if regular is None or bold is None:
        raise FileNotFoundError("Fonte Arial ou DejaVu Sans não encontrada")
    pdfmetrics.registerFont(TTFont("ArialTP2", str(regular)))
    pdfmetrics.registerFont(TTFont("ArialTP2-Bold", str(bold)))
    pdfmetrics.registerFontFamily(
        "ArialTP2", normal="ArialTP2", bold="ArialTP2-Bold"
    )


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    navy = colors.HexColor("#172b4d")
    slate = colors.HexColor("#43546b")
    return {
        "title": ParagraphStyle(
            "TP2Title", parent=base["Title"], fontName="ArialTP2-Bold",
            fontSize=23, leading=29, textColor=navy, alignment=TA_LEFT,
            spaceAfter=13,
        ),
        "subtitle": ParagraphStyle(
            "TP2Subtitle", parent=base["Normal"], fontName="ArialTP2",
            fontSize=11, leading=16, textColor=slate, spaceAfter=12,
        ),
        "h1": ParagraphStyle(
            "TP2H1", parent=base["Heading1"], fontName="ArialTP2-Bold",
            fontSize=14, leading=19, textColor=navy, spaceBefore=12,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "TP2H2", parent=base["Heading2"], fontName="ArialTP2-Bold",
            fontSize=10.5, leading=15, textColor=navy, spaceBefore=9,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "TP2Body", parent=base["BodyText"], fontName="ArialTP2",
            fontSize=9.2, leading=14.1, textColor=navy, spaceAfter=7,
        ),
        "small": ParagraphStyle(
            "TP2Small", parent=base["BodyText"], fontName="ArialTP2",
            fontSize=8, leading=11.5, textColor=slate, spaceAfter=5,
        ),
        "table": ParagraphStyle(
            "TP2Table", parent=base["BodyText"], fontName="ArialTP2",
            fontSize=8.1, leading=11.2, textColor=navy,
        ),
        "table_head": ParagraphStyle(
            "TP2TableHead", parent=base["BodyText"],
            fontName="ArialTP2-Bold", fontSize=8.1, leading=11.2,
            textColor=colors.white,
        ),
        "caption": ParagraphStyle(
            "TP2Caption", parent=base["BodyText"], fontName="ArialTP2",
            fontSize=8, leading=11, textColor=slate, alignment=TA_CENTER,
            spaceAfter=7,
        ),
    }


def para(value: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(value, style)


def bullet(value: str, style: ParagraphStyle) -> Paragraph:
    return para(f"&#8226;&nbsp; {value}", style)


def table(rows: list[list[str]], widths: list[float], css: dict) -> Table:
    content = [
        [para(cell, css["table_head"] if index == 0 else css["table"])
         for cell in row]
        for index, row in enumerate(rows)
    ]
    result = Table(content, colWidths=widths, repeatRows=1, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#24466b")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#24466b")),
    ]))
    return result


def figure(path: Path, width: float, caption: str, css: dict):
    pixel_width, pixel_height = ImageReader(str(path)).getSize()
    image = Image(str(path), width=width, height=width * pixel_height / pixel_width)
    return KeepTogether([image, para(escape(caption), css["caption"])])


def footer(canvas, doc) -> None:
    canvas.saveState()
    width, _ = A4
    canvas.setStrokeColor(colors.HexColor("#d7e0e9"))
    canvas.line(18 * mm, 16 * mm, width - 18 * mm, 16 * mm)
    canvas.setFont("ArialTP2", 8)
    canvas.setFillColor(colors.HexColor("#596b80"))
    canvas.drawString(18 * mm, 11 * mm, "Nathalia Artigas | E-ComShield | TP2")
    canvas.drawRightString(width - 18 * mm, 11 * mm, str(doc.page))
    canvas.restoreState()


def build() -> Path:
    register_fonts()
    css = styles()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=23 * mm,
        title="Nathalia Artigas - Projeto de Bloco - TP2",
        author="Nathalia Artigas",
    )
    content = []

    # Page 1 - scope and provenance.
    content += [
        para("Projeto de Bloco - TP2", css["title"]),
        para("E-ComShield | Análise exploratória e segurança da API<br/>"
             "Nathalia Artigas | 27 de setembro de 2026", css["subtitle"]),
        HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#3b77a4")),
        para("Problema e objetivo", css["h1"]),
        para(
            "Aprofundar a análise de textos de e-commerce com correlação, "
            "visualizações e teste de hipótese formal; verificar os controles "
            "de segurança da API FastAPI e registrar um scan passivo real do "
            "OWASP ZAP. O B2W fornece avaliações reais em português, enquanto "
            "o Bitext fornece rótulos de intenção publicados pela fonte.",
            css["body"],
        ),
        para("Fontes e separação metodológica", css["h1"]),
        table([
            ["Fonte", "Papel neste TP", "Volume após preparo"],
            ["Bitext Retail eCommerce", "EDA das intenções originais; base de treino do baseline", "44.884 textos; 46 intenções; 13 categorias"],
            ["B2W-Reviews01", "Feedback real em PT-BR; hipótese de comprimento do texto", "132.373 linhas originais; 131.347 após limpeza"],
            ["Amostra B2W anotada", "Validação externa futura, sem contaminar o treino", "500 rótulos humanos; 422 elegíveis sem marca de incerteza"],
        ], [39 * mm, 85 * mm, 49 * mm], css),
        Spacer(1, 10),
        para(
            "<b>Regra importante:</b> a nota do B2W não é rótulo de intenção. "
            "O projeto não usa as antigas heurísticas de palavras-chave como "
            "ground truth. O Bitext é inglês e híbrido/sintético; a avaliação "
            "PT-BR humana permanece separada do treinamento.", css["body"],
        ),
        para("Reprodutibilidade", css["h1"]),
        bullet("Downloads fixados por revisão e SHA-256; scripts verificam a integridade antes da EDA.", css["body"]),
        bullet("Partições do Bitext determinísticas, estratificadas por intenção e sem texto idêntico entre treino e teste.", css["body"]),
        bullet("Notebooks 03 e 04 contêm a EDA executada; o relatório completo está em <link href='" + REPORT_URL.replace("relatorio_owasp_zap.md", "tp2_data_eda/relatorio.md") + "' color='#185b91'>reports/tp2_data_eda/relatorio.md</link>.", css["body"]),
        PageBreak(),
    ]

    # Page 2 - visual exploratory analysis.
    content += [
        para("EDA aprofundada: correlações e relações", css["h1"]),
        para(
            "O heatmap usa Spearman para atributos numéricos do Bitext: "
            "comprimentos de solicitação e resposta, em caracteres e palavras, "
            "e presença de interrogação. Intenção e categoria são nominais e "
            "não foram convertidas em números arbitrários.", css["body"],
        ),
        figure(ROOT / "reports/tp2_data_eda/figures/01_bitext_correlacoes.png",
               135 * mm, "Figura 1. Correlações de Spearman no Bitext.", css),
        para(
            "Caracteres e palavras da solicitação têm correlação aproximada "
            "de 0,88; as duas medidas da resposta, 0,99. A correlação entre "
            "comprimento de solicitação e resposta é apenas 0,05. As duas "
            "primeiras associações são em grande parte mecânicas; nenhuma "
            "delas demonstra causalidade ou qualidade do classificador.", css["body"],
        ),
        PageBreak(),
        para("EDA aprofundada: dispersões", css["h1"]),
        figure(ROOT / "reports/tp2_data_eda/figures/02_bitext_intencoes_comprimento.png",
               151 * mm, "Figura 2. Mediana e percentil 95 do comprimento por intenção.", css),
        figure(ROOT / "reports/tp2_data_eda/figures/03_bitext_solicitacao_resposta.png",
               151 * mm, "Figura 3. Comprimento da solicitação versus resposta em amostra reprodutível de 5.000 linhas.", css),
        para(
            "O primeiro gráfico cobre as 46 intenções. Em track_order, o "
            "percentil 95 chega a 117 caracteres, contra 84 no conjunto. O "
            "segundo gráfico usa random_state=42 para legibilidade visual; "
            "as estatísticas são calculadas com todas as linhas elegíveis.",
            css["body"],
        ),
        PageBreak(),
    ]

    # Page 4 - formal statistical test.
    content += [
        para("Hipótese formal no B2W", css["h1"]),
        para(
            "Hipótese do TP1: avaliações negativas tendem a ter textos mais "
            "longos. Comparamos notas 1-2 com notas 4-5, excluindo nota 3. "
            "Aplicamos Mann-Whitney U unilateral (aproximação assintótica, "
            "com correção de empates) porque os comprimentos são assimétricos.",
            css["body"],
        ),
        table([
            ["Análise", "n (notas 1-2 / 4-5)", "Medianas", "p unilateral", "Efeito"],
            ["Todas as avaliações", "35.020 / 80.111", "154 / 102 caracteres", "&lt; 10<super>-300</super>", "P(superioridade)=0,6771"],
            ["Primeira por revisor", "31.313 / 69.028", "154 / 102 caracteres", "&lt; 10<super>-300</super>", "P(superioridade)=0,6762"],
        ], [35 * mm, 39 * mm, 36 * mm, 23 * mm, 40 * mm], css),
        Spacer(1, 8),
        para(
            "No teste principal, U=1.899.459.581,5; a diferença descritiva "
            "entre medianas é 52 caracteres. A probabilidade de superioridade "
            "de 0,6771 significa que, em pares de grupos diferentes, o texto "
            "de nota baixa tende a ser mais longo em cerca de 67,7% das "
            "comparações, contando empates pela metade. O p-valor não é zero.",
            css["body"],
        ),
        figure(ROOT / "reports/b2w_feedback/05_comprimento_por_nota.png",
               116 * mm, "Figura 4. Comprimento dos feedbacks por nota no B2W.", css),
        para(
            "A sensibilidade por primeira avaliação cronológica de cada "
            "revisor preserva quase todo o efeito. Este teste é exploratório: "
            "a hipótese foi formulada após olhar o TP1, e fatores de produto "
            "ou perfil do revisor podem confundir a associação. Mann-Whitney "
            "não prova, por si só, uma diferença causal ou de medianas.",
            css["body"],
        ),
        PageBreak(),
    ]

    # Page 5 - API and security evidence.
    content += [
        para("API e controles OWASP", css["h1"]),
        table([
            ["Controle", "Implementação e evidência"],
            ["Validação", "Modelos de entrada Pydantic com extra='forbid'; campos inesperados retornam 422."],
            ["Persistência e BOLA", "SQLModel com PostgreSQL; recursos vinculados ao usuário; leitura por ID exige dono ou administrador."],
            ["Headers e CORS", "HSTS, X-Frame-Options, X-Content-Type-Options e CSP; origens CORS em allowlist explícita."],
            ["Brute force", "POST /auth/token: 5 tentativas por IP em janela móvel de 60 segundos; resposta 429 com Retry-After."],
        ], [45 * mm, 128 * mm], css),
        para("Justificativa e limite do rate limiting", css["h2"]),
        para(
            "Cinco tentativas por minuto reduzem rajadas de tentativa de "
            "senha e ainda toleram poucos erros de digitação. É uma escolha "
            "para demonstração local, não garantia universal: o contador "
            "fica na memória, reinicia com o processo, não é compartilhado "
            "entre workers e une usuários atrás do mesmo IP/NAT. Produção "
            "exige armazenamento compartilhado, tratamento de proxy/IP e "
            "monitoramento.", css["body"],
        ),
        para("Verificações executadas", css["h2"]),
        bullet("pytest tests/: 16 testes passaram, cobrindo ausência de token, BOLA, campo extra, cadastro sem privilégio, CORS, headers e limite de autenticação.", css["body"]),
        bullet("Smoke test com PostgreSQL 16.15: recurso de B retornou 403 para A, 200 para B e 401 sem token; continuou acessível após reinício da API.", css["body"]),
        bullet("OWASP ZAP 2.17.0 real, análise passiva sem autenticação: 17 URLs importadas; relatório HTML/JSON exportado com execução concluída.", css["body"]),
        para("Finding Medium do ZAP", css["h2"]),
        para(
            "CSP style-src 'unsafe-inline' em /docs: <b>risco aceito para "
            "o TP2 local, não corrigido</b>. A exceção permite estilos "
            "inline na interface Swagger; removê-la sem validar "
            "compatibilidade pode quebrar a documentação. Scripts são "
            "restringidos à origem própria e a hash específico, e a "
            "exceção não vale para as demais respostas. Antes de exposição "
            "pública, restringir /docs ou validar uma interface com CSP "
            "mais estrita. Não houve finding High.", css["body"],
        ),
        PageBreak(),
    ]

    # Page 6 - limitations, handoff and references.
    content += [
        para("Limitações e próximos passos", css["h1"]),
        bullet("O Bitext é inglês e híbrido/sintético; frequências e métricas internas não representam automaticamente chamados reais em português.", css["body"]),
        bullet("O B2W contém avaliações de produto de 2018, não chamados de suporte com intenção original.", css["body"]),
        bullet("A amostra humana de 500 é estratificada por nota; 78 casos incertos ficam fora da métrica principal. Não deve estimar a distribuição natural do atendimento.", css["body"]),
        bullet("O ZAP foi passivo e sem autenticação. Não prova ausência de IDOR ou falhas de negócio; testes de ownership são evidência separada.", css["body"]),
        bullet("/predictions/predict ainda grava resposta placeholder. Integrar e validar o modelo é etapa posterior, não resultado deste TP2.", css["body"]),
        para("Entrega e referências", css["h1"]),
        para(
            "Código, notebooks e relatórios: <link href='" + BRANCH_URL + "' color='#185b91'>branch feature/integracao-tp2-dados-seguranca</link>.<br/>"
            "Findings detalhados: <link href='" + REPORT_URL + "' color='#185b91'>relatório OWASP ZAP</link>.<br/>"
            "Exportação da ferramenta: <link href='" + ZAP_HTML_URL + "' color='#185b91'>relatório ZAP em HTML</link>.<br/>"
            "EDA estruturada: <link href='" + REPORT_URL.replace("relatorio_owasp_zap.md", "tp2_data_eda/relatorio.md") + "' color='#185b91'>relatório TP2 de dados</link>.",
            css["body"],
        ),
        para(
            "Fontes dos dados: "
            "<link href='https://github.com/americanas-tech/b2w-reviews01' color='#185b91'>B2W-Reviews01 (CC BY-NC-SA 4.0)</link>; "
            "<link href='https://huggingface.co/datasets/bitext/Bitext-retail-ecommerce-llm-chatbot-training-dataset' color='#185b91'>Bitext Retail eCommerce (CDLA-Sharing-1.0)</link>.",
            css["body"],
        ),
        para(
            "Este PDF resume a evidência versionada na branch. Os dados "
            "brutos não foram incorporados ao PDF ou ao Git por tamanho e "
            "licença; os scripts de download e verificação estão no repositório.",
            css["small"],
        ),
    ]

    doc.build(content, onFirstPage=footer, onLaterPages=footer)
    return OUTPUT


if __name__ == "__main__":
    print(build())
