# Guia de Configuração — Move Online Guias INSS

## Você vai precisar de 2 coisas:
- Chave API do Google  (você disse que consegue gerar)
- ID da pasta no Drive (está na URL da pasta)

---

## PASSO 1 — Criar pasta no Google Drive (2 min)

1. Abra o Google Drive
2. Crie uma pasta chamada: Guias INSS
3. Clique com botão direito na pasta → Compartilhar
4. Altere para: "Qualquer pessoa com o link" → Leitor
5. Copie o ID da URL:
   https://drive.google.com/drive/folders/>>ESTE_TRECHO<<
   Guarde esse ID.

---

## PASSO 2 — Gerar Chave API do Google (5 min)

1. Acesse: https://console.cloud.google.com
2. Crie um projeto chamado: Move Online
3. Menu lateral → APIs e Serviços → Biblioteca
   → Busque "Google Drive API" → Ativar
4. Menu lateral → APIs e Serviços → Credenciais
   → + Criar Credenciais → Chave de API
   → Copie a chave gerada (começa com AIza...)

---

## PASSO 3 — GitHub + Railway (10 min)

1. Crie conta em: https://github.com
2. New repository → nome: move-guias → Criar
3. Arraste os arquivos de C:\Move\AppOnline para o repositório

4. Crie conta em: https://railway.app (login com GitHub)
5. New Project → Deploy from GitHub → selecione move-guias
6. Clique em Variables e adicione:

   GOOGLE_API_KEY  = AIza... (chave do passo 2)
   DRIVE_FOLDER_ID = (ID do passo 1)
   PORT            = 5000

7. Settings → Domains → Generate Domain
   Link final: https://move-guias.up.railway.app/minhas-guias

---

## Uso diário (só isso!)

1. Baixe o ZIP da Receita Federal
2. Jogue direto na pasta "Guias INSS" do Drive
   (o nome já tem o CNPJ, não precisa renomear)
3. Envie o link no WhatsApp:

   "Sua guia INSS está disponível!
    Acesse: https://move-guias.up.railway.app/minhas-guias
    Digite seu CNPJ para baixar."

Pronto! O sistema faz todo o resto.
