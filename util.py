"""
Funções auxiliares para o Sistema de Avaliação Docente V4.0
"""

import json
import pandas as pd
from datetime import datetime
import streamlit as st
from config import *


def carregar_perguntas():
    """
    Carrega perguntas do arquivo JSON.
    Tenta primeiro 'perguntas.json', depois 'perguntas_v4.1_LIMPO.json'
    """
    import os
    
    # Tentar perguntas.json primeiro (para compatibilidade)
    if os.path.exists('perguntas.json'):
        try:
            with open('perguntas.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"⚠️ Erro ao ler perguntas.json: {e}")
    
    # Tentar perguntas_v4.1_LIMPO.json como fallback
    if os.path.exists('perguntas_v4.1_LIMPO.json'):
        try:
            with open('perguntas_v4.1_LIMPO.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"⚠️ Erro ao ler perguntas_v4.1_LIMPO.json: {e}")
    
    st.error("❌ Nenhum arquivo de perguntas encontrado! Verifique se 'perguntas.json' ou 'perguntas_v4.1_LIMPO.json' existe na pasta.")
    return None


def inicializar_sessao():
    """
    Inicializa variáveis de sessão do Streamlit
    """
    if 'respostas' not in st.session_state:
        st.session_state.respostas = {}
    
    if 'pagina_atual' not in st.session_state:
        st.session_state.pagina_atual = 0
    
    if 'avaliacao_concluida' not in st.session_state:
        st.session_state.avaliacao_concluida = False
    
    if 'resultado' not in st.session_state:
        st.session_state.resultado = None
    
    if 'id_avaliacao' not in st.session_state:
        st.session_state.id_avaliacao = gerar_id_avaliacao()


def gerar_id_avaliacao():
    """
    Gera ID único para a avaliação
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"AVAL-{timestamp}"


def calcular_progresso(respostas, total_obrigatorias=41):
    """
    Calcula percentual de progresso baseado nas respostas obrigatórias
    """
    respostas_dadas = sum(1 for k, v in respostas.items() 
                         if k.startswith('Q') and v is not None and k not in ['Q042', 'Q043', 'Q044'])
    return (respostas_dadas / total_obrigatorias) * 100


def validar_respostas_obrigatorias(respostas):
    """
    Valida se todas as respostas obrigatórias foram respondidas
    """
    obrigatorias = [f'Q{i:03d}' for i in range(1, 42)]  # Q001-Q041
    faltando = [q for q in obrigatorias if q not in respostas or respostas[q] is None]
    return len(faltando) == 0, faltando


def formatar_nota(nota):
    """
    Formata nota com 2 casas decimais
    """
    if nota is None:
        return "N/A"
    return f"{nota:.2f}"


def obter_categoria_nota(nota):
    """
    Retorna categoria baseada na nota
    """
    if nota is None:
        return "INDEFINIDO"
    
    for categoria, config in CATEGORIAS_NOTA.items():
        if config['min'] <= nota < config['max']:
            return categoria
    
    # Se nota = 10.0 (edge case)
    if nota == 10.0:
        return "EXCELENTE"
    
    return "INDEFINIDO"


def obter_categoria_engajamento(score):
    """
    Retorna categoria de engajamento
    """
    if score is None:
        return "INDEFINIDO"
    
    for categoria, config in CATEGORIAS_ENGAJAMENTO.items():
        if config['min'] <= score < config['max']:
            return categoria
    
    # Edge case: score = 10.0
    if score == 10.0:
        return "ALTO"
    
    return "INDEFINIDO"


def exportar_para_json(resultado, info_adicional=None):
    """
    Exporta resultado para JSON
    """
    dados_export = {
        'id_avaliacao': st.session_state.id_avaliacao,
        'timestamp': datetime.now().isoformat(),
        'versao_sistema': VERSAO,
        'resultado': resultado,
        'respostas': st.session_state.respostas,
    }
    
    if info_adicional:
        dados_export['info_adicional'] = info_adicional
    
    return json.dumps(dados_export, ensure_ascii=False, indent=2)


def exportar_para_csv(resultado):
    """
    Exporta resultado para CSV
    """
    # Criar DataFrame com scores por dimensão
    dados = {
        'ID_Avaliacao': [st.session_state.id_avaliacao],
        'Timestamp': [datetime.now().isoformat()],
        'Nota_Final': [resultado.get('nota_final')],
        'Categoria': [resultado.get('categoria')],
        'Score_Engajamento': [resultado.get('engajamento', {}).get('score')],
        'Confiabilidade': [resultado.get('confiabilidade', {}).get('indice')],
    }
    
    # Adicionar scores por dimensão
    for dim in ['D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9']:
        dados[f'Score_{dim}'] = [resultado.get('scores_modificados', {}).get(dim)]
    
    df = pd.DataFrame(dados)
    return df.to_csv(index=False)


def gerar_relatorio_texto(resultado):
    """
    Gera relatório em texto formatado (Markdown)
    """
    linhas = []
    
    linhas.append("# RELATÓRIO DE AVALIAÇÃO DOCENTE - V4.0")
    linhas.append(f"\n**ID:** {st.session_state.id_avaliacao}")
    linhas.append(f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    linhas.append("\n---\n")
    
    # Nota final
    nota = resultado.get('nota_final')
    categoria = resultado.get('categoria')
    if nota:
        linhas.append(f"## 📊 NOTA FINAL: {nota:.2f}/10")
        linhas.append(f"**Categoria:** {categoria}")
    
    linhas.append("\n---\n")
    
    # Engajamento
    eng = resultado.get('engajamento', {})
    if eng.get('score'):
        linhas.append(f"## 👤 ENGAJAMENTO DO ESTUDANTE")
        linhas.append(f"- **Score:** {eng['score']:.2f}/10")
        linhas.append(f"- **Categoria:** {eng['categoria']}")
    
    linhas.append("\n---\n")
    
    # Scores por dimensão
    linhas.append("## 📋 SCORES POR DIMENSÃO\n")
    
    scores_mod = resultado.get('scores_modificados', {})
    for dim in ['D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9']:
        nome = NOMES_DIMENSOES.get(dim, dim)
        score = scores_mod.get(dim)
        if score:
            linhas.append(f"- **{dim} {nome}:** {score:.2f}/10")
    
    linhas.append("\n---\n")
    
    # Cruzamentos
    cruzamentos = resultado.get('cruzamentos', {}).get('cruzamentos_ativados', [])
    if cruzamentos:
        linhas.append(f"## 🔄 CRUZAMENTOS ATIVADOS ({len(cruzamentos)})\n")
        for cruz in cruzamentos:
            linhas.append(f"- **{cruz['id']} - {cruz['nome']}**")
            linhas.append(f"  - {cruz['justificativa']}")
    
    linhas.append("\n---\n")
    
    # Confiabilidade
    conf = resultado.get('confiabilidade', {})
    if conf:
        linhas.append("## ✅ CONFIABILIDADE\n")
        linhas.append(f"- **Índice:** {conf['indice']}/100")
        linhas.append(f"- **Status:** {conf['status']}")
        
        if conf.get('flags'):
            linhas.append("\n**Flags:**")
            for flag in conf['flags']:
                linhas.append(f"- {flag}")
    
    linhas.append("\n---\n")
    linhas.append(f"\n*Relatório gerado pelo Sistema de Avaliação Docente V{VERSAO}*")
    
    return "\n".join(linhas)


def criar_download_button(conteudo, nome_arquivo, formato='txt', label='📥 Baixar Relatório'):
    """
    Cria botão de download para Streamlit
    """
    mime_types = {
        'txt': 'text/plain',
        'json': 'application/json',
        'csv': 'text/csv',
        'md': 'text/markdown',
    }
    
    mime = mime_types.get(formato, 'text/plain')
    
    st.download_button(
        label=label,
        data=conteudo,
        file_name=nome_arquivo,
        mime=mime,
        use_container_width=True
    )


def formatar_diferenca_score(bruto, modificado):
    """
    Formata diferença entre score bruto e modificado
    """
    if bruto is None or modificado is None:
        return "N/A"
    
    if abs(bruto - modificado) < 0.01:
        return f"{modificado:.2f}"
    else:
        return f"{bruto:.2f} → {modificado:.2f}"


def obter_cor_categoria(categoria):
    """
    Retorna cor baseada na categoria
    """
    return CATEGORIAS_NOTA.get(categoria, {}).get('cor', '#999999')


def obter_emoji_categoria(categoria):
    """
    Retorna emoji baseado na categoria
    """
    return CATEGORIAS_NOTA.get(categoria, {}).get('emoji', '')


def reset_avaliacao():
    """
    Reseta a avaliação (para iniciar nova)
    """
    st.session_state.respostas = {}
    st.session_state.pagina_atual = 0
    st.session_state.avaliacao_concluida = False
    st.session_state.resultado = None
    st.session_state.id_avaliacao = gerar_id_avaliacao()


def salvar_estado_local(chave, valor):
    """
    Salva estado localmente (usando session_state)
    """
    st.session_state[chave] = valor


def carregar_estado_local(chave, padrao=None):
    """
    Carrega estado local
    """
    return st.session_state.get(chave, padrao)


def validar_entrada_numerica(valor, minimo, maximo):
    """
    Valida entrada numérica
    """
    try:
        val = float(valor)
        return minimo <= val <= maximo
    except (ValueError, TypeError):
        return False


def formatar_timestamp(timestamp=None):
    """
    Formata timestamp para exibição
    """
    if timestamp is None:
        timestamp = datetime.now()
    elif isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp)
    
    return timestamp.strftime('%d/%m/%Y às %H:%M:%S')


def obter_info_cruzamento(cruzamento_id):
    """
    Retorna informações de um cruzamento específico
    """
    for cruz in CRUZAMENTOS:
        if cruz['id'] == cruzamento_id:
            return cruz
    return None


def formatar_lista_cruzamentos(cruzamentos_ativados):
    """
    Formata lista de cruzamentos ativados para exibição
    """
    if not cruzamentos_ativados:
        return "Nenhum cruzamento ativado"
    
    linhas = []
    for cruz in cruzamentos_ativados:
        linhas.append(f"• **{cruz['id']}** - {cruz['nome']}")
    
    return "\n".join(linhas)


def calcular_estatisticas_turma(avaliacoes):
    """
    Calcula estatísticas agregadas de múltiplas avaliações
    (Para uso futuro quando houver múltiplas avaliações)
    """
    if not avaliacoes:
        return None
    
    notas = [a['nota_final'] for a in avaliacoes if a.get('nota_final')]
    
    if not notas:
        return None
    
    return {
        'media': sum(notas) / len(notas),
        'mediana': sorted(notas)[len(notas) // 2],
        'minima': min(notas),
        'maxima': max(notas),
        'total_avaliacoes': len(avaliacoes),
    }
