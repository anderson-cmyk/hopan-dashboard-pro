# ⚡ Guia Rápido de Início - HO Pan Dashboard

Este é um guia resumido para você começar rapidamente. Para detalhes completos, consulte o [README.md](README.md).

---

## 🎯 Objetivo

Implantar o HO Pan Dashboard no Google Cloud Run com autenticação segura e integração GitHub.

---

## 📋 Checklist Rápido

### 1️⃣ Pré-requisitos

- [ ] Conta no Google Cloud Platform
- [ ] Conta no GitHub
- [ ] gcloud CLI instalado
- [ ] Docker instalado (opcional)

### 2️⃣ Configuração do GCP

Execute o script de setup:

```bash
cd hopan-dashboard-pro
chmod +x ./config/setup-gcp.sh
./config/setup-gcp.sh
```

**O que o script faz:**
- Habilita APIs necessárias no GCP
- Cria Service Account com permissões corretas
- Gera credenciais e senhas
- Cria arquivos de configuração

**Arquivos gerados:**
- `service-account-key.json` (não commitar!)
- `.env.production` (variáveis de ambiente)
- `github-secrets.txt` (secrets para GitHub)
- `PROXIMOS_PASSOS.txt` (instruções detalhadas)

### 3️⃣ Configurar GitHub

1. Crie um repositório no GitHub para o projeto
2. Vá em **Settings > Secrets and variables > Actions**
3. Adicione cada secret do arquivo `github-secrets.txt`:
   - `GCP_PROJECT_ID`
   - `GCP_SA_KEY`
   - `SECRET_KEY`
   - `ADMIN_PASSWORD_HASH`
   - `GITHUB_TOKEN`
   - `GITHUB_REPO`
   - `GITHUB_USER`

### 4️⃣ Fazer Deploy

**Opção A - Automático (Recomendado):**

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/seu-usuario/seu-repositorio.git
git push -u origin main
```

O GitHub Actions fará o deploy automaticamente!

**Opção B - Manual:**

```bash
chmod +x ./config/deploy-manual.sh
./config/deploy-manual.sh
```

### 5️⃣ Acessar o Dashboard

Após o deploy, você receberá uma URL como:

```
https://hopan-dashboard-xxxxxxxxxx-uc.a.run.app
```

**Credenciais de acesso:**
- Usuário: `admin`
- Senha: (verifique no arquivo `.env.production`)

---

## 🔐 Segurança

- ✅ Autenticação obrigatória para todos os usuários
- ✅ Senhas com hash seguro (Werkzeug)
- ✅ Sessões criptografadas
- ✅ HTTPS automático (Cloud Run)
- ✅ Variáveis sensíveis em secrets

---

## 📊 Funcionalidades

- ✅ Login seguro com branding CobHub
- ✅ Dashboard interativo com análises
- ✅ Filtros master (Mês, Origem, Canal)
- ✅ Exportação de dados em CSV
- ✅ Atualização automática via GitHub
- ✅ Escalabilidade automática

---

## 🔄 Atualizações

Para atualizar o dashboard:

1. Faça alterações no código
2. Commit e push para o repositório
3. GitHub Actions faz deploy automaticamente

```bash
git add .
git commit -m "Descrição da atualização"
git push
```

---

## 👥 Adicionar Usuários

1. Gere o hash da senha:

```bash
python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('senha123'))"
```

2. Edite o secret `ADDITIONAL_USERS` no GitHub:

```json
{
  "usuario1": {
    "password": "hash_gerado",
    "name": "Nome do Usuário",
    "role": "user"
  }
}
```

3. Re-execute o workflow no GitHub Actions

---

## 🆘 Problemas Comuns

### Deploy falhou

- Verifique se todos os secrets estão configurados no GitHub
- Confirme que as APIs estão habilitadas no GCP
- Veja os logs no GitHub Actions para detalhes

### Não consigo fazer login

- Verifique a senha no arquivo `.env.production`
- Confirme que o secret `ADMIN_PASSWORD_HASH` está correto no GitHub

### Dados não aparecem

- Verifique se o arquivo `dashboard_data.json` existe no repositório GitHub
- Confirme que o `GITHUB_TOKEN` tem permissões de leitura

---

## 📚 Documentação Completa

Para informações detalhadas sobre arquitetura, segurança e customização, consulte:

- [README.md](README.md) - Guia completo de implantação
- [PROXIMOS_PASSOS.txt](PROXIMOS_PASSOS.txt) - Próximos passos após setup

---

## 🎉 Pronto!

Seu dashboard está no ar! Acesse a URL fornecida e comece a usar.

**Dúvidas?** Consulte a documentação completa ou entre em contato com a equipe de desenvolvimento.
