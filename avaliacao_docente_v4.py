#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Avaliação Docente - Versão 4.0 FINAL
CEFET-MG Engenharia Química

Autor: Sistema Integrado V4.0
Data: 01/03/2026
Status: PRONTO PARA DEPLOYMENT

Este script calcula automaticamente:
- Conversão Likert 1-5 → Nota 1-10
- Score de engajamento (D1)
- Scores por dimensão com pesos internos
- Aplicação dos 16 cruzamentos
- Nota final do professor (1-10)
- Relatório de confiabilidade
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import json
from datetime import datetime

# ============================================================================
# CONFIGURAÇÕES GLOBAIS
# ============================================================================

PESOS_DIMENSOES = {
    'D1': 0.00,  # Calibrador
    'D2': 0.22,  # Organização e Clareza
    'D3': 0.20,  # Didático-Pedagógico
    'D4': 0.13,  # Métodos e Recursos
    'D5': 0.17,  # Avaliação e Retorno
    'D6': 0.11,  # Relacionamento
    'D7': 0.07,  # Entusiasmo
    'D8': 0.07,  # Perspectiva EQ
    'D9': 0.03,  # Global
}

PESOS_PERGUNTAS = {
    # D1 - Autoavaliação (pesos para cálculo de engajamento)
    'Q001': 0.20, 'Q002': 0.10, 'Q003': 0.15, 'Q004': 0.20,
    'Q005': 0.10, 'Q006': 0.15, 'Q007': 0.10,
    
    # D2 - Organização e Clareza
    'Q008': 0.30, 'Q009': 0.25, 'Q010': 0.20, 'Q011': 0.15, 'Q012': 0.10,
    
    # D3 - Didático-Pedagógico
    'Q013': 0.35, 'Q014': 0.30, 'Q015': 0.20, 'Q016': 0.15,
    
    # D4 - Métodos e Recursos
    'Q017': 0.30, 'Q018': 0.30, 'Q019': 0.20, 'Q020': 0.20,
    
    # D5 - Avaliação e Retorno (todas iguais - todas críticas)
    'Q021': 0.25, 'Q022': 0.25, 'Q023': 0.25, 'Q024': 0.25,
    
    # D6 - Relacionamento
    'Q025': 0.30, 'Q026': 0.25, 'Q027': 0.25, 'Q028': 0.10, 'Q029': 0.10,
    
    # D7 - Entusiasmo
    'Q030': 0.40, 'Q031': 0.35, 'Q032': 0.25,
    
    # D8 - Perspectiva EQ
    'Q033': 0.35, 'Q034': 0.35, 'Q035': 0.30,
    
    # D9 - Global (Q036-Q040 são 0-10, Q041 é Likert)
    'Q036': 0.20, 'Q037': 0.25, 'Q038': 0.15, 
    'Q039': 0.20, 'Q040': 0.15, 'Q041': 0.05,
}

# ============================================================================
# FUNÇÕES DE CONVERSÃO
# ============================================================================

def converter_likert_para_nota(resposta: float) -> Optional[float]:
    """
    Converte resposta Likert 1-5 para escala 1-10.
    
    Fórmula: score = 1 + (resposta - 1) × 9/4
    
    Args:
        resposta: Valor Likert de 1 a 5
        
    Returns:
        Nota de 1 a 10, ou None se resposta inválida
    """
    if pd.isna(resposta) or resposta < 1 or resposta > 5:
        return None
    
    return 1 + (resposta - 1) * 9 / 4


def normalizar_escala_0_10(resposta: float) -> Optional[float]:
    """
    Para perguntas que já usam escala 0-10 (Q036-Q040).
    Converte 0-10 para 1-10 mantendo a proporção.
    
    Args:
        resposta: Valor de 0 a 10
        
    Returns:
        Valor de 1 a 10
    """
    if pd.isna(resposta) or resposta < 0 or resposta > 10:
        return None
    
    # Converter 0-10 para 1-10: 1 + (resposta × 9/10)
    return 1 + (resposta * 9 / 10)


# ============================================================================
# CÁLCULO DE SCORES POR DIMENSÃO
# ============================================================================

def calcular_score_engajamento(respostas: Dict[str, float]) -> Dict:
    """
    Calcula score de engajamento (Dimensão 1).
    
    Args:
        respostas: Dicionário com respostas Q001-Q007
        
    Returns:
        Dict com score e categoria
    """
    perguntas_d1 = ['Q001', 'Q002', 'Q003', 'Q004', 'Q005', 'Q006', 'Q007']
    
    score = 0
    pesos_usados = 0
    
    for pergunta in perguntas_d1:
        if pergunta in respostas and respostas[pergunta] is not None:
            valor_convertido = converter_likert_para_nota(respostas[pergunta])
            if valor_convertido is not None:
                peso = PESOS_PERGUNTAS[pergunta]
                score += valor_convertido * peso
                pesos_usados += peso
    
    # Normalizar pelo peso usado
    if pesos_usados > 0:
        score = score / pesos_usados
    else:
        score = None
    
    # Determinar categoria
    if score is None:
        categoria = "INDEFINIDO"
    elif score < 3:
        categoria = "CRÍTICO BAIXO"
    elif score < 5:
        categoria = "MODERADO BAIXO"
    elif score < 7:
        categoria = "MÉDIO"
    else:
        categoria = "ALTO"
    
    return {
        'score': score,
        'categoria': categoria,
        'presenca': respostas.get('Q001'),
        'rotina_estudo': respostas.get('Q004'),
        'participacao': respostas.get('Q006')
    }


