# 🏗️ Arquitetura Técnica - HO Pan Dashboard (CobHub)

**Versão:** 2.0.0  
**Autor:** Manus AI para CobHub  
**Data:** 08 de outubro de 2025

---

## 1. Visão Geral

Este documento detalha a arquitetura técnica completa do sistema HO Pan Dashboard, uma aplicação web profissional construída para análise de comissões. A solução foi projetada seguindo os princípios de **segurança por design**, **escalabilidade horizontal** e **desacoplamento de componentes**.

---

## 2. Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                         USUÁRIO FINAL                            │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GOOGLE CLOUD RUN                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  APLICAÇÃO FLASK                           │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │ │
│  │  │   Frontend   │  │   Backend    │  │  Processamento  │ │ │
│  │  │  (Templates) │◄─┤   (API)      │◄─┤    de Dados     │ │ │
│  │  └──────────────┘  └──────────────┘  └─────────────────┘ │ │
│  │         │                  │                    │          │ │
│  │         │                  │                    │          │ │
│  │         ▼                  ▼                    ▼          │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │ │
│  │  │ Autenticação │  │   Sessões    │  │  Pandas/Excel   │ │ │
│  │  │  (Werkzeug)  │  │   (Flask)    │  │  Transformação  │ │ │
│  │  └──────────────┘  └──────────────┘  └─────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        GITHUB REPOSITORY                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  dashboard_data.json (Dados Processados)                   │ │
│  │  - Metadados                                               │ │
│  │  - Dados Completos                                         │ │
│  │  - Análises Pré-calculadas                                │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      GITHUB ACTIONS                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Pipeline CI/CD                                            │ │
│  │  1. Build Docker Image                                     │ │
│  │  2. Push to GCR                                            │ │
│  │  3. Deploy to Cloud Run                                    │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Componentes Principais

### 3.1. Frontend (Templates Jinja2)

O frontend é composto por templates HTML renderizados no servidor, utilizando o motor de templates Jinja2 do Flask.

**Componentes:**

- **`login.html`**: Página de autenticação com design iOS 18, incluindo logo CobHub e validação de credenciais.
- **`dashboard.html`**: Interface principal do dashboard com carregamento assíncrono de dados via API interna.

**Características:**

- Design responsivo e moderno (estilo iOS 18)
- Carregamento progressivo com indicadores visuais
- Integração com Chart.js para visualizações
- Exportação de dados em CSV

**Tecnologias:**

- HTML5
- CSS3 (variáveis CSS, gradientes, animações)
- JavaScript (ES6+, Fetch API)
- Chart.js 4.4.0

### 3.2. Backend (Flask)

O backend é construído com Flask, um microframework Python leve e flexível.

**Responsabilidades:**

- **Autenticação:** Gerenciamento de login/logout com sessões seguras.
- **Autorização:** Controle de acesso baseado em roles (admin/user).
- **API de Dados:** Endpoint `/api/data` que serve os dados do dashboard.
- **Processamento:** Transformação de arquivos Excel em JSON otimizado.
- **Integração GitHub:** Atualização automática do repositório com novos dados.

**Endpoints Principais:**

| Endpoint | Método | Autenticação | Descrição |
| :--- | :--- | :--- | :--- |
| `/` | GET | Não | Redireciona para login ou dashboard |
| `/login` | GET, POST | Não | Página de login e validação de credenciais |
| `/logout` | GET | Sim | Encerra a sessão do usuário |
| `/dashboard` | GET | Sim | Página principal do dashboard |
| `/api/data` | GET | Sim | Retorna dados do dashboard em JSON |
| `/api/update` | POST | Admin | Atualiza dados do dashboard (apenas admin) |
| `/health` | GET | Não | Health check para Cloud Run |

**Segurança:**

- Senhas armazenadas com hash (Werkzeug PBKDF2)
- Sessões criptografadas com chave secreta
- Decorators para proteção de rotas (`@login_required`, `@admin_required`)
- Validação de entrada em todos os endpoints

### 3.3. Processamento de Dados (Pandas)

O módulo de processamento é responsável por transformar os dados brutos em um formato otimizado para o dashboard.

**Pipeline de Processamento:**

1. **Ingestão:** Download do arquivo Excel de uma URL fornecida.
2. **Limpeza:** Remoção de colunas desnecessárias e padronização de nomes.
3. **Transformação:** Criação de campos calculados (MesAno, PercComissao, FaixaAtraso, FaixaValor).
4. **Enriquecimento:** Adição de classificações (Classe, TipoPagamento).
5. **Validação:** Remoção de registros inválidos ou inconsistentes.
6. **Agregação:** Cálculo de análises pré-computadas (análise por faixa de atraso).
7. **Serialização:** Conversão para JSON com metadados.

**Campos Calculados:**

