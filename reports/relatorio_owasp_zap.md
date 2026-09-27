# TP2 — verificação com OWASP ZAP

## Execução e escopo

Em **26/09/2026, 22h37 (America/Sao_Paulo)**, executamos o **OWASP ZAP
2.17.0** portátil contra a API local em `http://127.0.0.1:8000`, usando
**PostgreSQL 16.15 em um banco descartável**. O ZAP foi obtido da distribuição
oficial; o SHA-256 do arquivo `ZAP_2.17.0_Crossplatform.zip` foi
`94c8f767b1c2e94f0db66b3ae56514d5e3f5a728ee1b6c798e0c8fe2d61fbff0`.

Comando usado, apontando para o diretório temporário da distribuição:

```bash
python scripts/run_owasp_zap_scan.py \
  --zap-home /caminho/ZAP_2.17.0 \
  --target http://127.0.0.1:8000 \
  --import-openapi
```

A automação solicitou oito recursos diretamente (saúde, OpenAPI, Swagger,
ReDoc, três assets locais e uma rota protegida, cuja resposta esperada era
401), importou **17 URLs** da especificação OpenAPI e aguardou a análise
**passiva**. A importação pode enviar requisições POST; só use
`--import-openapi` com banco descartável. Sem essa opção, o modo portátil faz
somente as requisições explícitas de leitura. O modo Docker padrão continua
disponível com `python scripts/run_owasp_zap_scan.py`.

Evidências exportadas diretamente pelo ZAP: [HTML](zap_report.html),
[JSON](zap_report.json) e [log da execução](zap_scan.log). A execução terminou
com código **0** e `Automation plan succeeded!`. Os relatórios antigos,
gerados por um simulador, foram substituídos e não são usados como evidência.

## Resultado e triagem

| Risco ZAP | Regra / ocorrências | Triagem |
| --- | --- | --- |
| Alto | Nenhuma | — |
| Médio | `10055` CSP `style-src unsafe-inline` / 1 | **Risco aceito para o TP2 local**, não corrigido. A exceção permite CSS inline na página `/docs`; se houver injeção de conteúdo nessa página, CSS malicioso pode ser aplicado. O bundle do Swagger UI contém operações de estilo dinâmico; a compatibilidade após retirar a exceção não foi verificada em navegador. O escopo é somente a documentação: scripts são limitados à origem própria e ao hash do script inline; a API não usa essa exceção nas demais respostas. Antes de expor `/docs` publicamente, testar uma UI com CSP estrita ou restringir o acesso à documentação. |
| Baixo | `2` Private IP Disclosure / 1 | **Falso positivo contextual**: `192.168.0.1` está no bundle estático do ReDoc; não é endereço revelado pelo backend. |
| Baixo | `10096` Timestamp Disclosure / 5 | **Falso positivo contextual**: constantes embutidas no bundle estático do Swagger UI, não timestamps de usuários ou transações. |
| Informativo | `10111` Authentication Request Identified / 1 | `/auth/token` identificado corretamente; não é vulnerabilidade. |
| Informativo | `10027` Suspicious Comments / 2 | Correspondências em bundles estáticos de terceiros; sem segredo ou comentário próprio identificado nessa evidência. |
| Informativo | `10109` Modern Web Application / 2 | Classificação de Swagger e ReDoc; não é vulnerabilidade. |

Antes da correção, a documentação carregava bibliotecas por CDN e gerava
alertas de dependência externa/SRI. Swagger UI e ReDoc agora são servidos
localmente com versões e hashes documentados em
[`src/app/static/THIRD_PARTY.md`](../src/app/static/THIRD_PARTY.md). Isso
eliminou aqueles alertas, mas **não** o aviso médio de `unsafe-inline`.
O status **aceito** acima é uma decisão de risco para o ambiente local de
entrega, não uma afirmação de que o alerta seja falso positivo ou de que a
documentação seja segura para exposição pública irrestrita.

## Autorização e limites da evidência

O ZAP fez análise passiva **sem sessão autenticada**. Logo, não prova ausência
de IDOR/BOLA, SQL injection explorável ou falhas nas regras de negócio. A
autorização por objeto tem evidência separada: os testes em
`tests/test_security.py` e `tests/test_api.py` passaram; no smoke test real
com PostgreSQL, a avaliação criada pelo usuário B retornou **403** ao usuário
A, **200** a B e **401** sem token. A avaliação continuou disponível a B após
reiniciar a API, confirmando persistência no PostgreSQL.

O ZAP registrou `No check for updates for over 3 month`, então os add-ons
podem estar desatualizados. Para uma avaliação de segurança mais completa,
seriam necessários um scan autenticado, testes ativos controlados em ambiente
descartável e revisão manual; estes **não** foram realizados aqui.

Referências: [ZAP Automation Framework](https://www.zaproxy.org/docs/desktop/addons/automation-framework/),
[ZAP Baseline Scan](https://www.zaproxy.org/docs/docker/baseline-scan/).