def calcular_score_dimensao(respostas: Dict[str, float], 
                           dimensao: str,
                           perguntas: List[str]) -> Optional[float]:
    """
    Calcula score ponderado de uma dimensão.
    
    Args:
        respostas: Dicionário com todas as respostas
        dimensao: ID da dimensão (D2-D9)
        perguntas: Lista de códigos das perguntas da dimensão
        
    Returns:
        Score de 1 a 10, ou None se não houver respostas válidas
    """
    score = 0
    pesos_usados = 0
    
    for pergunta in perguntas:
        if pergunta in respostas and respostas[pergunta] is not None:
            # Perguntas Q036-Q040 já estão em escala 0-10
            if pergunta in ['Q036', 'Q037', 'Q038', 'Q039', 'Q040']:
                valor_convertido = normalizar_escala_0_10(respostas[pergunta])
            else:
                valor_convertido = converter_likert_para_nota(respostas[pergunta])
            
            if valor_convertido is not None:
                peso = PESOS_PERGUNTAS[pergunta]
                score += valor_convertido * peso
                pesos_usados += peso
    
    if pesos_usados > 0:
        return score / pesos_usados
    else:
        return None


# ============================================================================
# SISTEMA DE 16 CRUZAMENTOS
# ============================================================================

def aplicar_cruzamentos(respostas: Dict[str, float],
                       scores: Dict[str, float],
                       engajamento: Dict) -> Dict:
    """
    Aplica os 16 cruzamentos do sistema V4.0.
    
    Args:
        respostas: Dicionário com todas as respostas
        scores: Dicionário com scores calculados por dimensão
        engajamento: Info sobre engajamento do aluno
        
    Returns:
        Dict com modificadores aplicados e justificativas
    """
    modificadores = {
        'D2': 1.0, 'D3': 1.0, 'D4': 1.0, 'D5': 1.0,
        'D6': 1.0, 'D7': 1.0, 'D8': 1.0, 'D9': 1.0
    }
    
    cruzamentos_ativados = []
    
    # CR01 - Exposição Mínima
    q001 = respostas.get('Q001')
    if q001 is not None:
        if q001 <= 2:
            fator_presenca = 0.70
            cruzamentos_ativados.append({
                'id': 'CR01',
                'nome': 'Exposição Mínima',
                'fator': 0.70,
                'justificativa': 'Presença crítica baixa (Q001≤2)'
            })
        elif q001 == 3:
            fator_presenca = 0.85
            cruzamentos_ativados.append({
                'id': 'CR01',
                'nome': 'Exposição Mínima',
                'fator': 0.85,
                'justificativa': 'Presença moderada baixa (Q001=3)'
            })
        else:
            fator_presenca = 1.00
        
        # Aplicar a todas dimensões
        for dim in ['D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9']:
            modificadores[dim] *= fator_presenca
    
    # CR02 - Engajamento Composto
    q004 = respostas.get('Q004')
    q005 = respostas.get('Q005')
    q006 = respostas.get('Q006')
    
    if all(x is not None for x in [q004, q005, q006]):
        media_engaj = (q004 + q005 + q006) / 3
        if media_engaj < 3:
            # Afeta apenas itens-síntese (D9)
            modificadores['D9'] *= 0.85
            cruzamentos_ativados.append({
                'id': 'CR02',
                'nome': 'Engajamento Composto',
                'fator': 0.85,
                'justificativa': f'Média engajamento baixa ({media_engaj:.2f}<3)'
            })
    
    # CR03 - Conhecimento Prévio × Dificuldade
    q002 = respostas.get('Q002')
    q038 = respostas.get('Q038')
    if q002 is not None and q038 is not None:
        if q002 <= 2 and q038 >= 4:
            # Penaliza apenas D9 (avaliações globais)
            modificadores['D9'] *= 0.85
            cruzamentos_ativados.append({
                'id': 'CR03',
                'nome': 'Conhecimento Prévio × Dificuldade',
                'fator': 0.85,
                'justificativa': 'Base prévia fraca + disciplina difícil'
            })
    
    # CR04 - Integridade Acadêmica
    q003 = respostas.get('Q003')
    if q003 is not None and q003 <= 2:
        # Afeta D5 (avaliação) e D9 (global)
        modificadores['D5'] *= 0.85
        modificadores['D9'] *= 0.85
        cruzamentos_ativados.append({
            'id': 'CR04',
            'nome': 'Integridade Acadêmica',
            'fator': 0.85,
            'justificativa': 'Baixa integridade em entregas (Q003≤2)'
        })
    
    # CR05 - Clareza vs Halo Global
    q008 = respostas.get('Q008')
    q009 = respostas.get('Q009')
    q010 = respostas.get('Q010')
    q037 = respostas.get('Q037')
    
    if all(x is not None for x in [q008, q009, q010, q037]):
        media_clareza = (q008 + q009 + q010) / 3
        # Contradição: clareza baixa MAS nota alta, OU inverso
        if (media_clareza <= 2 and q037 >= 4) or (media_clareza >= 4 and q037 <= 2):
            modificadores['D9'] *= 0.90
            cruzamentos_ativados.append({
                'id': 'CR05',
                'nome': 'Clareza vs Halo Global',
                'fator': 0.90,
                'justificativa': f'Contradição clareza({media_clareza:.1f}) vs nota({q037:.1f})'
            })
    
    # CR06 - Alinhamento Construtivo (DIAGNÓSTICO - amplifica D5)
    q010_v = respostas.get('Q010')
    q021 = respostas.get('Q021')
    q023 = respostas.get('Q023')
    if q010_v is not None and q021 is not None and q023 is not None:
        if q010_v >= 4 and (q021 <= 2 or q023 <= 2):
            # Amplifica peso de Q022/Q024 (diagnóstico de problema)
            modificadores['D5'] *= 1.10
            cruzamentos_ativados.append({
                'id': 'CR06',
                'nome': 'Alinhamento Construtivo',
                'fator': 1.10,
                'justificativa': 'Objetivos claros MAS avaliação incoerente'
            })
    
    # CR07 - Rigor sem Injustiça (PROTEÇÃO para professor rigoroso justo)
    q016 = respostas.get('Q016')
    q022 = respostas.get('Q022')
    q038_v = respostas.get('Q038')
    if all(x is not None for x in [q016, q022, q038_v]):
        if q016 >= 4 and q022 >= 4 and q038_v >= 4:
            # Protege professor exigente mas justo
            modificadores['D9'] *= 0.80  # REDUZ peso da global (que pode estar baixa por dificuldade)
            cruzamentos_ativados.append({
                'id': 'CR07',
                'nome': 'Rigor sem Injustiça',
                'fator': 0.80,
                'justificativa': '⚡ PROTEÇÃO: Professor rigoroso mas justo'
            })
    
    # CR08 - Organização de Materiais (DIAGNÓSTICO)
    q011 = respostas.get('Q011')
    q017 = respostas.get('Q017')
    if q011 is not None and q017 is not None:
        if q011 <= 2 and q017 <= 2:
            # Amplifica D4 (métodos) como sinal diagnóstico
            modificadores['D4'] *= 1.10
            cruzamentos_ativados.append({
                'id': 'CR08',
                'nome': 'Organização de Materiais',
                'fator': 1.10,
                'justificativa': 'Plataforma E material ruins (sinal forte)'
            })
    
    # CR09 - Suporte Disponível vs Uso
    q005_v = respostas.get('Q005')
    q025 = respostas.get('Q025')
    q026 = respostas.get('Q026')
    if all(x is not None for x in [q005_v, q025, q026]):
        media_suporte = (q025 + q026) / 2
        if q005_v <= 2 and media_suporte >= 4:
            # Não buscou ajuda MAS suporte é bom → reduz peso críticas
            modificadores['D6'] *= 0.90
            cruzamentos_ativados.append({
                'id': 'CR09',
                'nome': 'Suporte Disponível vs Uso',
                'fator': 0.90,
                'justificativa': 'Não buscou ajuda apesar de disponível'
            })
        elif q005_v >= 4 and media_suporte <= 2:
            # Buscou ajuda MAS suporte ruim → amplifica crítica
            modificadores['D6'] *= 1.10
            cruzamentos_ativados.append({
                'id': 'CR09',
                'nome': 'Suporte Disponível vs Uso',
                'fator': 1.10,
                'justificativa': 'Buscou ajuda MAS suporte insuficiente'
            })
    
    # CR10 - Clima de Sala e Participação
    q006_v = respostas.get('Q006')
    q027 = respostas.get('Q027')
    if q006_v is not None and q027 is not None:
        if q027 <= 2 and q006_v <= 2:
            # Clima ruim explica baixa participação
            modificadores['D7'] *= 1.05
            cruzamentos_ativados.append({
                'id': 'CR10',
                'nome': 'Clima de Sala e Participação',
                'fator': 1.05,
                'justificativa': 'Clima ruim explica baixa participação'
            })
        elif q027 >= 4 and q006_v <= 2:
            # Clima bom MAS baixa participação (problema do aluno)
            modificadores['D7'] *= 0.90
            cruzamentos_ativados.append({
                'id': 'CR10',
                'nome': 'Clima de Sala e Participação',
                'fator': 0.90,
                'justificativa': 'Clima bom MAS baixa participação'
            })
    
    # CR11 - Teoria–Prática (REFORÇO POSITIVO)
    q015 = respostas.get('Q015')
    q018 = respostas.get('Q018')
    if q015 is not None and q018 is not None:
        if q015 >= 4 and q018 >= 4:
            # Exemplos + aplicações boas → reforça valor
            modificadores['D8'] *= 1.05
            cruzamentos_ativados.append({
                'id': 'CR11',
                'nome': 'Teoria–Prática',
                'fator': 1.05,
                'justificativa': '⭐ Exemplos e aplicações práticas excelentes'
            })
        elif q015 <= 2 and q018 <= 2:
            modificadores['D8'] *= 0.90
            cruzamentos_ativados.append({
                'id': 'CR11',
                'nome': 'Teoria–Prática',
                'fator': 0.90,
                'justificativa': 'Falta de exemplos e aplicações práticas'
            })
    
    # CR12 - Inovação com Carga Cognitiva (ALERTA)
    q019 = respostas.get('Q019')
    q009_v = respostas.get('Q009')
    q038_v2 = respostas.get('Q038')
    if all(x is not None for x in [q019, q009_v, q038_v2]):
        if q019 >= 4 and q009_v <= 2 and q038_v2 >= 4:
            # Inovação SEM estrutura + difícil = problema
            modificadores['D2'] *= 1.10  # Amplifica clareza
            modificadores['D8'] *= 0.90  # Reduz valor percebido
            cruzamentos_ativados.append({
                'id': 'CR12',
                'nome': 'Inovação com Carga Cognitiva',
                'fator': 'variado',
                'justificativa': '⚠️ Inovação sem estrutura clara'
            })
    
    # CR13 - Atualização com Perspectiva
    q032 = respostas.get('Q032')
    q033 = respostas.get('Q033')
    q035 = respostas.get('Q035')
    if all(x is not None for x in [q032, q033, q035]):
        if q032 >= 4 and (q033 <= 2 or q035 <= 2):
            # Atualizado MAS sem contexto
            modificadores['D8'] *= 0.90
            cruzamentos_ativados.append({
                'id': 'CR13',
                'nome': 'Atualização com Perspectiva',
                'fator': 0.90,
                'justificativa': 'Atualizado MAS sem conexão contextual'
            })
        elif q032 >= 4 and q033 >= 4 and q035 >= 4:
            # Atualizado + contextualizado
            modificadores['D8'] *= 1.10
            cruzamentos_ativados.append({
                'id': 'CR13',
                'nome': 'Atualização com Perspectiva',
                'fator': 1.10,
                'justificativa': '⭐ Atualizado E bem contextualizado'
            })
    
    # CR14 - Pontualidade e Organização
    q028 = respostas.get('Q028')
    q012 = respostas.get('Q012')
    q029 = respostas.get('Q029')
    if all(x is not None for x in [q028, q012, q029]):
        if q028 <= 2 and (q012 <= 2 or q029 <= 2):
            # Problemas operacionais
            modificadores['D2'] *= 1.10  # Amplifica organização percebida
            modificadores['D9'] *= 0.90  # Reduz nota geral (não deve absorver tudo)
            cruzamentos_ativados.append({
                'id': 'CR14',
                'nome': 'Pontualidade e Organização',
                'fator': 'variado',
                'justificativa': 'Problemas operacionais afetam percepção'
            })
    
    # CR15 - Comparativos vs Nota Absoluta
    q039 = respostas.get('Q039')
    q040 = respostas.get('Q040')
    q037_v = respostas.get('Q037')
    if all(x is not None for x in [q039, q040, q037_v]):
        media_comp = (q039 + q040) / 2
        # Comparativos extremos vs nota mediana
        if (media_comp >= 8 and q037_v <= 5) or (media_comp <= 3 and q037_v >= 7):
            modificadores['D9'] *= 0.90
            cruzamentos_ativados.append({
                'id': 'CR15',
                'nome': 'Comparativos vs Nota Absoluta',
                'fator': 0.90,
                'justificativa': 'Contradição comparativos vs nota absoluta'
            })
    
    # CR16 - Abertas Obrigatórias em Extremos (FLAG apenas)
    q036 = respostas.get('Q036')
    q037_v2 = respostas.get('Q037')
    flags_cr16 = []
    if q036 is not None and (q036 <= 2 or q036 >= 9):
        flags_cr16.append(f'Q036 extrema ({q036})')
    if q037_v2 is not None and (q037_v2 <= 2 or q037_v2 >= 9):
        flags_cr16.append(f'Q037 extrema ({q037_v2})')
    
    if flags_cr16:
        cruzamentos_ativados.append({
            'id': 'CR16',
            'nome': 'Abertas Obrigatórias em Extremos',
            'fator': 'FLAG',
            'justificativa': f'⚠️ Validação: {", ".join(flags_cr16)} - verificar perguntas abertas'
        })
    
    # ========================================================================
    # NOVOS CRUZAMENTOS V4.1 (CR17-CR26)
    # ========================================================================
    
    # CR17 - Sobrecarga Cognitiva vs Tempo
    q007 = respostas.get('Q007')
    q031 = respostas.get('Q031')
    if all(x is not None for x in [q038, q007, q031]):
        if q038 >= 7 and q007 <= 2 and q031 <= 2:
            # Disciplina difícil + não se prepara + perde interesse
            modificadores['D3'] *= 1.10
            modificadores['D4'] *= 1.10
            cruzamentos_ativados.append({
                'id': 'CR17',
                'nome': 'Sobrecarga Cognitiva',
                'fator': 1.10,
                'justificativa': 'Disciplina difícil + sem preparação = possível sobrecarga'
            })
    
    # CR18 - Pré-requisitos Não Atendidos
    q034 = respostas.get('Q034')
    if all(x is not None for x in [q002, q038, q034]):
        if q002 <= 2 and q038 >= 7 and q034 <= 3:
            modificadores['D3'] *= 1.05
            modificadores['D9'] *= 0.90
            cruzamentos_ativados.append({
                'id': 'CR18',
                'nome': 'Pré-requisitos Não Atendidos',
                'fator': 'variado',
                'justificativa': 'Base fraca + difícil + sem valor = problema pré-requisito'
            })
    
    # CR19 - Carga Horária Excessiva (FLAG apenas)
    if all(x is not None for x in [q004, q007, q031]):
        if q004 >= 4 and q007 >= 4 and q031 <= 2:
            cruzamentos_ativados.append({
                'id': 'CR19',
                'nome': 'Carga Horária Excessiva',
                'fator': 'FLAG',
                'justificativa': '⚠️ Aluno dedicado mas perdeu interesse - carga excessiva?'
            })
    
    # CR20 - Feedback Qualitativo Rico
    q042 = respostas.get('Q042', '')
    q043 = respostas.get('Q043', '')
    if isinstance(q042, str) and isinstance(q043, str):
        if len(q042) > 100 and len(q043) > 100:
            # Aumenta confiabilidade (será aplicado depois)
            cruzamentos_ativados.append({
                'id': 'CR20',
                'nome': 'Feedback Qualitativo Rico',
                'fator': 'CONF+10',
                'justificativa': '⭐ Respostas abertas detalhadas - atenção genuína'
            })
    
    # CR21 - Consistência Interna D2-D3-D4 (FLAG apenas)
    score_d2 = scores.get('D2')
    score_d3 = scores.get('D3')
    score_d4 = scores.get('D4')
    if all(x is not None for x in [score_d2, score_d3, score_d4]):
        if abs(score_d2 - score_d3) > 2.5 or abs(score_d3 - score_d4) > 2.5:
            cruzamentos_ativados.append({
                'id': 'CR21',
                'nome': 'Consistência D2-D3-D4',
                'fator': 'FLAG',
                'justificativa': f'⚠️ Dimensões correlatas muito discrepantes (D2:{score_d2:.1f}, D3:{score_d3:.1f}, D4:{score_d4:.1f})'
            })
    
    # CR22 - Locus de Controle Externo
    q006_locus = respostas.get('Q006')  # Invertida!
    if q006_locus is not None and q037 is not None:
        # Q006 invertida: valor baixo = concordo que esforço reflete
        if q006_locus <= 2 and q037 <= 4:
            modificadores['D9'] *= 0.90
            cruzamentos_ativados.append({
                'id': 'CR22',
                'nome': 'Locus de Controle Externo',
                'fator': 0.90,
                'justificativa': 'Atribui desempenho a fatores externos + nota baixa'
            })
    
    # CR23 - Viés de Recenticidade (FLAG apenas - análise temporal)
    q024_rec = respostas.get('Q024')  # Invertida!
    q028_rec = respostas.get('Q028')
    if q024_rec is not None and q028_rec is not None:
        # Detectar se perguntas finais são muito diferentes das iniciais
        # (simplificado - flag para análise manual)
        cruzamentos_ativados.append({
            'id': 'CR23',
            'nome': 'Viés de Recenticidade',
            'fator': 'FLAG',
            'justificativa': '⚠️ Análise: Verificar se perguntas finais refletem apenas últimas semanas'
        })
    
    # CR24 - Expectativa Disciplina Prática vs Teórica
    q015 = respostas.get('Q015')
    q018 = respostas.get('Q018')  # Invertida!
    if all(x is not None for x in [q015, q018, q034]):
        # Q018 invertida: valor baixo = concordo que usou exemplos
        if q015 >= 4 and q018 <= 2 and q034 <= 3:
            modificadores['D8'] *= 1.10
            cruzamentos_ativados.append({
                'id': 'CR24',
                'nome': 'Expectativa Prática vs Teórica',
                'fator': 1.10,
                'justificativa': 'Exemplos bons MAS não vê valor EQ - expectativa desalinhada'
            })
    
    # CR25 - Comparação com Média da Turma
    # DESATIVADO - Requer agregação de dados da turma
    # Implementar quando houver múltiplas avaliações
    
    # CR26 - Resposta Central Excessiva
    valores_likert = [
        respostas.get(f'Q{i:03d}') for i in range(1, 42)
        if f'Q{i:03d}' in respostas 
        and respostas[f'Q{i:03d}'] is not None
        and i not in [36, 37, 38, 39, 40]  # Excluir escalas 0-10
    ]
    
    if len(valores_likert) >= 10:
        neutros = sum(1 for v in valores_likert if v == 3)
        percentual_neutro = (neutros / len(valores_likert)) * 100
        
        if percentual_neutro > 60:
            cruzamentos_ativados.append({
                'id': 'CR26',
                'nome': 'Resposta Central Excessiva',
                'fator': 'CONF-20',
                'justificativa': f'⚠️ {percentual_neutro:.0f}% de respostas Neutro - falta de reflexão?'
            })
    
    return {
        'modificadores': modificadores,
        'cruzamentos_ativados': cruzamentos_ativados,
        'total_cruzamentos': len(cruzamentos_ativados)
    }


