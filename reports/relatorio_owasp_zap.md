# TP2 — verificação passiva com OWASP ZAP

## Estado da evidência

**Pendente de execução real.** Os antigos `zap_report.html` e
`zap_report.json` foram removidos porque eram produzidos por um simulador com
alertas escritos no código, e não exportados pelo OWASP ZAP. Eles não eram
evidência válida de scan. Nenhum resultado ou risco abaixo é atribuído ao ZAP
antes de rodar a ferramenta.

## Procedimento reprodutível

1. Inicie a API localmente com banco configurado e confirme
   `http://localhost:8000/health` e `http://localhost:8000/openapi.json`.
2. Com Docker disponível, execute
   `python scripts/run_owasp_zap_scan.py`. O script roda a imagem oficial
   `ghcr.io/zaproxy/zaproxy:stable` com `zap-baseline.py` e exporta
   `reports/zap_report.html` e `reports/zap_report.json` diretamente do ZAP.
3. Registre aqui a data, versão da imagem, URL, quantidade de URLs observadas,
   alertas reais, severidades, triagem (corrigido/aceito/pendente) e links para
   os dois relatórios exportados. Um scan passivo sem autenticação **não**
   demonstra ausência de BOLA/IDOR nas rotas protegidas; use os testes de
   autorização como evidência separada.

Referência do procedimento: [ZAP Baseline Scan](https://www.zaproxy.org/docs/docker/baseline-scan/).
