# 🚀 Guia de Implantação Profissional - HO Pan Dashboard (CobHub)

**Versão:** 2.0.0  
**Autor:** Manus AI para CobHub  
**Data:** 08 de outubro de 2025

---

## 1. Introdução

Este documento detalha a arquitetura e o processo de implantação profissional do **HO Pan Dashboard**, uma aplicação oficial da CobHub. A solução foi projetada para ser segura, escalável, e facilmente atualizável, utilizando as melhores práticas de mercado com **Google Cloud Platform (GCP)** e **GitHub**.

A aplicação consiste em um dashboard analítico construído com Flask (Python), que serve uma interface moderna e interativa, protegida por um sistema de autenticação robusto. Os dados são processados no backend e atualizados em um repositório GitHub, garantindo desacoplamento e versionamento dos dados.

### 1.1. Arquitetura da Solução

A arquitetura foi desenhada para ser modular e escalável, separando as responsabilidades em diferentes componentes:

| Componente | Tecnologia | Responsabilidade |
| :--- | :--- | :--- |
| **Frontend** | Flask (Templates Jinja2) | Renderização da interface do usuário, incluindo a tela de login e o dashboard principal. |
| **Backend** | Flask (Python) | Gerenciamento de autenticação, sessões de usuário, e serviço de uma API segura para os dados. |
| **Processamento de Dados** | Pandas (Python) | Transformação e enriquecimento dos dados brutos (Excel) em um formato otimizado (JSON). |
| **Armazenamento de Dados** | GitHub | O arquivo `dashboard_data.json` é armazenado e versionado em um repositório GitHub, servindo como uma "base de dados" desacoplada. |
| **Hospedagem** | Google Cloud Run | Plataforma serverless para hospedar a aplicação, garantindo escalabilidade automática e alta disponibilidade. |
| **CI/CD** | GitHub Actions | Automação do processo de build, teste e deploy da aplicação a cada atualização no repositório. |
| **Segurança** | Werkzeug, Flask-Session | Gerenciamento de senhas com hash e sessões seguras do lado do servidor. |

![Arquitetura](https-placeholder-for-diagram)

### 1.2. Fluxo de Dados e Atualização

1.  **Login:** O usuário acessa a aplicação e se autentica através da tela de login.
2.  **Carregamento do Dashboard:** Após o login, o frontend solicita os dados para a API interna (`/api/data`).
3.  **Serviço de Dados:** O backend (Flask) verifica se há uma cópia recente dos dados em cache local. Caso contrário, baixa a versão mais recente do `dashboard_data.json` do repositório GitHub.
4.  **Renderização:** O frontend recebe os dados em formato JSON e renderiza todas as visualizações e análises.
5.  **Atualização (Admin):** Um usuário com perfil de administrador pode enviar um novo arquivo Excel através de uma interface (ou API). O backend processa o arquivo, gera um novo `dashboard_data.json` e o atualiza no repositório GitHub, acionando a atualização para todos os usuários.

---

## 2. Pré-requisitos

Antes de iniciar, garanta que você possui as seguintes ferramentas e acessos:

