#!/bin/bash

# Script de Deploy Manual para Cloud Run
# Use este script para fazer deploy manualmente sem GitHub Actions

set -e

echo "🚀 Deploy Manual - HO Pan Dashboard"
echo "===================================="

# Carregar variáveis de ambiente
if [ -f .env.production ]; then
    source .env.production
    echo "✅ Variáveis de ambiente carregadas"
else
    echo "❌ Arquivo .env.production não encontrado"
    echo "Execute primeiro: ./config/setup-gcp.sh"
    exit 1
fi

# Verificar variáveis obrigatórias
if [ -z "$GCP_PROJECT_ID" ]; then
    echo "❌ GCP_PROJECT_ID não definido"
    exit 1
fi

# Configurações
SERVICE_NAME="hopan-dashboard"
REGION="${GCP_REGION:-us-central1}"
IMAGE_NAME="gcr.io/$GCP_PROJECT_ID/$SERVICE_NAME"

echo "📦 Projeto: $GCP_PROJECT_ID"
echo "🌍 Região: $REGION"
echo "🏷️  Serviço: $SERVICE_NAME"
echo ""

# Configurar projeto
gcloud config set project $GCP_PROJECT_ID

# Build da imagem
echo "🔨 Construindo imagem Docker..."
docker build -t $IMAGE_NAME:latest .

# Push para GCR
echo "📤 Enviando imagem para Google Container Registry..."
docker push $IMAGE_NAME:latest

# Deploy no Cloud Run
echo "🚀 Fazendo deploy no Cloud Run..."

# Gerar hash da senha de admin se necessário
if [ -n "$ADMIN_PASSWORD" ] && [ -z "$ADMIN_PASSWORD_HASH" ]; then
    ADMIN_PASSWORD_HASH=$(python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('$ADMIN_PASSWORD'))")
fi

gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="SECRET_KEY=$SECRET_KEY" \
    --set-env-vars="GITHUB_TOKEN=$GITHUB_TOKEN" \
    --set-env-vars="GITHUB_REPO=$GITHUB_REPO" \
    --set-env-vars="GITHUB_USER=$GITHUB_USER" \
    --set-env-vars="ADMIN_PASSWORD_HASH=$ADMIN_PASSWORD_HASH" \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0

# Obter URL do serviço
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')

echo ""
echo "===================================="
echo "✅ Deploy concluído com sucesso!"
echo "===================================="
echo ""
echo "🌐 URL do serviço: $SERVICE_URL"
echo "👤 Usuário: admin"
echo "🔑 Senha: $ADMIN_PASSWORD"
echo ""
echo "📊 Acesse o dashboard em: $SERVICE_URL"
echo ""
