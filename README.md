# EcomShield Platform

Plataforma de seguranca e monitoramento para ecossistemas de comercio eletronico. O EcomShield Platform foi desenvolvido para auxiliar lojas virtuais a detectar fraudes, monitorar transacoes em tempo real e proteger operacoes contra ameacas digitais.

## Indice

- [Sobre o Projeto](#sobre-o-projeto)
- [Arquitetura](#arquitetura)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Pre-requisitos](#pre-requisitos)
- [Quick Start](#quick-start)
- [Configuracao](#configuracao)
- [Contribuicao](#contribuicao)
- [Licenca](#licenca)

## Sobre o Projeto

O EcomShield Platform atua como uma camada de protecao intermediaria para arquiteturas de e-commerce. A solucao processa dados de transacoes, identifica padroes suspeitos de comportamento do usuario e fornece relatorios gerenciais para analistas de risco e seguranca.

## Arquitetura

O sistema e composto por servicos modulares orientados a microsservicos, garantindo alta disponibilidade, escalabilidade horizontal e isolamento de falhas criticas de processamento.

## Tecnologias Utilizadas

- **Backend:** Node.js / Python (conforme especificacao do modulo)
- **Banco de Dados:** PostgreSQL / Redis
- **Containerizacao:** Docker e Docker Compose
- **Controle de Versao:** Git e GitHub

## Pre-requisitos

Antes de iniciar, certifique-se de ter instalado em sua maquina:

- Git
- Docker e Docker Compose (recomendado)
- Node.js (versao 18 ou superior) ou Python (versao 3.10 ou superior)

## Quick Start

Siga os passos abaixo para colocar o projeto em execucao localmente em poucos minutos:

1. Clone o repositorio:
```bash
git clone https://github.com/danielssaugusto/ecomshield-platform.git
```

2. Acesse o diretorio do projeto:
```bash
cd ecomshield-platform
```

3. Crie um arquivo de configuracao de ambiente a partir do exemplo fornecido:
```bash
cp .env.example .env
```

4. Suba os servicos essenciais utilizando o Docker Compose:
```bash
docker-compose up -d
```

5. Instale as dependencias da aplicacao (caso execute fora do container):
```bash
npm install
```

6. Inicie a aplicacao em modo de desenvolvimento:
```bash
npm run dev
```

O servico estara disponivel por padrao na porta `3000` (ou na porta configurada no arquivo `.env`).

## Configuracao

As variaveis de ambiente fundamentais para a execucao do sistema estao listadas abaixo. Preencha-as corretamente no arquivo `.env`:

- `PORT`: Porta de execucao do servidor.
- `DATABASE_URL`: String de conexao com o banco de dados relacional.
- `REDIS_URL`: URL de conexao com o servidor de cache/mensageria.

## Contribuicao

1. Faca um fork do repositorio.
2. Crie uma branch para a sua feature (`git checkout -b feature/nome-da-feature`).
3. Faca o commit das suas alteracoes (`git commit -m 'Adiciona nova funcionalidade'`).
4. Faca o push para a branch (`git push origin feature/nome-da-feature`).
5. Abra um Pull Request.

## Licenca

Este projeto e os datasets derivados utilizam a licença **Creative Commons Attribution 4.0 International (CC BY 4.0)**.
