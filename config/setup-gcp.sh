#!/bin/bash

# Script de Configuração Inicial do GCP para HO Pan Dashboard
# Este script configura todos os recursos necessários no Google Cloud Platform

set -e

echo "🚀 Iniciando configuração do GCP para HO Pan Dashboard"
echo "=================================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para printar mensagens coloridas
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se gcloud está instalado
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI não está instalado. Por favor, instale: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

print_info "gcloud CLI encontrado"

# Solicitar informações do projeto
read -p "Digite o ID do seu projeto GCP: " PROJECT_ID
read -p "Digite a região preferida (padrão: us-central1): " REGION
REGION=${REGION:-us-central1}

print_info "Configurando projeto: $PROJECT_ID"
print_info "Região: $REGION"

# Configurar projeto padrão
gcloud config set project $PROJECT_ID

# Verificar se o projeto existe
if ! gcloud projects describe $PROJECT_ID &> /dev/null; then
    print_error "Projeto $PROJECT_ID não encontrado. Verifique o ID do projeto."
    exit 1
fi

print_info "Projeto verificado com sucesso"

# Habilitar APIs necessárias
print_info "Habilitando APIs necessárias..."

APIS=(
    "run.googleapis.com"
    "containerregistry.googleapis.com"
    "cloudbuild.googleapis.com"
    "secretmanager.googleapis.com"
    "iam.googleapis.com"
)

for api in "${APIS[@]}"; do
    print_info "Habilitando $api..."
    gcloud services enable $api --project=$PROJECT_ID
done

print_info "Todas as APIs foram habilitadas"

# Criar Service Account
SERVICE_ACCOUNT_NAME="hopan-dashboard-sa"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

print_info "Criando Service Account..."

if gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL --project=$PROJECT_ID &> /dev/null; then
    print_warning "Service Account já existe"
else
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="HO Pan Dashboard Service Account" \
        --project=$PROJECT_ID
    print_info "Service Account criada: $SERVICE_ACCOUNT_EMAIL"
fi

# Atribuir roles necessárias
print_info "Atribuindo permissões..."

ROLES=(
    "roles/run.admin"
    "roles/storage.admin"
    "roles/cloudbuild.builds.builder"
    "roles/iam.serviceAccountUser"
)

for role in "${ROLES[@]}"; do
    print_info "Atribuindo $role..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="$role" \
        --quiet
done

# Criar chave da Service Account
KEY_FILE="service-account-key.json"
print_info "Criando chave da Service Account..."

gcloud iam service-accounts keys create $KEY_FILE \
    --iam-account=$SERVICE_ACCOUNT_EMAIL \
    --project=$PROJECT_ID

print_info "Chave criada: $KEY_FILE"

# Gerar senha de admin segura
ADMIN_PASSWORD=$(openssl rand -base64 24)
print_info "Senha de admin gerada"

# Criar arquivo de variáveis de ambiente
ENV_FILE=".env.production"
cat > $ENV_FILE << EOF
# Configurações do GCP
GCP_PROJECT_ID=$PROJECT_ID
GCP_REGION=$REGION
GCP_SERVICE_ACCOUNT=$SERVICE_ACCOUNT_EMAIL

# Configurações da aplicação
SECRET_KEY=$(openssl rand -hex 32)
ADMIN_PASSWORD=$ADMIN_PASSWORD

# Configurações do GitHub (preencha com seus valores)
GITHUB_TOKEN=seu_github_token_aqui
GITHUB_REPO=seu_usuario/seu_repositorio
GITHUB_USER=seu_usuario

# Service Account Key (caminho)
GOOGLE_APPLICATION_CREDENTIALS=./$KEY_FILE
EOF

print_info "Arquivo de ambiente criado: $ENV_FILE"

# Criar arquivo de secrets para GitHub
SECRETS_FILE="github-secrets.txt"
cat > $SECRETS_FILE << EOF
# Secrets para configurar no GitHub Actions
# Vá em: Settings > Secrets and variables > Actions > New repository secret

