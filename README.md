# 🐾 Perfumaria Pettit Gateau

**E-commerce de perfumaria de nicho focado em alta escalabilidade e integridade de dados.**

Este projeto é um ecossistema completo de vendas online, desenvolvido para demonstrar práticas avançadas de arquitetura de software, modelagem de dados internacionalizável e segurança de back-end.

---

## 🚀 Status do Projeto: [Fase 6 - Carrinho de Compras e Sessões (API-Driven)]
O Front-end público (Vitrine PLP com filtros avançados, busca textual e paginação, além dos Detalhes PDP) foi implementado com sucesso utilizando Server-Side Rendering (SSR) otimizado para SEO. Iniciando agora a arquitetura transacional: criação do Carrinho de Compras e controle de Sessões utilizando integrações assíncronas.

## 🧠 Diferenciais Técnicos (O que este projeto resolve)

Diferente de e-commerces básicos, o **Pettit Gateau** foi projetado com:

* **Arquitetura Híbrida Estratégica:** Separação inteligente de responsabilidades. Uso de **SSR (Django Templates)** nas áreas públicas para maximizar SEO e performance (Time-to-First-Byte), e preparação para **API-Driven (DRF)** nas áreas transacionais (Carrinho/Checkout) garantindo fluidez e escalabilidade.
* **Custom User Model (Email Auth):** Substituição do padrão de *Username* do Django pela autenticação via E-mail, otimizando o fluxo de checkout e melhorando a UX.
* **Gestão Logística 1:N:** Modelagem de múltiplos endereços por cliente estruturada com chaves estrangeiras, `is_default` flag para cálculo de frete rápido, e proteção de dados alinhada à LGPD (Exclusão em Cascata).
* **Arquitetura de SKU:** Separação lógica entre Produto (Identidade) e SKU (Logística), permitindo variações de volume (50ml, 100ml) com controle de estoque independente.
* **Data Integrity (Snapshotting):** Registro histórico de preços para garantir que alterações no catálogo não corrompam o faturamento retroativo.
* **Security First:** Uso de **UUIDs** (Universal Unique Identifiers) e abstração de *BaseModels* para mitigar ataques de enumeração e garantir auditoria (created_at/updated_at).
* **Global Standards:** Nomenclatura técnica em inglês, aderindo aos padrões das melhores equipes de engenharia de software.

## 🔄 Workflow de Desenvolvimento (Git)

Este projeto adota o **GitHub Flow** como estratégia oficial de versionamento, visando entregas ágeis e integração contínua.
* A branch **`main`** é a única fonte da verdade e reflete o estado estável/produção do projeto.
* Novas implementações utilizam branches efêmeras (`feature/nome-da-tarefa`).
* A integração é feita exclusivamente via **Pull Requests (PRs)** diretos para a `main`, mantendo o histórico linear e dispensando o uso de ramificações intermediárias duradouras (como `develop`).

## 🛠️ Stack Tecnológica

* **Linguagem:** Python 3.x
* **Framework:** Django & Django REST Framework (DRF)
* **Banco de Dados:** PostgreSQL (Relacional Robusto)
* **Ambiente:** Docker & Docker Compose (Containerização)
* **Front-end:** HTML5, CSS3, Vanilla JavaScript
* **Segurança:** Python-Decouple (Gestão de .env)
* **Modelagem:** DBML / DBDiagram.io

## 🗺️ Roadmap de Desenvolvimento

- [x] Levantamento de Requisitos e Regras de Negócio
- [x] Modelagem Lógica de Entidades (ERD) e Governança (Git)
- [x] Implementação do Core e Base Models (UUID/Audit)
- [x] Desenvolvimento do Módulo de Catálogo & Variações (SKUs)
- [x] Módulo de Clientes (Auth Customizada & Múltiplos Endereços)
- [x] Construção do Front-end Reativo (Views, Templates e JS)
- [x] Filtros Dinâmicos PLP
- [ ] Fluxo de Carrinho de Compras e Sessões
- [ ] Checkout e Integridade de Pedidos
- [ ] Deploy Automatizado e Documentação de API

---
*Desenvolvido por **Brendon** como parte do portfólio profissional de Software Development.*