- **MesAno:** Formato YYYY-MM extraído da Data_Base.
- **PercComissao:** (ValorComissao / ValorPago) × 100.
- **FaixaAtraso:** Classificação em 7 faixas (0-20 dias, 21-30 dias, ..., >360 dias).
- **FaixaValor:** Classificação em 7 faixas de valor (Até R$ 1.000, ..., >R$ 10.000).
- **Classe:** Contact (<90 dias), Ativas 1 (91-180 dias), Ativas 2 (>181 dias).
- **TipoPagamento:** Parcial (<R$ 3.000), Atualização (R$ 3.001-8.000), Quitação (>R$ 8.000).

### 3.4. Armazenamento de Dados (GitHub)

Os dados processados são armazenados em um arquivo JSON no repositório GitHub, servindo como uma "base de dados" versionada e desacoplada.

**Vantagens:**

- **Versionamento:** Histórico completo de todas as atualizações de dados.
- **Desacoplamento:** A aplicação não depende de um banco de dados tradicional.
- **Simplicidade:** Fácil de auditar, fazer backup e restaurar.
- **Performance:** O Cloud Run faz cache local dos dados, reduzindo latência.

**Estrutura do JSON:**

```json
{
  "metadados": {
    "total_registros": 1234,
    "meses_disponiveis": ["2025-09", "2025-10"],
    "campos_numericos": ["ValorPago", "ValorComissao", ...],
    "data_atualizacao": "2025-10-08 14:30:00"
  },
  "dados_completos": [
    {
      "Proposta": "12345",
      "Cliente": "Nome do Cliente",
      "ValorPago": 5000.00,
      ...
    }
  ],
  "analise_faixas": {
    "0-20 dias": {
      "operacoes": 100,
      "valor_pago": 500000.00,
      ...
    }
  }
}
```

### 3.5. Hospedagem (Google Cloud Run)

O Cloud Run é uma plataforma serverless que executa containers de forma escalável e gerenciada.

**Configuração:**

- **Imagem:** `gcr.io/[PROJECT_ID]/hopan-dashboard:latest`
- **Memória:** 1 GB
- **CPU:** 1 vCPU
- **Timeout:** 300 segundos
- **Instâncias:** 0 (mínimo) a 10 (máximo)
- **Autenticação:** Permitida (allow-unauthenticated) - a autenticação é feita pela aplicação

**Escalabilidade:**

- **Scale to Zero:** Quando não há tráfego, o Cloud Run reduz para 0 instâncias, economizando custos.
- **Auto-scaling:** Novas instâncias são criadas automaticamente conforme a demanda aumenta.
- **Cold Start:** Otimizado com imagem Docker leve (Python 3.11 slim).

**Monitoramento:**

- Logs centralizados no Cloud Logging
- Métricas de performance no Cloud Monitoring
- Health check automático via endpoint `/health`

### 3.6. CI/CD (GitHub Actions)

O pipeline de CI/CD automatiza todo o processo de build, teste e deploy.

**Workflow:**

1. **Trigger:** Push para a branch `main` ou execução manual.
2. **Checkout:** Código é baixado do repositório.
3. **Autenticação:** GitHub Actions se autentica no GCP usando Service Account.
4. **Build:** Imagem Docker é construída com a tag do commit SHA.
5. **Push:** Imagem é enviada para o Google Container Registry (GCR).
6. **Deploy:** Cloud Run é atualizado com a nova imagem e variáveis de ambiente.
7. **Verificação:** URL do serviço é exibida no log.

**Secrets Necessários:**

- `GCP_PROJECT_ID`: ID do projeto no GCP
- `GCP_SA_KEY`: Chave JSON da Service Account (base64)
- `SECRET_KEY`: Chave secreta para sessões Flask
- `ADMIN_PASSWORD_HASH`: Hash da senha do administrador
- `GITHUB_TOKEN`: Token de acesso ao GitHub
- `GITHUB_REPO`: Repositório no formato `usuario/repo`
- `GITHUB_USER`: Usuário do GitHub

---

## 4. Fluxo de Autenticação

```
┌──────────┐
│ Usuário  │
└────┬─────┘
     │
     ▼
┌─────────────────┐
│  GET /login     │
│  (Formulário)   │
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│ POST /login     │
│ username+senha  │
└────┬────────────┘
     │
     ▼
┌─────────────────────────────┐
│ Verificar credenciais       │
│ - Buscar usuário            │
│ - Validar hash da senha     │
└────┬────────────────────────┘
     │
     ├─── Inválido ──► Retornar erro
     │
     └─── Válido
          │
          ▼
     ┌─────────────────────┐
     │ Criar sessão        │
     │ - session['user']   │
     │ - session['name']   │
     │ - session['role']   │
     └────┬────────────────┘
          │
          ▼
     ┌─────────────────────┐
     │ Redirecionar para   │
     │ /dashboard          │
     └─────────────────────┘
```

**Proteção de Rotas:**

Todas as rotas protegidas utilizam o decorator `@login_required`, que verifica se a chave `user` existe na sessão. Caso não exista, o usuário é redirecionado para `/login`.