# ============================================================================
# CÁLCULO FINAL E RELATÓRIO
# ============================================================================

def calcular_nota_final(respostas: Dict[str, float]) -> Dict:
    """
    Calcula nota final do professor (1-10) com todos os passos.
    
    Args:
        respostas: Dicionário com todas as respostas do aluno
        
    Returns:
        Dict completo com nota, scores, cruzamentos e relatório
    """
    resultado = {
        'timestamp': datetime.now().isoformat(),
        'versao': '4.0',
        'status': 'CALCULADO'
    }
    
    # Passo 1: Calcular engajamento
    engajamento = calcular_score_engajamento(respostas)
    resultado['engajamento'] = engajamento
    
    # Passo 2: Calcular scores por dimensão
    scores_brutos = {}
    
    # D2
    scores_brutos['D2'] = calcular_score_dimensao(
        respostas, 'D2', 
        ['Q008', 'Q009', 'Q010', 'Q011', 'Q012']
    )
    
    # D3
    scores_brutos['D3'] = calcular_score_dimensao(
        respostas, 'D3',
        ['Q013', 'Q014', 'Q015', 'Q016']
    )
    
    # D4
    scores_brutos['D4'] = calcular_score_dimensao(
        respostas, 'D4',
        ['Q017', 'Q018', 'Q019', 'Q020']
    )
    
    # D5
    scores_brutos['D5'] = calcular_score_dimensao(
        respostas, 'D5',
        ['Q021', 'Q022', 'Q023', 'Q024']
    )
    
    # D6
    scores_brutos['D6'] = calcular_score_dimensao(
        respostas, 'D6',
        ['Q025', 'Q026', 'Q027', 'Q028', 'Q029']
    )
    
    # D7
    scores_brutos['D7'] = calcular_score_dimensao(
        respostas, 'D7',
        ['Q030', 'Q031', 'Q032']
    )
    
    # D8
    scores_brutos['D8'] = calcular_score_dimensao(
        respostas, 'D8',
        ['Q033', 'Q034', 'Q035']
    )
    
    # D9
    scores_brutos['D9'] = calcular_score_dimensao(
        respostas, 'D9',
        ['Q036', 'Q037', 'Q038', 'Q039', 'Q040', 'Q041']
    )
    
    resultado['scores_brutos'] = scores_brutos
    
    # Passo 3: Aplicar cruzamentos
    cruzamentos_info = aplicar_cruzamentos(respostas, scores_brutos, engajamento)
    resultado['cruzamentos'] = cruzamentos_info
    
    # Passo 4: Aplicar modificadores aos scores
    scores_modificados = {}
    for dim, score_bruto in scores_brutos.items():
        if score_bruto is not None:
            modificador = cruzamentos_info['modificadores'].get(dim, 1.0)
            score_mod = score_bruto * modificador
            # Garantir limites 1-10
            score_mod = max(1.0, min(10.0, score_mod))
            scores_modificados[dim] = round(score_mod, 2)
        else:
            scores_modificados[dim] = None
    
    resultado['scores_modificados'] = scores_modificados
    
    # Passo 5: Calcular nota final ponderada
    nota_final = 0
    peso_total = 0
    
    for dim, peso in PESOS_DIMENSOES.items():
        if dim == 'D1':  # Pular calibrador
            continue
        
        score = scores_modificados.get(dim)
        if score is not None:
            nota_final += score * peso
            peso_total += peso
    
    if peso_total > 0:
        nota_final = nota_final / peso_total
        nota_final = round(nota_final, 2)
    else:
        nota_final = None
    
    resultado['nota_final'] = nota_final
    
    # Passo 6: Determinar categoria
    if nota_final is None:
        categoria = "INDEFINIDO"
    elif nota_final >= 8.5:
        categoria = "EXCELENTE"
    elif nota_final >= 7.0:
        categoria = "MUITO BOM"
    elif nota_final >= 5.5:
        categoria = "BOM"
    elif nota_final >= 4.0:
        categoria = "REGULAR"
    else:
        categoria = "INSUFICIENTE"
    
    resultado['categoria'] = categoria
    
    # Passo 7: Calcular índice de confiabilidade
    confiabilidade = calcular_confiabilidade(respostas, engajamento, cruzamentos_info)
    resultado['confiabilidade'] = confiabilidade
    
    return resultado