- **Conta no Google Cloud Platform:** Com permissões para criar projetos e habilitar APIs.
- **Conta no GitHub:** Com permissões para criar repositórios e configurar secrets.
- **gcloud CLI:** A ferramenta de linha de comando do GCP. [Instruções de instalação](https://cloud.google.com/sdk/docs/install).
- **Docker:** Para construir a imagem da aplicação localmente (opcional, para testes). [Instruções de instalação](https://docs.docker.com/get-docker/).
- **Python 3.10+:** Para executar scripts de configuração.

---

## 3. Configuração do Ambiente GCP (Passo a Passo)

Para simplificar a configuração de todos os recursos necessários no GCP, foi criado um script automatizado. Ele irá configurar o projeto, habilitar as APIs, criar uma Service Account com as permissões corretas e gerar as credenciais necessárias.

**Execute o seguinte comando no seu terminal, na raiz do projeto:**

```bash
chmod +x ./config/setup-gcp.sh
./config/setup-gcp.sh
```

O script solicitará o **ID do seu projeto GCP** e a **região** desejada. Ao final, ele criará 3 arquivos importantes:

1.  `service-account-key.json`: A chave de credencial da Service Account. **NUNCA adicione este arquivo ao Git.**
2.  `.env.production`: Um arquivo com variáveis de ambiente, incluindo uma senha de administrador gerada automaticamente.
3.  `github-secrets.txt`: Um arquivo contendo os nomes e valores dos secrets que você deve configurar no seu repositório GitHub.

Siga as instruções no arquivo `PROXIMOS_PASSOS.txt` gerado pelo script para configurar os secrets no seu repositório GitHub. Esta é uma etapa **crucial** para que o pipeline de CI/CD funcione.

---

## 4. Pipeline de CI/CD com GitHub Actions

O arquivo `.github/workflows/deploy.yml` define um pipeline de integração e entrega contínua que automatiza todo o processo de implantação.

### 4.1. Gatilhos (Triggers)

O pipeline é acionado automaticamente quando:

- Um `push` é feito para a branch `main`.
- O workflow é acionado manualmente através da interface do GitHub Actions (`workflow_dispatch`).

### 4.2. Etapas do Pipeline

1.  **Checkout:** O código do repositório é baixado para o ambiente de execução.
2.  **Autenticação no GCP:** O GitHub Actions se autentica no Google Cloud usando a Service Account Key configurada nos secrets.
3.  **Configuração do Docker:** O ambiente é configurado para permitir o envio de imagens para o Google Container Registry (GCR).
4.  **Build da Imagem:** A imagem Docker da aplicação é construída usando o `Dockerfile`.
5.  **Push da Imagem:** A imagem é enviada para o GCR, com a tag do commit SHA e a tag `latest`.
6.  **Deploy no Cloud Run:** O `gcloud run deploy` é executado, atualizando o serviço com a nova imagem e injetando todas as variáveis de ambiente (secrets) necessárias para a aplicação funcionar.
7.  **Resumo:** A URL do serviço é exibida no final do log do pipeline.

Com este pipeline, qualquer atualização no código do dashboard é automaticamente implantada em produção, garantindo agilidade e consistência.

---

## 5. Implantação Manual (Alternativa)

Caso prefira fazer o deploy manualmente, sem usar o GitHub Actions, utilize o script `deploy-manual.sh`.

1.  **Execute o script de setup primeiro:** `./config/setup-gcp.sh`
2.  **Preencha o arquivo `.env.production`** com suas credenciais do GitHub.
3.  **Execute o script de deploy:**

```bash
chmod +x ./config/deploy-manual.sh
./config/deploy-manual.sh
```

Este script irá construir a imagem Docker, enviá-la para o GCR e fazer o deploy no Cloud Run, assim como o pipeline automatizado.

---

## 6. Estrutura de Arquivos do Projeto

```
/hopan-dashboard-pro
├── .github/workflows/deploy.yml  # Pipeline de CI/CD
├── config/
│   ├── setup-gcp.sh              # Script de configuração inicial do GCP
│   └── deploy-manual.sh          # Script de deploy manual
├── static/
│   └── logo.png                  # Logo da CobHub
├── templates/
│   ├── login.html                # Template da página de login
│   └── dashboard.html            # Template do dashboard principal
├── app.py                        # Aplicação principal Flask (backend)
├── Dockerfile                    # Definição da imagem Docker
├── requirements.txt              # Dependências Python
├── .dockerignore                 # Arquivos a serem ignorados pelo Docker
├── .gitignore                    # Arquivos a serem ignorados pelo Git
└── README.md                     # Este guia
```

---

## 7. Gerenciamento de Usuários e Segurança

### 7.1. Adicionando Usuários

O sistema permite a adição de novos usuários através de variáveis de ambiente, sem a necessidade de alterar o código.

1.  **Gere o Hash da Senha:**
    Execute o seguinte comando para gerar um hash seguro para a nova senha:
    ```bash
    python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash(\'senha_do_novo_usuario\'))"
    ```

2.  **Atualize o Secret no GitHub:**
    - Vá para `Settings > Secrets and variables > Actions` no seu repositório.
    - Edite o secret `ADDITIONAL_USERS`.
    - Adicione o novo usuário no formato JSON, como no exemplo abaixo:

    ```json
    {
      "novo_usuario": {
        "password": "hash_gerado_no_passo_1",
        "name": "Nome do Usuário",
        "role": "user"
      },
      "outro_usuario": {
        "password": "outro_hash",
        "name": "Outro Nome",
        "role": "user"
      }
    }
    ```

3.  **Re-execute o Pipeline:**
    Vá na aba "Actions" e rode o workflow "Deploy to Cloud Run" manualmente para que as novas variáveis de ambiente sejam aplicadas.

### 7.2. Níveis de Acesso

- **`admin`**: Acesso total, incluindo a capacidade de atualizar os dados do dashboard.
- **`user`**: Acesso de visualização ao dashboard.

---

## 8. Branding e Customização

- **Logo:** O logo da CobHub está localizado em `/static/logo.png`. Para alterá-lo, simplesmente substitua este arquivo.
- **Cores e Estilos:** As cores e fontes são definidas como variáveis CSS no início de cada arquivo HTML (`<style>`). Altere os valores em `:root` para customizar o tema da aplicação.
- **Textos:** Todos os textos e títulos podem ser editados diretamente nos arquivos de template (`/templates/*.html`).

---

## 9. Conclusão

Esta solução entrega um sistema de dashboard profissional, seguro e escalável. A automação com GitHub Actions e a flexibilidade do Cloud Run permitem que a equipe da CobHub se concentre em evoluir as análises, enquanto a infraestrutura cuida da implantação e da escalabilidade de forma automática.

Para qualquer dúvida, consulte a documentação oficial do GCP e do GitHub ou entre em contato com a equipe de desenvolvimento.

