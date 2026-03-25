# ==============================================================================
# SISTEMA DE AVALIAÇÃO DOCENTE - ENGENHARIA QUÍMICA (CEFET-MG)
# VERSÃO v1.1.0: Respostas anonimizadas + controle de duplicação separado
# ==============================================================================
#
# ARQUITETURA DE ANONIMATO
# ========================
#
# O sistema utiliza DUAS planilhas separadas no Google Sheets:
#
#   1. "Respostas" (MAIN_SHEET_RESP)
#      → Armazena: data/hora, id_anonimo, professor, disciplina, p1..p41,
#        respostas abertas, pontuação.
#      → NÃO contém: matrícula, nome do aluno, ou qualquer dado identificador.
#      → O campo id_anonimo é um hash SHA-256 aleatório de 12 caracteres,
#        gerado com timestamp + entropia criptográfica (os.urandom).
#        Não é derivado da matrícula e não pode ser revertido.
#      → Esta planilha é usada para análise de resultados.
#
#   2. "Controle_Anonimato" (CONTROL_SHEET)
#      → Armazena APENAS: data/hora e chave de controle.
#      → A chave de controle identifica QUAL avaliação foi feita (disciplina +
#        professor + aluno), para evitar duplicação.
#      → Esta planilha NÃO contém respostas nem notas.
#      → Não existe cruzamento possível entre as duas planilhas.
#
# FLUXO DE DADOS
# ==============
#
#   LOGIN (Tela 1):
#   → Aluno informa matrícula + primeiro nome
#   → Sistema busca na BASE_DISCENTES e valida
#   → Matrícula fica apenas na session_state (memória temporária)
#   → Nada é gravado em disco nesta etapa
#
#   ATUALIZAÇÃO DE CONTATOS (Tela 2):
#   → Aluno confirma e-mail e celular
#   → Dados atualizados na session_state
#   → Nada é gravado em disco nesta etapa
#
#   SELEÇÃO (Tela 3):
#   → Sistema lê Controle_Anonimato para saber quais já foram feitas
#   → Compara com disciplinas do aluno para mostrar pendentes
#   → Nenhum dado pessoal é transmitido nesta etapa
#
#   QUESTIONÁRIO (Tela 4):
#   → Aluno preenche 44 perguntas (41 obrigatórias + 3 abertas)
#   → Ao clicar "Enviar":
#        a) Gera id_anonimo aleatório (hash SHA-256, sem vínculo com matrícula)
#        b) Grava na "Respostas": [data, id_anonimo, professor, disciplina, notas]
#        c) Grava na "Controle_Anonimato": [data, chave_controle]
#   → A matrícula NÃO aparece em nenhum registro gravado
#
#   RESULTADO:
#   → O coordenador vê "alguém avaliou professor X com notas Y"
#   → O coordenador NÃO vê "aluno Z avaliou professor X com notas Y"
#
# ==============================================================================

import streamlit as st
import pandas as pd
import json
import gspread
import os
import re
import logging
import time
import pathlib
import csv
from google.oauth2.service_account import Credentials
from datetime import datetime
import unicodedata

# ------------------------------------------------------------------------------
# CONFIGURAÇÃO
# ------------------------------------------------------------------------------

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Avaliação Eng. Química CEFET-MG",
    page_icon="🧪",
    layout="centered"
)

# ------------------------------------------------------------------------------
# CONSTANTES E PATHS
# Definem os nomes das planilhas no Google Sheets e caminhos locais.
# A separação entre MAIN_SHEET_RESP e CONTROL_SHEET é o que garante o anonimato:
# as respostas ficam em uma planilha, o controle de duplicação em outra.
# ------------------------------------------------------------------------------
LOG_LOCAL = pathlib.Path.cwd() / "click_log.csv"
CREDENTIALS_FILE = "credentials.json"
SPREADSHEET_ID = "1Y6JbcvUcHAxKL8WTjQUF3aXPaNwqmoLbW1Ip8xOA5lk"

# Planilha com dados cadastrais dos alunos (matrícula, disciplinas, etc.)
# Usada APENAS para autenticação e listagem de disciplinas no login.
MAIN_SHEET_BASE = "BASE_DISCENTES"

# Planilha onde as RESPOSTAS são gravadas — SEM dados identificadores do aluno.
# Colunas: data_hora | id_anonimo | professor | disciplina | p1...p41 | abertas | pontuação
MAIN_SHEET_RESP = "Respostas"

# Planilha de CONTROLE DE DUPLICAÇÃO — registra apenas QUAIS avaliações foram feitas.
# Colunas: data_hora | chave_controle
# NÃO contém respostas, notas ou textos abertos.
CONTROL_SHEET = "Controle_Anonimato"

BACKUP_SHEET = "Respostas_backup"
LOCAL_FALLBACK_RESP = "Respostas_local.csv"   # Fallback quando offline
PENDING_DIR = pathlib.Path.cwd() / "pending"

MAPA_NOTAS = {
    "😡": 1, "🙁": 2, "😐": 3, "🙂": 4, "🤩": 5,
    "🤬": 1, "Sim": 5, "Não": 1, "Não sei": 3
}

