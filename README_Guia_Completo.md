# Sistema de Avaliação Docente — Engenharia Química (CEFET-MG)

## Guia Completo de Instalação e Verificação de Anonimato

Este guia ensina, passo a passo, como instalar uma cópia do sistema no seu computador para verificar pessoalmente que as respostas são anônimas. Não é necessário experiência prévia com programação.

**Tempo estimado:** 30 a 45 minutos (primeira vez). Depois de configurado, funciona automaticamente.

**O que você vai precisar:**
- Um computador com acesso à internet
- Uma conta Google (Gmail)
- Uma conta no GitHub (gratuita)

---

## ETAPA 1: Criar conta no GitHub (se ainda não tiver)

O GitHub é uma plataforma onde programadores guardam código. Vamos usá-lo para armazenar os arquivos do sistema.

1. Acesse **https://github.com** no navegador
2. Clique no botão verde **"Sign up"** (canto superior direito)
3. Preencha: e-mail, senha, nome de usuário (pode ser qualquer um)
4. Confirme o e-mail (GitHub envia um código para o e-mail cadastrado)
5. Pronto. Você tem uma conta no GitHub.

---

## ETAPA 2: Criar um repositório no GitHub

Um "repositório" é uma pasta no GitHub onde os arquivos ficam armazenados.

1. Após o login no GitHub, clique no ícone **"+"** no canto superior direito da tela
2. No menu que aparece, clique em **"New repository"**
3. Na tela de criação:
   - **Repository name:** digite `avaliacao-docente-teste` (ou o nome que preferir)
   - **Description:** (opcional) digite "Teste de anonimato do sistema de avaliação"
   - Marque **"Private"** (para manter o repositório visível apenas para você)
   - Marque a caixa **"Add a README file"**
   - Clique no botão verde **"Create repository"**
4. Você será levado para a página do repositório recém-criado.

---

## ETAPA 3: Fazer upload dos arquivos do sistema

Agora vamos colocar os arquivos do sistema dentro do repositório.

1. Na página do repositório, clique no botão **"Add file"** (fica acima da lista de arquivos, ao lado do botão verde "Code")
2. No menu que aparece, clique em **"Upload files"**
3. Uma tela de upload aparece. Você pode:
   - **Arrastar** os arquivos do seu computador para a área indicada, **OU**
   - Clicar em **"choose your files"** e selecionar os arquivos na janela do explorador
4. Selecione **TODOS** os seguintes arquivos (que vieram no pacote ZIP):
   - `app.py`
   - `config.py`
   - `avaliacao_docente_v4.py`
   - `util.py`
   - `perguntas.json`
   - `requirements.txt`
   - `BASE_DISCENTES_BOGUS.csv`
   
   **NÃO envie** o `secrets_TEMPLATE.toml` nem o `gerar_base_bogus.py` (não são necessários)

5. Aguarde o upload terminar (uma barra de progresso aparece para cada arquivo)
6. Na parte de baixo da página, no campo **"Commit changes"**, pode deixar o texto padrão
7. Clique no botão verde **"Commit changes"**
8. Pronto. Os arquivos estão no GitHub.

**Como verificar:** na página do repositório, você deve ver a lista de arquivos: app.py, config.py, etc.

---

## ETAPA 4: Criar uma planilha no Google Planilhas

Esta planilha fará o papel do "banco de dados" do sistema.

### 4.1 Criar a planilha

1. Acesse **https://sheets.google.com** (faça login com sua conta Google se necessário)
2. Clique em **"Em branco"** (ou no ícone **"+"**) para criar uma nova planilha
3. No canto superior esquerdo, clique no nome "Planilha sem título" e renomeie para **"Avaliacao Docente Teste"**

### 4.2 Configurar a aba BASE_DISCENTES

