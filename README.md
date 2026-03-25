# 🧪 Sistema de Avaliação Docente — Engenharia Química (CEFET-MG)

## Como funciona o anonimato?

Este sistema pede matrícula e nome no login **apenas para dois fins**:
1. Confirmar que você é aluno da EQ
2. Listar as disciplinas que você cursou

**Na hora de gravar suas respostas, o sistema NÃO registra sua matrícula, nome ou qualquer dado que identifique quem respondeu.** As respostas são salvas com um código aleatório (`id_anonimo`) gerado por hash criptográfico.

O controle de "quem já avaliou qual disciplina" (para evitar duplicação) é feito em uma planilha **separada** que não contém respostas — apenas a informação de que determinada avaliação já foi realizada.

**Resultado:** o coordenador sabe que "alguém avaliou o professor X com nota Y", mas NÃO sabe quem foi.

---

## Como verificar por conta própria

Você pode fazer o deploy deste sistema com uma base de dados fictícia e comprovar pessoalmente que as respostas são anônimas.

### Passo 1: Criar conta no Streamlit Cloud (gratuito)

1. Acesse [share.streamlit.io](https://share.streamlit.io)
2. Faça login com sua conta GitHub

### Passo 2: Criar repositório no GitHub

1. Crie um novo repositório no GitHub (pode ser privado)
2. Faça upload de todos os arquivos desta pasta

### Passo 3: Criar planilha no Google Sheets

1. Crie uma planilha no Google Sheets
2. Renomeie a primeira aba para `BASE_DISCENTES`
3. Cole o conteúdo do arquivo `BASE_DISCENTES_BOGUS.csv` (os dados são fictícios)
4. Crie uma segunda aba chamada `Respostas` (vazia, com cabeçalho se desejar)
5. Anote o ID da planilha (está na URL entre `/d/` e `/edit`)

### Passo 4: Criar credenciais do Google (Service Account)

1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
2. Crie um projeto novo
3. Ative a API do Google Sheets e Google Drive
4. Em "Credenciais", crie uma Service Account
5. Gere uma chave JSON para essa conta
6. Compartilhe a planilha do Passo 3 com o e-mail da Service Account

### Passo 5: Configurar secrets no Streamlit Cloud

1. No Streamlit Cloud, vá em Settings > Secrets
2. Cole o conteúdo do seu JSON de credenciais no formato TOML (veja `secrets_TEMPLATE.toml`)

### Passo 6: Atualizar o SPREADSHEET_ID

1. No arquivo `app.py`, altere a linha:
   ```python
   SPREADSHEET_ID = "SEU_ID_DA_PLANILHA_AQUI"
   ```

### Passo 7: Deploy

1. No Streamlit Cloud, aponte para o repositório do Passo 2
2. O app vai subir automaticamente

### Passo 8: Testar

1. Faça login com uma matrícula da base bogus (ex: `2027MEC9997`, nome: `ANITTA`)
2. Preencha uma avaliação qualquer
3. Vá até a planilha Google Sheets e verifique:
   - Na aba `Respostas`: suas notas estão lá, mas **sem matrícula e sem nome**
   - Na aba `Controle_Anonimato`: apenas registra que uma avaliação de certa disciplina foi feita
   - **Não há como cruzar quem respondeu o quê**

---

## Estrutura dos arquivos

```
app.py                    → Aplicação principal (Streamlit)
config.py                 → Pesos, cruzamentos, configurações
avaliacao_docente_v4.py   → Motor de cálculo de notas
util.py                   → Funções auxiliares
perguntas.json            → Questionário (44 perguntas, 9 dimensões)
requirements.txt          → Dependências Python
BASE_DISCENTES_BOGUS.csv  → Base de dados fictícia para teste
secrets_TEMPLATE.toml     → Template de credenciais (preencher com as suas)
```

## Base de dados fictícia

A base `BASE_DISCENTES_BOGUS.csv` contém dados 100% inventados:
- **Alunos:** nomes de músicos brasileiros famosos
- **Professores:** nomes de atores de Hollywood
- **Matrículas, CPFs, RGs:** completamente fictícios
- **E-mails:** domínios de vilões do Superman

Nenhum dado real de qualquer pessoa está presente nesta base.

---

**Coordenação de Engenharia Química — CEFET-MG Campus Contagem**