def calcular_confiabilidade(respostas: Dict[str, float],
                            engajamento: Dict,
                            cruzamentos_info: Dict) -> Dict:
    """
    Calcula índice de confiabilidade da avaliação.
    
    Returns:
        Dict com índice (0-100) e flags
    """
    pontos = 100  # Começar com 100%
    flags = []
    
    # Penalizar por baixo engajamento
    se = engajamento['score']
    if se is not None:
        if se < 3:
            pontos -= 30
            flags.append("⚠️ Engajamento crítico baixo")
        elif se < 5:
            pontos -= 15
            flags.append("⚠️ Engajamento moderado baixo")
    
    # Penalizar por presença baixa
    q001 = respostas.get('Q001')
    if q001 is not None and q001 <= 2:
        pontos -= 25
        flags.append("⚠️ Presença insuficiente")
    
    # Penalizar por muitos cruzamentos negativos
    cruzamentos_negativos = sum(
        1 for c in cruzamentos_info['cruzamentos_ativados']
        if c['fator'] not in ['FLAG', 'variado'] and float(c['fator']) < 1.0
    )
    
    if cruzamentos_negativos >= 4:
        pontos -= 20
        flags.append(f"⚠️ Múltiplos cruzamentos negativos ({cruzamentos_negativos})")
    
    # Verificar contradições (CR16)
    cr16_presente = any(c['id'] == 'CR16' for c in cruzamentos_info['cruzamentos_ativados'])
    if cr16_presente:
        pontos -= 10
        flags.append("⚠️ Avaliações extremas - verificar abertas")
    
    # Calcular variância das respostas (detectar straight-lining)
    valores_likert = [
        respostas[f'Q{i:03d}'] for i in range(1, 42)
        if f'Q{i:03d}' in respostas 
        and respostas[f'Q{i:03d}'] is not None
        and i not in [36, 37, 38, 39, 40]  # Excluir 0-10
    ]
    
    if len(valores_likert) >= 10:
        variancia = np.var(valores_likert)
        if variancia < 0.3:
            pontos -= 25
            flags.append("⚠️ Straight-lining detectado (variância < 0.3)")
    
    # Garantir limites
    pontos = max(0, min(100, pontos))
    
    # Determinar status
    if pontos >= 80:
        status = "ALTA CONFIABILIDADE"
    elif pontos >= 60:
        status = "CONFIABILIDADE MODERADA"
    elif pontos >= 40:
        status = "CONFIABILIDADE BAIXA"
    else:
        status = "CONFIABILIDADE CRÍTICA"
    
    return {
        'indice': pontos,
        'status': status,
        'flags': flags
    }