1. Na parte inferior da tela, você verá uma aba chamada "Plan1". Clique com o botão direito sobre ela
2. Selecione **"Renomear"** e digite: **BASE_DISCENTES**
3. Importe o arquivo CSV com os dados fictícios:
   - Clique em **Arquivo** → **Importar**
   - Clique na aba **"Upload"** → **"Procurar"** e selecione o arquivo `BASE_DISCENTES_BOGUS.csv`
   - Em "Local da importação", selecione: **"Substituir planilha atual"**
   - Em "Tipo de separador", selecione: **"Vírgula"**
   - Clique em **"Importar dados"**
4. Verifique: a planilha deve ter cabeçalhos na primeira linha (Matrícula, Discente, Entrada...) e aproximadamente 230 linhas de dados

### 4.3 Criar a aba Respostas

1. Na parte inferior da tela, clique no ícone **"+"** (ao lado da aba BASE_DISCENTES) para criar nova aba
2. Clique com botão direito na nova aba → **"Renomear"** → digite: **Respostas**
3. Deixe esta aba **vazia** (o sistema vai preenchê-la automaticamente)

### 4.4 Anotar o ID da planilha

1. Olhe para a barra de endereço do navegador. A URL será algo como:
   ```
   https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/edit
   ```
2. O ID da planilha é o texto longo entre `/d/` e `/edit`. No exemplo acima:
   ```
   1AbCdEfGhIjKlMnOpQrStUvWxYz
   ```
3. **Copie este ID** e guarde (você vai precisar na Etapa 6)

---

## ETAPA 5: Criar credenciais do Google (Conta de Serviço)

Esta é a etapa mais técnica. É o que permite que o sistema acesse a planilha automaticamente.

### 5.1 Acessar o Console do Google Cloud

1. Acesse **https://console.cloud.google.com** no navegador
2. Faça login com a mesma conta Google usada na planilha
3. Se aparecer uma tela de "Termos de Serviço", aceite e continue

### 5.2 Criar um projeto

1. No topo da tela, ao lado do logo "Google Cloud", há um seletor de projeto. Clique nele
2. Na janela que abre, clique em **"NOVO PROJETO"** (canto superior direito)
3. Em "Nome do projeto", digite: **avaliacao-teste**
4. Clique em **"CRIAR"**
5. Aguarde a criação. Depois, selecione o projeto criado no seletor

### 5.3 Ativar as APIs necessárias

O sistema precisa de duas APIs (serviços) do Google: Google Sheets e Google Drive.

**Ativar Google Sheets API:**
1. No menu lateral esquerdo, clique em **"APIs e serviços"** → **"Biblioteca"**
   (Se o menu não estiver visível, clique no ícone de 3 linhas horizontais no canto superior esquerdo)
2. Na barra de busca, digite: **Google Sheets API**
3. Clique no resultado **"Google Sheets API"**
4. Clique no botão azul **"ATIVAR"**

**Ativar Google Drive API:**
1. Volte para a Biblioteca: **"APIs e serviços"** → **"Biblioteca"**
2. Na barra de busca, digite: **Google Drive API**
3. Clique no resultado **"Google Drive API"**
4. Clique no botão azul **"ATIVAR"**

### 5.4 Criar uma Conta de Serviço

1. No menu lateral, clique em **"APIs e serviços"** → **"Credenciais"**
2. Clique em **"+ CRIAR CREDENCIAIS"** → **"Conta de serviço"**
3. Preencha:
   - **Nome:** `avaliacao-sistema`
   - **Descrição:** `Acesso do sistema à planilha` (opcional)
4. Clique em **"CRIAR E CONTINUAR"**
5. Nas etapas seguintes, pode clicar em **"CONTINUAR"** e **"CONCLUÍDO"**

### 5.5 Gerar a chave JSON

1. Na lista de Contas de Serviço, clique no e-mail da conta criada
2. Clique na aba **"CHAVES"**
3. Clique em **"ADICIONAR CHAVE"** → **"Criar nova chave"**
4. Selecione **"JSON"** → Clique em **"CRIAR"**
5. Um arquivo `.json` será baixado. **Guarde este arquivo com cuidado.**
6. **Anote o e-mail da Conta de Serviço** (formato: `nome@projeto.iam.gserviceaccount.com`)