GCP_PROJECT_ID=$PROJECT_ID
GCP_SA_KEY=$(cat $KEY_FILE | base64 -w 0)
SECRET_KEY=$(grep SECRET_KEY $ENV_FILE | cut -d'=' -f2)
ADMIN_PASSWORD_HASH=\$(python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('$ADMIN_PASSWORD'))")

# Preencha estes com seus valores:
GITHUB_TOKEN=seu_github_token_aqui
GITHUB_REPO=seu_usuario/seu_repositorio
GITHUB_USER=seu_usuario

# Opcional - Usuários adicionais (formato JSON)
ADDITIONAL_USERS={}
EOF

print_info "Arquivo de secrets criado: $SECRETS_FILE"

# Criar arquivo de instruções
INSTRUCTIONS_FILE="PROXIMOS_PASSOS.txt"
cat > $INSTRUCTIONS_FILE << EOF
✅ Configuração do GCP concluída com sucesso!

📋 PRÓXIMOS PASSOS:

1. CREDENCIAIS GERADAS:
   - Service Account Key: $KEY_FILE
   - Variáveis de ambiente: $ENV_FILE
   - Secrets do GitHub: $SECRETS_FILE
   - Senha de Admin: $ADMIN_PASSWORD

   ⚠️  IMPORTANTE: Guarde a senha de admin em local seguro!

2. CONFIGURAR GITHUB:
   a) Vá até seu repositório no GitHub
   b) Acesse: Settings > Secrets and variables > Actions
   c) Adicione cada secret do arquivo $SECRETS_FILE
   d) Preencha os valores do GitHub Token, Repo e User

3. FAZER PRIMEIRO DEPLOY:
   a) Commit e push do código para o repositório
   b) O GitHub Actions fará o deploy automaticamente
   c) Ou execute manualmente: gcloud run deploy

4. ACESSAR O DASHBOARD:
   - Após o deploy, a URL será exibida no GitHub Actions
   - Faça login com: admin / $ADMIN_PASSWORD

5. CONFIGURAR DOMÍNIO CUSTOMIZADO (Opcional):
   - No Cloud Run, vá em "Manage Custom Domains"
   - Adicione seu domínio personalizado
   - Configure os registros DNS

6. ADICIONAR USUÁRIOS:
   - Edite o secret ADDITIONAL_USERS no GitHub
   - Formato JSON: {"usuario": {"password": "hash", "name": "Nome", "role": "user"}}
   - Gere hash com: python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('senha'))"

📚 DOCUMENTAÇÃO:
   - Cloud Run: https://cloud.google.com/run/docs
   - GitHub Actions: https://docs.github.com/actions

🔒 SEGURANÇA:
   - Nunca commite o arquivo $KEY_FILE no Git
   - Mantenha as senhas em local seguro
   - Rotacione as credenciais periodicamente

🎉 Tudo pronto! Seu dashboard está configurado para deployment profissional.
EOF

print_info "Arquivo de instruções criado: $INSTRUCTIONS_FILE"

# Resumo final
echo ""
echo "=================================================="
print_info "✅ Configuração concluída com sucesso!"
echo "=================================================="
echo ""
echo "📁 Arquivos criados:"
echo "   - $KEY_FILE (Service Account Key)"
echo "   - $ENV_FILE (Variáveis de ambiente)"
echo "   - $SECRETS_FILE (Secrets para GitHub)"
echo "   - $INSTRUCTIONS_FILE (Próximos passos)"
echo ""
echo "🔐 Credenciais de Admin:"
echo "   Usuário: admin"
echo "   Senha: $ADMIN_PASSWORD"
echo ""
print_warning "⚠️  IMPORTANTE: Guarde essas credenciais em local seguro!"
echo ""
print_info "📖 Leia o arquivo $INSTRUCTIONS_FILE para os próximos passos"
echo ""