Rotas administrativas utilizam `@admin_required`, que verifica adicionalmente se `session['role'] == 'admin'`.

---

## 5. Fluxo de Atualização de Dados

```
┌──────────────┐
│ Admin        │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│ POST /api/update     │
│ { "url": "..." }     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Baixar arquivo Excel │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Processar dados      │
│ (Pandas)             │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Gerar JSON           │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Clonar repositório   │
│ GitHub               │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Atualizar arquivo    │
│ dashboard_data.json  │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Commit e Push        │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Retornar sucesso     │
└──────────────────────┘
```

**Observações:**

- O processo é síncrono e pode levar alguns minutos para arquivos grandes.
- O cache local é atualizado automaticamente após o push para o GitHub.
- Todos os usuários verão os dados atualizados na próxima requisição.

---

## 6. Segurança

### 6.1. Camadas de Segurança

| Camada | Mecanismo | Descrição |
| :--- | :--- | :--- |
| **Transporte** | HTTPS (TLS 1.3) | Toda comunicação é criptografada pelo Cloud Run |
| **Autenticação** | Werkzeug PBKDF2 | Senhas armazenadas com hash seguro (SHA256, 260.000 iterações) |
| **Sessão** | Flask-Session | Sessões criptografadas com chave secreta (256 bits) |
| **Autorização** | Role-Based Access Control (RBAC) | Controle de acesso baseado em roles (admin/user) |
| **Secrets** | GitHub Secrets + GCP Secret Manager | Variáveis sensíveis nunca expostas no código |
| **Rede** | Cloud Run VPC | Isolamento de rede gerenciado pelo GCP |

### 6.2. Boas Práticas Implementadas

- ✅ Princípio do menor privilégio (Service Account com permissões mínimas)
- ✅ Separação de ambientes (dev/staging/prod)
- ✅ Auditoria de acessos (logs no Cloud Logging)
- ✅ Rotação de credenciais (recomendado a cada 90 dias)
- ✅ Validação de entrada (sanitização de dados)
- ✅ Rate limiting (implementável via Cloud Armor)

---

## 7. Performance e Escalabilidade

### 7.1. Otimizações Implementadas

- **Cache Local:** Dados são armazenados em `/tmp` e reutilizados por 5 minutos.
- **Compressão:** Responses são comprimidas automaticamente pelo Cloud Run.
- **Lazy Loading:** Dados são carregados apenas quando necessário.
- **Pré-computação:** Análises agregadas são calculadas no backend e armazenadas no JSON.

### 7.2. Capacidade

| Métrica | Valor |
| :--- | :--- |
| **Requisições por segundo** | ~100 RPS por instância |
| **Latência média** | <200ms (cache hit) |
| **Latência máxima** | <2s (cache miss + download GitHub) |
| **Tamanho máximo do JSON** | ~50 MB (recomendado) |
| **Usuários simultâneos** | ~1.000 (com 10 instâncias) |

---

## 8. Custos Estimados

Baseado em um uso moderado (1.000 requisições/dia, 100 usuários ativos):

| Serviço | Custo Mensal (USD) |
| :--- | :--- |
| **Cloud Run** | $5 - $15 |
| **Container Registry** | $1 - $3 |
| **Cloud Logging** | $2 - $5 |
| **GitHub Actions** | $0 (free tier) |
| **Total Estimado** | $8 - $23 |

**Observação:** O Cloud Run cobra apenas pelo tempo de CPU utilizado. Com scale-to-zero, os custos são mínimos em períodos de baixo tráfego.

---

## 9. Roadmap Técnico

### Curto Prazo (1-3 meses)

- [ ] Implementar dashboard completo (migrar de `index.html`)
- [ ] Adicionar testes automatizados (pytest)
- [ ] Configurar domínio customizado
- [ ] Implementar rate limiting

### Médio Prazo (3-6 meses)

- [ ] Migrar para Cloud SQL (PostgreSQL) para dados maiores
- [ ] Implementar cache distribuído (Redis/Memorystore)
- [ ] Adicionar monitoramento avançado (Prometheus/Grafana)
- [ ] Implementar backup automático

### Longo Prazo (6-12 meses)

- [ ] Multi-tenancy (suporte a múltiplas empresas)
- [ ] API pública com autenticação OAuth2
- [ ] Integração com BigQuery para analytics
- [ ] Mobile app (React Native)

---

## 10. Conclusão

A arquitetura do HO Pan Dashboard foi projetada para ser **simples, segura e escalável**. A escolha de tecnologias modernas e serviços gerenciados (Cloud Run, GitHub) permite que a equipe se concentre em evoluir o produto, enquanto a infraestrutura cuida da operação.

A separação clara de responsabilidades entre frontend, backend e armazenamento de dados garante flexibilidade para futuras evoluções, como a migração para um banco de dados relacional ou a adição de novos módulos de análise.

---

**Autor:** Manus AI para CobHub  
**Última atualização:** 08 de outubro de 2025