def gerar_relatorio_texto(resultado: Dict) -> str:
    """
    Gera relatório em texto formatado.
    
    Args:
        resultado: Dict retornado por calcular_nota_final()
        
    Returns:
        String com relatório formatado
    """
    linhas = []
    linhas.append("="*70)
    linhas.append("RELATÓRIO DE AVALIAÇÃO DOCENTE - V4.0 FINAL")
    linhas.append("="*70)
    linhas.append("")
    
    # Nota final
    nota = resultado['nota_final']
    categoria = resultado['categoria']
    
    if nota is not None:
        estrelas = "⭐" * min(5, int(nota / 2))
        linhas.append(f"NOTA FINAL: {nota:.2f}/10 {estrelas}")
        linhas.append(f"Categoria: {categoria}")
    else:
        linhas.append("NOTA FINAL: INDEFINIDA (respostas insuficientes)")
    
    linhas.append("")
    linhas.append("-"*70)
    linhas.append("ENGAJAMENTO DO ESTUDANTE")
    linhas.append("-"*70)
    
    eng = resultado['engajamento']
    if eng['score'] is not None:
        linhas.append(f"Score de Engajamento: {eng['score']:.2f}/10")
        linhas.append(f"Categoria: {eng['categoria']}")
        linhas.append(f"  • Presença: {eng['presenca']}/5")
        linhas.append(f"  • Rotina de estudo: {eng['rotina_estudo']}/5")
        linhas.append(f"  • Participação: {eng['participacao']}/5")
    else:
        linhas.append("Score de Engajamento: INDEFINIDO")
    
    linhas.append("")
    linhas.append("-"*70)
    linhas.append("SCORES POR DIMENSÃO")
    linhas.append("-"*70)
    
    nomes_dim = {
        'D2': 'Organização e Clareza',
        'D3': 'Didático-Pedagógico',
        'D4': 'Métodos e Recursos',
        'D5': 'Avaliação e Retorno',
        'D6': 'Relacionamento',
        'D7': 'Entusiasmo',
        'D8': 'Perspectiva EQ',
        'D9': 'Global',
    }
    
    for dim in ['D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9']:
        nome = nomes_dim[dim]
        bruto = resultado['scores_brutos'].get(dim)
        modificado = resultado['scores_modificados'].get(dim)
        peso = PESOS_DIMENSOES[dim]
        
        if modificado is not None:
            if bruto != modificado:
                linhas.append(f"{dim} {nome:25s}: {bruto:.2f} → {modificado:.2f} (peso: {peso:.0%})")
            else:
                linhas.append(f"{dim} {nome:25s}: {modificado:.2f} (peso: {peso:.0%})")
        else:
            linhas.append(f"{dim} {nome:25s}: N/A")
    
    linhas.append("")
    linhas.append("-"*70)
    linhas.append(f"CRUZAMENTOS ATIVADOS ({resultado['cruzamentos']['total_cruzamentos']})")
    linhas.append("-"*70)
    
    for cruz in resultado['cruzamentos']['cruzamentos_ativados']:
        linhas.append(f"• {cruz['id']} - {cruz['nome']}")
        linhas.append(f"  Fator: {cruz['fator']}")
        linhas.append(f"  {cruz['justificativa']}")
        linhas.append("")
    
    if not resultado['cruzamentos']['cruzamentos_ativados']:
        linhas.append("Nenhum cruzamento ativado")
        linhas.append("")
    
    linhas.append("-"*70)
    linhas.append("CONFIABILIDADE DA AVALIAÇÃO")
    linhas.append("-"*70)
    
    conf = resultado['confiabilidade']
    linhas.append(f"Índice de Confiabilidade: {conf['indice']}/100")
    linhas.append(f"Status: {conf['status']}")
    
    if conf['flags']:
        linhas.append("")
        linhas.append("Flags:")
        for flag in conf['flags']:
            linhas.append(f"  {flag}")
    else:
        linhas.append("✓ Sem flags de alerta")
    
    linhas.append("")
    linhas.append("="*70)
    
    return "\n".join(linhas)


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def processar_avaliacao(respostas: Dict[str, float], 
                       verbose: bool = True) -> Dict:
    """
    Função principal para processar uma avaliação completa.
    
    Args:
        respostas: Dicionário com respostas Q001-Q044
        verbose: Se True, imprime relatório
        
    Returns:
        Dict completo com todos os resultados
    """
    resultado = calcular_nota_final(respostas)
    
    if verbose:
        print(gerar_relatorio_texto(resultado))
    
    return resultado


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Exemplo de respostas
    respostas_exemplo = {
        # D1 - Autoavaliação
        'Q001': 5, 'Q002': 4, 'Q003': 5, 'Q004': 4,
        'Q005': 5, 'Q006': 4, 'Q007': 4,
        
        # D2 - Clareza
        'Q008': 5, 'Q009': 4, 'Q010': 5, 'Q011': 4, 'Q012': 4,
        
        # D3 - Didática
        'Q013': 5, 'Q014': 5, 'Q015': 4, 'Q016': 5,
        
        # D4 - Métodos
        'Q017': 4, 'Q018': 5, 'Q019': 4, 'Q020': 4,
        
        # D5 - Avaliação
        'Q021': 5, 'Q022': 5, 'Q023': 5, 'Q024': 4,
        
        # D6 - Relacionamento
        'Q025': 5, 'Q026': 4, 'Q027': 5, 'Q028': 4, 'Q029': 4,
        
        # D7 - Entusiasmo
        'Q030': 5, 'Q031': 4, 'Q032': 4,
        
        # D8 - Perspectiva
        'Q033': 4, 'Q034': 5, 'Q035': 4,
        
        # D9 - Global (escala 0-10)
        'Q036': 8, 'Q037': 8, 'Q038': 7, 'Q039': 8, 'Q040': 8, 'Q041': 4,
    }
    
    print("Processando exemplo de avaliação...\n")
    resultado = processar_avaliacao(respostas_exemplo, verbose=True)
    
    print("\n\nExportando resultado como JSON...")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
