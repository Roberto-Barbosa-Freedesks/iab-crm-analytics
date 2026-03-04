# Guia de Setup — IAB Brasil CRM Analytics

## Passo 1: RD Station Marketing — Criar App OAuth2

### 1.1 Acesse o App Store do RD Station
1. Faça login no RD Station Marketing: https://app.rdstation.com.br/login
2. Clique no menu superior → **Perfil** → **Configurações**
3. Vá em **Integrações** → **App Store**
4. Clique em **"Criar aplicativo"** (ou "Minhas aplicações")

### 1.2 Configure o App
- **Nome:** IAB Analytics Integration
- **URL de Redirect:** `http://localhost:8080/callback`
- **Escopos necessários:** Todos (leitura de campanhas, emails, contatos)
- Salve e anote o **client_id** e **client_secret**

### 1.3 Autorize o App
Depois de ter o client_id e client_secret, execute:
```bash
python3 scripts/01_rdstation_auth.py
```
Isso abrirá o fluxo OAuth2 e salvará o access_token.

---

## Passo 2: GA4 — Criar Service Account no Google Cloud

### 2.1 Acesse o Google Cloud Console
1. Vá em: https://console.cloud.google.com/
2. Selecione o projeto **IAB-Data-Analytics**

### 2.2 Crie a Service Account
1. Menu lateral → **IAM e administrador** → **Contas de serviço**
2. Clique em **"+ Criar conta de serviço"**
3. Nome: `iab-analytics-sa`
4. Clique em **Continuar** → **Concluído**

### 2.3 Gere a chave JSON
1. Clique na conta de serviço criada
2. Aba **Chaves** → **Adicionar chave** → **Criar nova chave**
3. Selecione **JSON** → Baixe e salve como:
   `credentials/ga4-service-account.json`

### 2.4 Ative a GA4 Data API
1. Menu lateral → **APIs e serviços** → **Biblioteca**
2. Pesquise **"Google Analytics Data API"**
3. Clique em **Ativar**

### 2.5 Adicione a Service Account ao GA4
1. Acesse: https://analytics.google.com/
2. Selecione a propriedade do IAB Brasil
3. **Admin** → **Gerenciamento de acesso à propriedade**
4. Clique em **"+"** → **Adicionar usuários**
5. Digite o email da service account (formato: nome@projeto.iam.gserviceaccount.com)
6. Papel: **Leitor** → Adicionar

### 2.6 Anote o Property ID
1. No GA4: **Admin** → **Configurações da propriedade**
2. Copie o **Property ID** (número, ex: 123456789)
3. Salve em: `credentials/ga4_property_id.txt`

---

## Passo 3: GitHub Pages

O repositório já existe: https://github.com/Roberto-Barbosa-Freedesks/iab-crm-analytics

Configure GitHub Pages nas Settings do repositório para publicar a branch `gh-pages`.

---

## Passo 4: Configurar variáveis

Após obter as credenciais, edite o arquivo `credentials/config.json`:
```json
{
  "rdstation": {
    "client_id": "SEU_CLIENT_ID",
    "client_secret": "SEU_CLIENT_SECRET"
  },
  "ga4": {
    "property_id": "SEU_PROPERTY_ID",
    "service_account_file": "credentials/ga4-service-account.json"
  },
  "github": {
    "repo": "Roberto-Barbosa-Freedesks/iab-crm-analytics"
  }
}
```
