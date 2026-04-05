# 🐾 Perfumaria Pettit Gateau

**E-commerce de perfumaria de nicho focado em alta escalabilidade e integridade de dados.**

Este projeto é um ecossistema completo de vendas online, desenvolvido para demonstrar práticas avançadas de arquitetura de software, modelagem de dados internacionalizável e segurança de back-end.

---

## 🚀 Status do Projeto: [Fase 2 - Catálogo e Admin]
Ambiente de desenvolvimento configurado. Módulos principais de Catálogo (Produtos, SKUs e Imagens) modelados com sucesso e integrados ao painel administrativo.

## 🧠 Diferenciais Técnicos (O que este projeto resolve)

Diferente de e-commerces básicos, o **Pettit Gateau** foi projetado com:

* **Arquitetura de SKU:** Separação lógica entre Produto (Identidade) e SKU (Logística), permitindo variações de volume (50ml, 100ml) e concentração (EDP, EDT) com controle de estoque independente.
* **Data Integrity (Snapshotting):** Implementação de registro histórico de preços no ato da venda, garantindo que alterações no catálogo não corrompam o faturamento retroativo.
* **Security First:** Uso de **UUIDs** (Universal Unique Identifiers) em todas as entidades transacionais para mitigar ataques de enumeração de dados.
* **Global Standards:** Nomenclatura técnica em inglês e suporte a múltiplos endereços por cliente, seguindo padrões de APIs internacionais.

## 🔄 Workflow de Desenvolvimento (Git)

Este projeto adota o **GitHub Flow** como estratégia oficial de versionamento, visando entregas ágeis e integração contínua.
* A branch **`main`** é a única fonte da verdade e reflete o estado estável/produção do projeto.
* Novas implementações utilizam branches efêmeras (`feature/nome-da-tarefa`).
* A integração é feita exclusivamente via **Pull Requests (PRs)** diretos para a `main`, mantendo o histórico linear e dispensando o uso de ramificações intermediárias duradouras (como `develop`).

## 🛠️ Stack Tecnológica

* **Linguagem:** Python 3.x
* **Framework:** Django (Web Framework for perfectionists)
* **Banco de Dados:** PostgreSQL (Relacional Robusto)
* **Ambiente:** Docker & Docker Compose (Containerização)
* **Segurança:** Python-Decouple (Gestão de .env)
* **Modelagem:** DBML / DBDiagram.io

## 🗺️ Roadmap de Desenvolvimento

- [x] Levantamento de Requisitos e Regras de Negócio
- [x] Modelagem Lógica de Entidades (ERD)
- [x] Configuração de Governança (Git/GitHub)
- [ ] Implementação do Core e Base Models (UUID/Audit)
- [ ] Desenvolvimento do Módulo de Catálogo & SKUs
- [ ] Fluxo de Checkout e Integridade de Pedidos
- [ ] Deploy Automatizado e Documentação de API

---
*Desenvolvido por **Brendon** como parte do portfólio profissional de Software Development.*