# ------------------------------------------------------------------------------
# ESTILO VISUAL (COMPLETO E DETALHADO)
# ------------------------------------------------------------------------------
def aplicar_estilo_visual():
    """CSS completo com todos os ajustes estéticos"""
    st.markdown("""
        <style>
        /* --- INPUT LABELS --- */
        div[data-testid="stTextInput"] label p {
            font-size: 1.5rem !important;
            font-weight: 900 !important;
            text-transform: uppercase !important;
            color: #1f77b4 !important;
        }
        
        div[data-testid="stTextInput"] input {
            font-size: 1.2rem !important;
            font-weight: bold !important;
        }
        
        /* --- TELA 1: TÍTULO PRINCIPAL - CENTRALIZADO --- */
        .titulo-principal {
            text-align: center !important;
            font-size: 2.5rem !important;
            font-weight: 900 !important;
            color: #1f77b4 !important;
            margin-bottom: 0.5rem !important;
        }
        
        /* --- TELA 1: SUBTÍTULO CAMPUS - CENTRALIZADO --- */
        .campus-subtitulo {
            text-align: center !important;
            font-size: 1.6rem !important;
            font-weight: 700 !important;
            color: #333 !important;
            margin-top: 0.15rem !important;
            margin-bottom: 1.5rem !important;
        }
        
        /* --- TELA 2: LABEL SIGAA MAIOR --- */
        .label-sigaa {
            font-size: 1.8rem !important;
            font-weight: bold !important;
            font-style: italic !important;
            color: #31333F !important;
            margin-bottom: 1rem !important;
        }

        /* --- TELA 2: MOLDURA DE DADOS MAIOR --- */
        .moldura-dados {
            background-color: #f0f2f6 !important;
            border: 2px solid #1f77b4 !important;
            border-radius: 15px !important;
            padding: 20px !important;
            text-align: center !important;
            font-size: 1.8rem !important;
            font-weight: bold !important;
            font-style: italic !important;
            color: #1f77b4 !important;
            margin-bottom: 1.5rem !important;
        }
        
        /* --- TELA 2: PERGUNTAS DE VALIDAÇÃO MAIORES --- */
        .pergunta-validacao {
            font-size: 1.4rem !important;
            font-weight: 700 !important;
            color: #333 !important;
            margin-top: 0.5rem !important;
            margin-bottom: 0.8rem !important;
        }
        
        /* --- TELA 2: BOTÕES SIM/NÃO MAIORES (FORÇADO) --- */
        div[data-testid="stRadio"] div[role="radiogroup"] label {
            font-size: 1.3rem !important;
            font-weight: 600 !important;
        }
        
        div[data-testid="stRadio"] div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] p {
            font-size: 1.3rem !important;
            font-weight: 600 !important;
        }
        
        div[data-testid="stRadio"] div[role="radiogroup"] label span {
            font-size: 1.3rem !important;
            font-weight: 600 !important;
        }
        
        /* --- TELA 2: ESPAÇAMENTO APÓS MOLDURA --- */
        .espaco-depois-moldura {
            margin-top: 1.5rem !important;
        }

        /* --- TELA 3: SELECTBOX LABEL MAIOR (FORÇADO) --- */
        div[data-testid="stSelectbox"] label p {
            font-size: 1.6rem !important;
            font-weight: 700 !important;
            color: #333 !important;
        }
        
        div[data-testid="stSelectbox"] label div[data-testid="stMarkdownContainer"] p {
            font-size: 1.6rem !important;
            font-weight: 700 !important;
            color: #333 !important;
        }
        
        div[data-testid="stSelectbox"] label span {
            font-size: 1.6rem !important;
            font-weight: 700 !important;
        }
        
        /* --- TELA 3: SUBTÍTULO "AVALIAÇÕES PENDENTES" --- */
        .subtitulo-pendentes {
            font-size: 1.6rem !important;
            font-weight: 800 !important;
            color: #1f77b4 !important;
            margin-bottom: 1rem !important;
        }
        
        /* --- TELA 3: MÉTRICAS MAIORES E CENTRALIZADAS --- */
        div[data-testid="stMetric"] {
            background-color: #f8f9fa !important;
            padding: 1rem !important;
            border-radius: 10px !important;
            text-align: center !important;
        }
        
        div[data-testid="stMetric"] label {
            font-size: 1.4rem !important;
            font-weight: 700 !important;
            color: #1f77b4 !important;
            text-align: center !important;
            justify-content: center !important;
        }
        
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            font-size: 2.5rem !important;
            font-weight: 900 !important;
            text-align: center !important;
            justify-content: center !important;
        }

        /* --- TELA 4: INFO BOX CUSTOMIZADO --- */
        .info-avaliacao {
            text-align: center !important;
            font-size: 1.2rem !important;
            padding: 1rem !important;
            background-color: #e3f2fd !important;
            border-radius: 10px !important;
            margin-bottom: 1.5rem !important;
        }
        
        .info-professor {
            font-size: 1.3rem !important;
            font-weight: bold !important;
            color: #1976d2 !important;
            margin-bottom: 0.5rem !important;
        }
        
        .info-disciplina {
            font-size: 1.3rem !important;
            font-weight: bold !important;
            color: #1976d2 !important;
        }

        /* --- TELA 4: EXPANDERS (TÍTULOS DAS SEÇÕES) --- */
        .stExpander summary p { 
            font-size: 1.8rem !important; 
            font-weight: 900 !important;
            font-style: italic !important;
            color: #1f77b4 !important;
        }
        
        /* --- TELA 4: PERGUNTAS JUSTIFICADAS --- */
        .pergunta-texto { 
            font-size: 1.1rem !important; 
            font-weight: bold !important; 
            color: black !important;
            text-align: justify !important;
            line-height: 1.6 !important;
        }

        /* --- TELA 4: BOTÕES DE RÁDIO CENTRALIZADOS --- */
        div[role="radiogroup"] {
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            gap: 20px !important;
            width: 100% !important;
            margin-top: 0.5rem !important;
        }
        
        div[role="radiogroup"] > label {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            text-align: center !important;
            margin: 0 !important;
            padding: 8px !important;
        }
        
        /* Número abaixo do botão de rádio - 50% MAIOR */
        div[role="radiogroup"] > label > div:last-child {
            order: 2 !important;
            margin-top: 5px !important;
            font-size: 1.5rem !important;
            font-weight: bold !important;
        }

        /* --- TELA 5: MENSAGEM DE SUCESSO CENTRALIZADA E MAIOR --- */
        .mensagem-sucesso {
            text-align: center !important;
            font-size: 1.3rem !important;
            font-weight: 600 !important;
            color: #2e7d32 !important;
            margin: 1.5rem 0 !important;
            line-height: 1.8 !important;
        }

        /* --- BOTÕES GERAIS (ALTURA CORRIGIDA + TEXTO FORÇADO) --- */
        div.stButton > button { 
            height: 3.2em !important;
            font-size: 1.8rem !important;
            font-weight: 900 !important;
            text-transform: uppercase !important;
            border-radius: 12px !important;
            border: 2px solid black !important;
        }
        
        div.stButton > button p,
        div.stButton > button span,
        div.stButton > button div {
            font-size: 1.8rem !important;
            font-weight: 900 !important;
        }
        
        /* --- BOTÃO VERDE (PRIMARY) --- */
        div.stButton > button[kind="primary"] { 
            background-color: #00B050 !important; 
            color: white !important;
            font-size: 1.9rem !important;
            font-weight: 900 !important;
        }
        
        div.stButton > button[kind="primary"] p,
        div.stButton > button[kind="primary"] span,
        div.stButton > button[kind="primary"] div {
            font-size: 1.9rem !important;
            font-weight: 900 !important;
        }
        
        /* --- BOTÃO VERMELHO (SECONDARY) --- */
        div.stButton > button[kind="secondary"] { 
            background-color: #FF3300 !important; 
            color: white !important;
            font-size: 1.8rem !important;
            font-weight: 900 !important;
        }
        
        div.stButton > button[kind="secondary"] p,
        div.stButton > button[kind="secondary"] span,
        div.stButton > button[kind="secondary"] div {
            font-size: 1.8rem !important;
            font-weight: 900 !important;
        }
        
        /* --- FORM SUBMIT BUTTONS (FORÇADO) --- */
        button[kind="formSubmit"] {
            font-size: 1.8rem !important;
            font-weight: 900 !important;
            height: 3.2em !important;
        }
        
        button[kind="formSubmit"] p,
        button[kind="formSubmit"] span,
        button[kind="formSubmit"] div {
            font-size: 1.8rem !important;
            font-weight: 900 !important;
        }
        
        button[kind="primaryFormSubmit"] {
            font-size: 1.9rem !important;
            font-weight: 900 !important;
            background-color: #00B050 !important;
            color: white !important;
        }
        
        button[kind="primaryFormSubmit"] p,
        button[kind="primaryFormSubmit"] span,
        button[kind="primaryFormSubmit"] div {
            font-size: 1.9rem !important;
            font-weight: 900 !important;
        }
        
        button[kind="secondaryFormSubmit"] {
            font-size: 1.8rem !important;
            font-weight: 900 !important;
            background-color: #FF3300 !important;
            color: white !important;
        }
        
        button[kind="secondaryFormSubmit"] p,
        button[kind="secondaryFormSubmit"] span,
        button[kind="secondaryFormSubmit"] div {
            font-size: 1.8rem !important;
            font-weight: 900 !important;
        }

        /* --- HR E FOOTER --- */
        hr {
            margin-top: 0.25rem !important;
            margin-bottom: 0.25rem !important;
            border: none !important;
            border-top: 1px solid #e6e6e6 !important;
        }
        
        /* --- RODAPÉ COMPLETO (COM 3 LINHAS) --- */
        .footer-text {
            text-align: center;
            font-size: 0.95rem;
            color: #444;
            line-height: 1.6;
            margin-top: 0.5rem !important;
        }
        
        .footer-line {
            margin: 0.3rem 0;
        }
        </style>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# FUNÇÕES DE VALIDAÇÃO
# ------------------------------------------------------------------------------
def validar_email(email):
    """Valida formato de e-mail usando regex"""
    if not email:
        return False
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(padrao, email.strip()) is not None

def validar_celular(celular):
    """Valida formato de celular brasileiro: (XX) 9 XXXX-XXXX"""
    if not celular:
        return False
    apenas_numeros = re.sub(r'\D', '', celular.strip())
    if len(apenas_numeros) != 11:
        return False
    if apenas_numeros[2] != '9':
        return False
    return True

def formatar_celular(celular):
    """Formata celular para padrão (XX) 9 XXXX-XXXX"""
    apenas_numeros = re.sub(r'\D', '', celular.strip())
    if len(apenas_numeros) == 11:
        return f"({apenas_numeros[:2]}) {apenas_numeros[2]} {apenas_numeros[3:7]}-{apenas_numeros[7:]}"
    return celular

# ------------------------------------------------------------------------------
# UTILITÁRIOS E CONEXÃO
# ------------------------------------------------------------------------------
def maybe_rerun():
    """Força reexecução do script - compatível com múltiplas versões"""
    try:
        st.rerun()
    except AttributeError:
        try:
            st.experimental_rerun()
        except Exception:
            return

@st.cache_resource(ttl=3600)
def conectar_google_sheets():
    """
    Conecta ao Google Sheets usando google-auth.
    Retorna None em caso de erro (modo offline).
    """
    try:
        if "gcp_service_account" in st.secrets:
            logger.info("Usando credenciais do Streamlit Secrets")
            credentials_dict = dict(st.secrets["gcp_service_account"])
            scopes = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            credentials = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
        else:
            logger.info("Usando arquivo credentials.json local")
            if not os.path.exists(CREDENTIALS_FILE):
                logger.warning("Arquivo credentials.json não encontrado")
                return None
            
            scopes = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
        
        client = gspread.authorize(credentials)
        planilha = client.open_by_key(SPREADSHEET_ID)
        logger.info("Conexão com Google Sheets estabelecida com sucesso")
        return planilha
        
    except Exception as e:
        logger.warning(f"Falha ao conectar Google Sheets: {e}")
        return None

def carregar_perguntas():
    """Carrega perguntas do arquivo JSON"""
    try:
        if os.path.exists('perguntas.json'):
            with open('perguntas.json', 'r', encoding='utf-8') as f:
                perguntas = json.load(f)
                logger.info(f"Perguntas carregadas: {len(perguntas)} categorias")
                return perguntas
        else:
            logger.warning("Arquivo perguntas.json não encontrado")
            return {}
    except Exception as e:
        logger.error(f"Erro ao carregar perguntas: {e}")
        return {}

def normalizar_texto(texto):
    """Remove acentos, hífens, espaços e converte para minúsculas"""
    if not texto:
        return ""
    # Remove acentos
    texto_sem_acento = unicodedata.normalize('NFD', str(texto)).encode('ascii', 'ignore').decode("utf-8")
    # Remove hífens e espaços, depois strip e lower
    texto_limpo = texto_sem_acento.replace('-', '').replace(' ', '').strip().lower()
    return texto_limpo

def gerar_chave_unica(row):
    """
    Gera chave de controle para verificar se o aluno já avaliou determinada disciplina.
    
    Formato: {codigo_disciplina}_{ultimos_4_digitos_siape}_{matricula}
    Exemplo: G11QORG1.01_8807_2027MEC9997
    
    IMPORTANTE: esta chave é gravada APENAS na planilha Controle_Anonimato,
    que NÃO contém respostas. Serve exclusivamente para evitar avaliações
    duplicadas (o mesmo aluno avaliando a mesma disciplina duas vezes).
    
    A planilha de Respostas NÃO recebe esta chave.
    
    Destino: planilha "Controle_Anonimato", coluna 2
    """
    siape = str(row.get('siapeprof', '0000')).strip()[-4:]
    mat = str(row.get('matricula', '00000000000')).strip()
    cod = str(row.get('codigo', 'DISC')).strip()
    return f"{cod}_{siape}_{mat}"


def gerar_id_anonimo():
    """
    Gera identificador aleatório para a planilha de Respostas.
    
    Processo:
    1. Concatena timestamp ISO + 16 bytes de entropia criptográfica (os.urandom)
    2. Aplica hash SHA-256 sobre essa string
    3. Retorna os primeiros 12 caracteres hexadecimais em maiúsculo
    
    Resultado: string como "A3F7B2E9C1D4" — sem nenhum vínculo com matrícula,
    nome, ou qualquer dado do aluno. Impossível de reverter.
    
    Destino: planilha "Respostas", coluna 2 (campo id_anonimo)
    """
    import hashlib
    seed = f"{datetime.now().isoformat()}{os.urandom(16).hex()}"
    return hashlib.sha256(seed.encode()).hexdigest()[:12].upper()

# ------------------------------------------------------------------------------
# RODAPÉ (COM 3 LINHAS)
# ------------------------------------------------------------------------------
def render_footer():
    """Rodapé permanente com 3 linhas"""
    st.markdown("---")
    st.markdown(
        "<div class='footer-text'>"
        "<div class='footer-line'>Desenvolvido por equipe de avaliação • Versão v1.1.0</div>"
        "<div class='footer-line'>CEFET-MG – Campus Contagem - Engenharia Química • 2026</div>"
        "<div class='footer-line'>Contato: engquimica-cn@cefetmg.br</div>"
        "</div>",
        unsafe_allow_html=True
    )

# ------------------------------------------------------------------------------
# TELAS
# ------------------------------------------------------------------------------

def tela_login():
    """
    TELA 1: Autenticação do aluno.
    
    Fluxo:
    1. Aluno digita matrícula e primeiro nome
    2. Sistema busca na planilha BASE_DISCENTES (Google Sheets)
    3. Compara matrícula e primeiro nome (normalizado, sem acentos)
    4. Se válido: salva dados na session_state (memória temporária do Streamlit)
    5. Avança para Tela 2 (Atualização de Contatos)
    
    ANONIMATO: a matrícula e nome ficam APENAS na session_state (memória RAM
    do servidor Streamlit). Nenhum dado é gravado em disco ou planilha nesta etapa.
    Quando o aluno faz logout, a session_state é limpa.
    
    Dados lidos: planilha "BASE_DISCENTES"
    Dados gravados: NENHUM (apenas session_state temporária)
    """
    if os.path.exists("processo_industrial.png"):
        try:
            st.image("processo_industrial.png", use_container_width=True)
        except Exception:
            pass
    
    # Título principal centralizado
    st.markdown('<h1 class="titulo-principal">🧪 Portal de Avaliação Docente EQ</h1>', unsafe_allow_html=True)
    
    # Subtítulo campus centralizado
    st.markdown('<p class="campus-subtitulo">CEFET-MG - Campus Contagem</p>', unsafe_allow_html=True)
    
    with st.form("form_login"):
        mat_in = st.text_input("Sua Matrícula", max_chars=20)
        nome_in = st.text_input("Seu Primeiro Nome", max_chars=50)
        
        # BOTÃO VERDE
        submit = st.form_submit_button("ACESSAR PAINEL 🚀", type="primary", width='stretch')
        
        if submit:
            if not mat_in.strip() or not nome_in.strip():
                st.error("⚠️ Por favor, preencha todos os campos!")
                return
            
            try:
                with st.spinner("Verificando credenciais..."):
                    gc = conectar_google_sheets()
                    if gc is None:
                        st.error("❌ Não foi possível conectar ao sistema. Tente novamente.")
                        return
                    
                    df = pd.DataFrame(gc.worksheet(MAIN_SHEET_BASE).get_all_records())
                    
                    # Debug: mostrar colunas originais
                    logger.info(f"Colunas originais: {df.columns.tolist()}")
                    
                    # Normalizar nomes das colunas (remove acentos, minúsculas, strip)
                    df.columns = [normalizar_texto(str(c)) for c in df.columns]
                    logger.info(f"Colunas normalizadas: {df.columns.tolist()}")
                    
                    # As colunas corretas após normalização são:
                    # matricula, discente, codigo, nome, siapeprof, professor, 
                    # telefonecelular, email
                    
                    # Verificar se coluna matricula existe
                    if 'matricula' not in df.columns:
                        st.error(f"❌ Erro: Coluna 'matricula' não encontrada. Colunas disponíveis: {', '.join(df.columns.tolist())}")
                        logger.error(f"Coluna 'matricula' não existe. Colunas: {df.columns.tolist()}")
                        return
                    
                    # Normalizar dados da matrícula
                    mat_normalizada = mat_in.strip().upper()
                    df['matricula_norm'] = df['matricula'].astype(str).str.strip().str.upper()
                    
                    aluno_match = df[df['matricula_norm'] == mat_normalizada]
                    
                    if not aluno_match.empty:
                        # A coluna de nome é "Discente" → "discente"
                        nome_aluno_completo = str(aluno_match.iloc[0].get('discente', ''))
                        
                        if not nome_aluno_completo or not nome_aluno_completo.strip():
                            st.error(f"❌ Erro: Nome do aluno não encontrado. Colunas disponíveis: {', '.join(df.columns.tolist())}")
                            logger.error(f"Nome vazio ou não encontrado na coluna 'discente'")
                            return
                        
                        nome_base = normalizar_texto(nome_aluno_completo.split()[0])
                        nome_input = normalizar_texto(nome_in)
                        
                        logger.info(f"Comparando: '{nome_base}' com '{nome_input}'")
                        
                        if nome_base == nome_input:
                            st.session_state.aluno_logado = aluno_match.iloc[0].to_dict()
                            st.session_state.minhas_disciplinas = aluno_match
                            st.session_state.etapa = 'atualizacao'
                            logger.info(f"Login bem-sucedido: Matrícula {mat_normalizada}")
                            maybe_rerun()
                            return
                        else:
                            st.error("❌ Nome incorreto para a matrícula informada.")
                            logger.warning(f"Nome incorreto: esperado '{nome_base}', recebido '{nome_input}'")
                    else:
                        st.error("❌ Matrícula não encontrada no sistema.")
                        logger.warning(f"Matrícula não encontrada: {mat_normalizada}")
                        
            except Exception as e:
                logger.error(f"Erro no login: {e}", exc_info=True)
                st.error(f"❌ Erro ao processar login: {e}")
                # Mostrar informação de debug em caso de erro
                try:
                    if 'df' in locals():
                        st.error(f"Debug - Colunas encontradas: {', '.join(df.columns.tolist())}")
                except:
                    pass
    
    render_footer()

def tela_atualizacao():
    """
    TELA 2: Confirmação e atualização de dados de contato (e-mail e celular).
    
    Fluxo:
    1. Exibe dados cadastrais do aluno (vindos da session_state, não de disco)
    2. Aluno confirma ou atualiza e-mail e celular
    3. Dados atualizados ficam na session_state
    
    ANONIMATO: esta tela NÃO grava nada em disco ou planilha.
    Os dados de contato ficam apenas na memória temporária.
    
    Dados lidos: session_state (memória)
    Dados gravados: NENHUM
    """
    st.title("📱 Confirmação de Contatos")
    
    if os.path.exists("gif1.gif"):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            try:
                st.image("gif1.gif", width=410)
            except Exception:
                pass
    
    aluno = st.session_state.aluno_logado
    # Debug: ver o que está no dicionário aluno
    logger.info(f"Chaves disponíveis no aluno: {list(aluno.keys())}")
    logger.info(f"Valores do aluno: {aluno}")
    
    # A coluna de nome é "Discente" → "discente"
    nome_discente = str(aluno.get('discente', '')).upper()
    st.subheader(f"Olá, {nome_discente}! 👋")
    st.write("")

    # SEÇÃO E-MAIL - A coluna é "E-mail" → após normalização será "email"
    st.markdown('<p class="label-sigaa">E-mail cadastrado no SIGAA:</p>', unsafe_allow_html=True)
    email_sigaa = aluno.get("email", "Não informado")
    logger.info(f"Email encontrado: '{email_sigaa}'")
    if not email_sigaa or str(email_sigaa).strip() == "":
        email_sigaa = "Não informado"
    st.markdown(f'<div class="moldura-dados">{email_sigaa}</div>', unsafe_allow_html=True)
    
    # Espaço após moldura
    st.markdown('<div class="espaco-depois-moldura"></div>', unsafe_allow_html=True)
    
    st.markdown('<p class="pergunta-validacao">Este e-mail continua válido?</p>', unsafe_allow_html=True)
    
    c_e = st.radio(
        "Selecione uma opção:",
        ["Sim", "Não"],
        horizontal=True,
        key="ce",
        help="Precisamos de um e-mail válido para contato",
        label_visibility="collapsed"
    )
    
    if c_e == "Não":
        novo_email = st.text_input(
            "Novo e-mail:",
            key="ne",
            placeholder="exemplo@email.com"
        )
        if novo_email and not validar_email(novo_email):
            st.warning("⚠️ Por favor, informe um e-mail válido")
        email_final = novo_email if novo_email and validar_email(novo_email) else email_sigaa
    else:
        email_final = email_sigaa
    
    st.write("---")
    
    # SEÇÃO CELULAR - A coluna é "Telefone Celular" → "telefonecelular"
    st.markdown('<p class="label-sigaa">Celular cadastrado no SIGAA:</p>', unsafe_allow_html=True)
    celular_sigaa = aluno.get("telefonecelular", "Não informado")
    logger.info(f"Celular encontrado: '{celular_sigaa}'")
    if not celular_sigaa or str(celular_sigaa).strip() == "":
        celular_sigaa = "Não informado"
    st.markdown(f'<div class="moldura-dados">{celular_sigaa}</div>', unsafe_allow_html=True)
    
    # Espaço após moldura
    st.markdown('<div class="espaco-depois-moldura"></div>', unsafe_allow_html=True)
    
    st.markdown('<p class="pergunta-validacao">Este celular continua válido?</p>', unsafe_allow_html=True)
    
    c_c = st.radio(
        "Selecione uma opção:",
        ["Sim", "Não"],
        horizontal=True,
        key="cc",
        help="Use o formato: (XX) 9 XXXX-XXXX",
        label_visibility="collapsed"
    )
    
    if c_c == "Não":
        novo_celular = st.text_input(
            "Novo celular:",
            key="nc",
            placeholder="(31) 9 1234-5678"
        )
        if novo_celular:
            if validar_celular(novo_celular):
                celular_final = formatar_celular(novo_celular)
                st.success(f"✅ Celular formatado: {celular_final}")
            else:
                st.warning("⚠️ Celular inválido. Use: (XX) 9 XXXX-XXXX")
                celular_final = celular_sigaa
        else:
            celular_final = celular_sigaa
    else:
        celular_final = celular_sigaa
    
    # Validação final
    pode_prosseguir = True
    if c_e == "Não" and not validar_email(email_final):
        pode_prosseguir = False
    if c_c == "Não" and not validar_celular(celular_final):
        pode_prosseguir = False
    
    if st.button(
        "TUDO PRONTO! VAMOS AVALIAR ⚡",
        type="primary",
        width='stretch',
        disabled=not pode_prosseguir
    ):
        # Atualizar com as colunas corretas da planilha
        st.session_state.aluno_logado.update({
            'email': email_final,
            'telefonecelular': celular_final
        })
        logger.info(f"Dados atualizados: {aluno.get('matricula', 'unknown')}")
        st.session_state.etapa = 'selecao'
        maybe_rerun()
        return
    
    render_footer()

def tela_selecao():
    """
    TELA 3: Seleção de disciplina para avaliar.
    
    Fluxo:
    1. Lê a planilha "Controle_Anonimato" para obter lista de chaves já feitas
    2. Compara com as disciplinas do aluno logado (da session_state)
    3. Exibe métricas: total, realizadas, pendentes
    4. Aluno seleciona professor/disciplina e inicia avaliação
    
    ANONIMATO: esta tela lê a planilha Controle_Anonimato (que tem chaves de
    controle mas NÃO tem respostas). A comparação é feita na memória do servidor.
    
    Dados lidos: planilha "Controle_Anonimato" (coluna 2: chaves)
    Dados gravados: NENHUM
    """
    st.title("🎓 Suas Avaliações")

    try:
        with st.spinner("Carregando suas avaliações..."):
            gc = conectar_google_sheets()
            
            if gc is None:
                st.warning("⚠️ Conexão com planilha indisponível; operando em modo offline.")
                df_m = st.session_state.get("minhas_disciplinas", pd.DataFrame())
                chaves_feitas = []
            else:
                # Verificar avaliações já realizadas
                try:
                    sh_controle = gc.worksheet(CONTROL_SHEET)
                    chaves_feitas = [str(c).strip() for c in sh_controle.col_values(2)[1:]]
                except gspread.exceptions.WorksheetNotFound:
                    # Primeira execução: aba ainda não existe
                    chaves_feitas = []
                df_m = st.session_state.minhas_disciplinas.copy()

            if not isinstance(df_m, pd.DataFrame):
                df_m = pd.DataFrame()

            if not df_m.empty:
                df_m['chave'] = df_m.apply(gerar_chave_unica, axis=1)
            
            pendentes = df_m[~df_m['chave'].isin(chaves_feitas)] if not df_m.empty else pd.DataFrame()
            concluidas = df_m[df_m['chave'].isin(chaves_feitas)] if not df_m.empty else pd.DataFrame()

            # Métricas centralizadas
            st.markdown('<div style="display: flex; justify-content: center; margin: 2rem 0;">', unsafe_allow_html=True)
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Total", len(df_m))
            with col_b:
                st.metric("Realizadas", len(concluidas))
            with col_c:
                st.metric("Pendentes", len(pendentes))
            st.markdown('</div>', unsafe_allow_html=True)

            st.write("---")

            if not pendentes.empty:
                st.markdown('<h3 class="subtitulo-pendentes">📋 Avaliações Pendentes</h3>', unsafe_allow_html=True)
                # As colunas são: "Professor" → "professor" e "Nome" → "nome" (nome da disciplina)
                lista_opcoes = pendentes.apply(
                    lambda x: f"👨‍🏫 {x.get('professor', '')} | 📘 {x.get('nome', '')}",
                    axis=1
                ).tolist()
                
                escolha = st.selectbox(
                    "Quem vamos avaliar agora?",
                    lista_opcoes,
                    help="Selecione o professor e disciplina"
                )
                
                # Botão verde INICIAR AVALIAÇÃO
                if st.button("INICIAR AVALIAÇÃO ✨", type="primary", width='stretch'):
                    idx = lista_opcoes.index(escolha)
                    st.session_state.disciplina_foco = pendentes.iloc[idx].to_dict()
                    st.session_state.etapa = 'questionario'
                    logger.info(f"Iniciando: {escolha}")
                    maybe_rerun()
                    return
            else:
                st.success("🎉 Parabéns! Você concluiu todas as avaliações!")
                st.balloons()

            if not concluidas.empty:
                st.write("---")
                with st.expander("📝 HISTÓRICO DE AVALIAÇÕES CONCLUÍDAS"):
                    for _, r in concluidas.iterrows():
                        st.markdown(f"✅ **{r.get('professor', '')}** - {r.get('nome', '')}")

    except Exception as e:
        logger.error(f"Erro ao carregar avaliações: {e}")
        st.error(f"❌ {e}")

    st.write("---")
    if st.button("SAIR COM SEGURANÇA 🔒", type="secondary", width='stretch'):
        for k in ['aluno_logado', 'minhas_disciplinas', 'disciplina_foco', '_pending_login']:
            st.session_state.pop(k, None)
        st.session_state.etapa = 'login'
        logger.info("Logout realizado")
        maybe_rerun()
        return

    render_footer()

def tela_questionario():
    """
    TELA 4: Questionário de avaliação — onde o aluno responde as 44 perguntas.
    
    Fluxo:
    1. Exibe professor e disciplina selecionados
    2. Renderiza perguntas por categoria (Likert 1-5, escala 0-10, abertas)
    3. Valida: mínimo 70% respondido + todas as abertas preenchidas
    4. Ao clicar "Enviar":
       a) Calcula média das notas numéricas
       b) Gera id_anonimo (hash SHA-256 aleatório, sem vínculo com matrícula)
       c) Gera chave_controle (identifica disciplina + aluno para evitar duplicação)
       d) Grava na planilha "Respostas": [data, id_anonimo, professor, disciplina, notas]
          → SEM matrícula, SEM nome do aluno
       e) Grava na planilha "Controle_Anonimato": [data, chave_controle]
          → SEM respostas, SEM notas
    
    ANONIMATO: o ponto crítico está no passo (d). A linha gravada em "Respostas"
    contém apenas id_anonimo (aleatório), professor, disciplina e notas.
    Não existe nenhum campo que identifique o aluno. A chave_controle (que contém
    a matrícula) vai para uma planilha SEPARADA que não tem respostas.
    
    Dados gravados em "Respostas": data, id_anonimo, professor, disciplina, p1..p41, abertas, pontuação
    Dados gravados em "Controle_Anonimato": data, chave_controle
    Dados NÃO gravados: matrícula, nome do aluno, e-mail, celular
    """
    foco = st.session_state.disciplina_foco
    perguntas_data = carregar_perguntas()

    if not perguntas_data:
        st.error("❌ Não foi possível carregar as perguntas.")
        if st.button("Voltar", width='stretch'):
            st.session_state.etapa = 'selecao'
            maybe_rerun()
        return

    respostas_discente = {}
    st.title("📝 Questionário de Avaliação")
    
    # Professor em uma linha, disciplina em outra
    # As colunas são: "Professor" → "professor" e "Nome" → "nome"
    st.markdown(
        '<div class="info-avaliacao">'
        f'<div class="info-professor">Professor(a): {foco.get("professor","")}</div>'
        f'<div class="info-disciplina">Disciplina: {foco.get("nome","")}</div>'
        '</div>',
        unsafe_allow_html=True
    )

    total_perguntas = sum(len(lista) for lista in perguntas_data.values())

    with st.form("form_questionario"):
        for categoria, lista in perguntas_data.items():
            with st.expander(f"📍 {categoria}", expanded=True):
                for p in lista:
                    # Pergunta justificada
                    st.markdown(f'<p class="pergunta-texto">{p}</p>', unsafe_allow_html=True)
                    
                    if "[ABERTA]" in p:
                        respostas_discente[p] = st.text_area(
                            "Resposta",
                            key=f"ab_{hash(p)}",
                            label_visibility="collapsed",
                            placeholder="Digite sua resposta aqui..."
                        )
                    elif "[1-5]" in p or "[1-10]" in p:
                        notas = [1,2,3,4,5] if "[1-5]" in p else list(range(1, 11))
                        respostas_discente[p] = st.radio(
                            f"Nota para: {p[:30]}...",
                            notas,
                            key=f"k_{hash(p)}",
                            horizontal=True,
                            label_visibility="collapsed",
                            index=None
                        )
                    else:
                        respostas_discente[p] = st.radio(
                            "Escolha",
                            ["Sim", "Não", "Não sei"],
                            horizontal=True,
                            key=f"sn_{hash(p)}",
                            label_visibility="collapsed",
                            index=None
                        )

        # Botão VERDE para enviar
        if st.form_submit_button("ENVIAR AVALIAÇÃO ✉️", type="primary", width='stretch'):
            respondidas = sum(1 for v in respostas_discente.values() if v is not None and str(v).strip() != "")
            percentual = (respondidas / total_perguntas) * 100 if total_perguntas else 0
            vazias_abertas = [p for p, v in respostas_discente.items() if "[ABERTA]" in p and (v is None or str(v).strip() == "")]

            if percentual < 70:
                st.error(f"⚠️ Você respondeu apenas {percentual:.0f}% do questionário. Mínimo: 70%.")
                return
            if vazias_abertas:
                st.error("⚠️ Preencha todas as questões de texto antes de enviar.")
                return

            try:
                with st.spinner("Salvando sua avaliação..."):
                    gc = conectar_google_sheets()
                    
                    notas_calc = [
                        MAPA_NOTAS.get(v, v)
                        for p, v in respostas_discente.items()
                        if isinstance(MAPA_NOTAS.get(v, v), (int, float))
                    ]
                    media = round(sum(notas_calc) / len(notas_calc), 2) if notas_calc else 0
                    
                    chave_controle = gerar_chave_unica(foco)  # Para Controle_Anonimato (sem respostas)
                    id_anonimo = gerar_id_anonimo()            # Hash aleatório para Respostas (sem matrícula)
                    
                    # ┌─────────────────────────────────────────────────────────┐
                    # │ LINHA GRAVADA NA PLANILHA "Respostas"                   │
                    # │ Campos: data | id_anonimo | professor | disciplina |   │
                    # │         p1..p41 | abertas 1-3 | pontuação              │
                    # │ NÃO inclui: matrícula, nome, e-mail, chave_controle    │
                    # └─────────────────────────────────────────────────────────┘
                    linha_respostas = [
                        datetime.now().strftime("%d/%m/%Y %H:%M"),  # Col A: data/hora
                        id_anonimo,                                  # Col B: ID aleatório (hash)
                        foco.get('professor', ''),                   # Col C: nome do professor
                        foco.get('nome', ''),                        # Col D: nome da disciplina
                    ]                                                # Cols E+: respostas p1..p41, abertas, média
                    linha_respostas.extend([MAPA_NOTAS.get(v, v) for v in respostas_discente.values()])
                    linha_respostas.append(media)
                    
                    # ┌─────────────────────────────────────────────────────────┐
                    # │ LINHA GRAVADA NA PLANILHA "Controle_Anonimato"         │
                    # │ Campos: data | chave_controle                          │
                    # │ NÃO inclui: respostas, notas, textos abertos           │
                    # └─────────────────────────────────────────────────────────┘
                    linha_controle = [
                        datetime.now().strftime("%d/%m/%Y %H:%M"),  # Col A: data/hora
                        chave_controle                               # Col B: chave (disciplina+prof+aluno)
                    ]

                    # Salvar online ou localmente
                    if gc:
                        gc.worksheet(MAIN_SHEET_RESP).append_row(
                            linha_respostas, value_input_option='USER_ENTERED'
                        )
                        # Registrar no controle de duplicação
                        try:
                            gc.worksheet(CONTROL_SHEET).append_row(
                                linha_controle, value_input_option='USER_ENTERED'
                            )
                        except gspread.exceptions.WorksheetNotFound:
                            planilha = gc
                            ws = planilha.add_worksheet(
                                title=CONTROL_SHEET, rows=2000, cols=2
                            )
                            ws.append_row(["data_hora", "chave_controle"])
                            ws.append_row(linha_controle, value_input_option='USER_ENTERED')
                            logger.info("Aba de controle criada")
                        
                        logger.info(f"Avaliacao registrada: {id_anonimo}")
                    else:
                        # Fallback local
                        df_local = pd.DataFrame([linha_respostas])
                        if os.path.exists(LOCAL_FALLBACK_RESP):
                            df_exist = pd.read_csv(LOCAL_FALLBACK_RESP, header=None)
                            df_concat = pd.concat([df_exist, df_local], ignore_index=True)
                            df_concat.to_csv(LOCAL_FALLBACK_RESP, index=False, header=False)
                        else:
                            df_local.to_csv(LOCAL_FALLBACK_RESP, index=False, header=False)
                        logger.info(f"Avaliacao registrada localmente: {id_anonimo}")

                    st.session_state.etapa = 'pos_envio'
                    maybe_rerun()
                    return

            except Exception as e:
                logger.error(f"Erro ao salvar: {e}")
                st.error(f"❌ Erro ao salvar avaliação: {e}")

    render_footer()

def tela_sucesso():
    """
    TELA 5: Confirmação de envio bem-sucedido.
    
    Exibe mensagem de sucesso e oferece opções:
    - Avaliar outro professor (volta para Tela 3)
    - Finalizar e sair (limpa session_state, volta para Tela 1)
    
    Dados gravados: NENHUM (dados já foram gravados na Tela 4)
    """
    st.title("✅ Sucesso!")
    
    if os.path.exists("gif3.gif"):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            try:
                st.image("gif3.gif", width=420)
            except Exception:
                pass

    st.balloons()
    
    # Mensagem centralizada e com fonte maior
    st.markdown(
        '<p class="mensagem-sucesso">🎉 Obrigado pela sua participação! Sua opinião é muito importante.</p>',
        unsafe_allow_html=True
    )

    if st.button("AVALIAR OUTRO PROFESSOR", type="primary", width='stretch'):
        st.session_state.etapa = 'selecao'
        maybe_rerun()
        return

    if st.button("FINALIZAR E SAIR 🔒", type="secondary", width='stretch'):
        for k in ['aluno_logado', 'minhas_disciplinas', 'disciplina_foco', '_pending_login']:
            st.session_state.pop(k, None)
        st.session_state.etapa = 'login'
        logger.info("Finalização e logout")
        maybe_rerun()
        return

    render_footer()

# ------------------------------------------------------------------------------
# EXECUÇÃO PRINCIPAL
# ------------------------------------------------------------------------------
def main():
    """Função principal"""
    aplicar_estilo_visual()
    
    # Session ID
    if "_session_id" not in st.session_state:
        st.session_state["_session_id"] = os.urandom(8).hex()
    
    if 'etapa' not in st.session_state:
        st.session_state.etapa = 'login'
        logger.info("Nova sessão iniciada")

    telas = {
        'login': tela_login,
        'atualizacao': tela_atualizacao,
        'selecao': tela_selecao,
        'questionario': tela_questionario,
        'pos_envio': tela_sucesso
    }
    
    telas.get(st.session_state.etapa, tela_login)()

if __name__ == "__main__":
    main()

# ==============================================================================
# FIM - VERSÃO v1.1.0 - RESPOSTAS ANONIMIZADAS
# ==============================================================================