### 5.6 Compartilhar a planilha com a Conta de Serviço

1. Volte para a planilha Google Planilhas
2. Clique em **"Compartilhar"** (botão verde, canto superior direito)
3. Cole o **e-mail da Conta de Serviço** no campo de compartilhamento
4. Permissão: **"Editor"**
5. Desmarque "Notificar pessoas" → Clique em **"Compartilhar"**

---

## ETAPA 6: Configurar e publicar no Streamlit Cloud

### 6.1 Criar conta no Streamlit Cloud

1. Acesse **https://share.streamlit.io**
2. Clique em **"Continue with GitHub"** e autorize o acesso

### 6.2 Atualizar o ID da planilha no código

1. No GitHub, vá até o repositório e clique no arquivo **`app.py`**
2. Clique no ícone de **lápis** (editar)
3. Procure a linha (perto da linha 42):
   ```
   SPREADSHEET_ID = "SEU_ID_DA_PLANILHA_AQUI"
   ```
4. Substitua pelo ID que você anotou na Etapa 4.4
5. Clique em **"Commit changes"**

### 6.3 Criar o aplicativo no Streamlit

1. No Streamlit Cloud, clique em **"New app"**
2. Selecione o repositório `avaliacao-docente-teste`, branch `main`, arquivo `app.py`
3. Clique em **"Advanced settings"**
4. No campo **"Secrets"**, cole o conteúdo no formato abaixo, substituindo pelos valores do seu JSON:

```toml
[gcp_service_account]
type = "service_account"
project_id = "VALOR_DO_SEU_JSON"
private_key_id = "VALOR_DO_SEU_JSON"
private_key = """CHAVE_PRIVADA_INTEIRA_DO_SEU_JSON"""
client_email = "VALOR_DO_SEU_JSON"
client_id = "VALOR_DO_SEU_JSON"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "VALOR_DO_SEU_JSON"
universe_domain = "googleapis.com"
```

5. Clique em **"Save"** e depois **"Deploy!"**
6. Aguarde 2 a 5 minutos

---

## ETAPA 7: Testar e verificar o anonimato

### 7.1 Fazer login com dados fictícios

No aplicativo, digite:
- **Matrícula:** `2027MEC9997`
- **Primeiro Nome:** `ANITTA`

Preencha qualquer avaliação e clique em "Enviar".

### 7.2 Verificar a planilha

Abra a planilha e confira:

**Aba "Respostas":**
- Coluna A: data/hora
- Coluna B: código aleatório de 12 caracteres (exemplo: A3F7B2E9C1D4)
- Coluna C: professor
- Coluna D: disciplina
- Colunas seguintes: notas
- **NENHUMA coluna contém a matrícula 2027MEC9997 ou o nome ANITTA**

**Aba "Controle_Anonimato":**
- Coluna A: data/hora
- Coluna B: chave de controle (contém matrícula, para evitar duplicação)
- **NÃO há notas ou respostas nesta aba**

**Conclusão:** notas em um lugar (sem saber quem), controle em outro lugar (sem saber o quê). Impossível cruzar.

---

## Problemas comuns

| Problema | Solução |
|----------|---------|
| "Matrícula não encontrada" | CSV não foi importado corretamente. A primeira coluna deve ser "Matrícula" |
| Erro de conexão | Verifique: APIs ativadas? Planilha compartilhada com a Conta de Serviço? Secrets corretos? |
| App não inicia | Arquivo deve se chamar `app.py` (minúsculo). `requirements.txt` deve estar no repositório |

---

## Sobre a base de dados fictícia

Todos os dados são inventados:
- **Alunos:** músicos brasileiros (Anitta, Ludmilla, IZA, etc.)
- **Professores:** atores de Hollywood (Tom Hanks, Meryl Streep, etc.)
- **CPFs/RGs:** letras aleatórias
- **Telefones:** formato Hollywood (55) 5555-XXXX
- **E-mails:** vilões do Superman (lexluthor.com, brainiac.net, etc.)

**Coordenação de Engenharia Química — CEFET-MG Campus Contagem**
