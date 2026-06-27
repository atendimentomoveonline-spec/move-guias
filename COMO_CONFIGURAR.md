# Como colocar o sistema no ar

## PASSO 1 — Google Cloud (10 min)

1. Acesse: https://console.cloud.google.com
2. Clique em "Selecionar projeto" → "Novo projeto"
   - Nome: Move Online Guias
   - Clique "Criar"

3. No menu lateral → "APIs e Serviços" → "Biblioteca"
   - Busque: "Google Drive API"
   - Clique "Ativar"

4. Vá em "APIs e Serviços" → "Credenciais"
   - Clique "+ Criar Credenciais" → "Conta de serviço"
   - Nome: move-guias
   - Clique "Concluído"

5. Clique na conta de serviço criada → aba "Chaves"
   - "Adicionar chave" → "Criar nova chave" → JSON
   - Vai baixar um arquivo .json — GUARDE ESSE ARQUIVO

---

## PASSO 2 — Google Drive (5 min)

1. Acesse seu Google Drive
2. Crie uma pasta chamada: "Guias INSS Move Online"
3. Dentro dela, crie subpastas com o CNPJ de cada cliente:
   ```
   📁 Guias INSS Move Online/
      📁 53578465000190/
         📄 GuiaPagamento_Abr2026.pdf
      📁 12345678000195/
         📄 GuiaPagamento_Abr2026.pdf
   ```
4. Clique com botão direito na pasta "Guias INSS Move Online"
   → Compartilhar
   → Cole o e-mail que está no arquivo .json
     (campo "client_email", ex: move-guias@move-online.iam.gserviceaccount.com)
   → Permissão: "Leitor"
   → Clique Compartilhar

5. Abra a pasta no Drive e copie o ID da URL:
   https://drive.google.com/drive/folders/ESTE_TRECHO_É_O_ID
   Guarde esse ID.

---

## PASSO 3 — GitHub (5 min)

1. Crie conta em: https://github.com
2. Clique "New repository"
   - Nome: move-guias-inss
   - Público
   - Clique "Create repository"
3. Copie a pasta C:\Move\AppOnline para dentro do repositório
   (pode arrastar os arquivos no próprio site do GitHub)

---

## PASSO 4 — Railway (5 min)

1. Acesse: https://railway.app
2. Faça login com o GitHub
3. Clique "New Project" → "Deploy from GitHub repo"
4. Selecione: move-guias-inss
5. Clique no projeto → aba "Variables" → adicione:

   | Nome                | Valor                              |
   |---------------------|------------------------------------|
   | DRIVE_FOLDER_ID     | (ID da pasta do Drive - passo 2.5) |
   | GOOGLE_CREDENTIALS  | (conteúdo inteiro do arquivo .json) |
   | PORT                | 5000                               |

6. Vá em "Settings" → "Domains" → "Generate Domain"
   Vai gerar: https://move-guias-inss.up.railway.app

---

## PASSO 5 — Testar

Acesse: https://move-guias-inss.up.railway.app/minhas-guias
Digite um CNPJ que tem arquivo no Drive.
Se aparecer a guia → tudo certo!

---

## Operação diária (depois de configurado)

1. Baixe o ZIP da Receita Federal
2. Extraia o PDF
3. Jogue o PDF na pasta do cliente no Google Drive
4. Pronto! Cliente já consegue baixar em segundos.

Link para enviar no WhatsApp:
https://move-guias-inss.up.railway.app/minhas-guias
