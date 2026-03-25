#!/usr/bin/env python3
"""
Script de Teste - Sistema V4.1
Verifica se todos os arquivos e configurações estão corretos
"""

import sys
import os
import json

print("=" * 80)
print("TESTE DO SISTEMA V4.1 - VERIFICAÇÃO PRÉ-DEPLOYMENT")
print("=" * 80)
print()

erros = []
avisos = []
ok = []

# ============================================================================
# 1. VERIFICAR ARQUIVOS ESSENCIAIS
# ============================================================================

print("📁 1. VERIFICANDO ARQUIVOS ESSENCIAIS...")
print("-" * 80)

arquivos_essenciais = [
    'app.py',
    'config.py',
    'estilo.py',
    'util.py',
    'avaliacao_docente_v4.py',
]

# Verificar perguntas.json OU perguntas_v4.1_LIMPO.json
tem_perguntas = False
if os.path.exists('perguntas.json'):
    ok.append("✅ perguntas.json existe")
    tem_perguntas = True
if os.path.exists('perguntas_v4.1_LIMPO.json'):
    ok.append("✅ perguntas_v4.1_LIMPO.json existe")
    tem_perguntas = True

if not tem_perguntas:
    erros.append("❌ Nenhum arquivo de perguntas encontrado!")

for arquivo in arquivos_essenciais:
    if os.path.exists(arquivo):
        ok.append(f"✅ {arquivo} existe")
    else:
        erros.append(f"❌ {arquivo} NÃO ENCONTRADO!")

print()

# ============================================================================
# 2. VERIFICAR config.py
# ============================================================================

print("⚙️ 2. VERIFICANDO config.py...")
print("-" * 80)

try:
    import config
    
    # Verificar peso D9
    peso_d9 = config.PESOS_DIMENSOES.get('D9')
    if peso_d9 == 0.10:
        ok.append(f"✅ Peso D9 = {peso_d9} (CORRETO)")
    elif peso_d9 == 0.03:
        erros.append(f"❌ Peso D9 = {peso_d9} (ANTIGO! Deveria ser 0.10)")
    else:
        avisos.append(f"⚠️ Peso D9 = {peso_d9} (Inesperado)")
    
    # Verificar total de cruzamentos
    total_cruz = len(config.CRUZAMENTOS)
    if total_cruz == 26:
        ok.append(f"✅ Total de cruzamentos: {total_cruz} (CORRETO)")
    elif total_cruz == 16:
        erros.append(f"❌ Total de cruzamentos: {total_cruz} (ANTIGO! Deveria ser 26)")
    else:
        avisos.append(f"⚠️ Total de cruzamentos: {total_cruz}")
    
    # Verificar se CR17-CR26 existem
    ids_cruzamentos = [c['id'] for c in config.CRUZAMENTOS]
    novos_ids = ['CR17', 'CR18', 'CR19', 'CR20', 'CR21', 'CR22', 'CR23', 'CR24', 'CR25', 'CR26']
    
    tem_novos = all(cid in ids_cruzamentos for cid in novos_ids)
    if tem_novos:
        ok.append("✅ Novos cruzamentos CR17-CR26 presentes")
    else:
        faltando = [cid for cid in novos_ids if cid not in ids_cruzamentos]
        erros.append(f"❌ Cruzamentos faltando: {', '.join(faltando)}")
    
except ImportError as e:
    erros.append(f"❌ Erro ao importar config.py: {e}")

print()

# ============================================================================
# 3. VERIFICAR perguntas.json
# ============================================================================

print("📋 3. VERIFICANDO ARQUIVO DE PERGUNTAS...")
print("-" * 80)

try:
    # Tentar carregar perguntas
    perguntas_file = None
    if os.path.exists('perguntas.json'):
        perguntas_file = 'perguntas.json'
    elif os.path.exists('perguntas_v4.1_LIMPO.json'):
        perguntas_file = 'perguntas_v4.1_LIMPO.json'
    
    if perguntas_file:
        with open(perguntas_file, 'r', encoding='utf-8') as f:
            perguntas_data = json.load(f)
        
        # Verificar se tem referências (não deveria ter em V4.1 LIMPO)
        tem_refs = False
        if 'dimensoes' in perguntas_data:
            for dim in perguntas_data['dimensoes']:
                if 'perguntas' in dim:
                    for perg in dim['perguntas']:
                        if 'referencia' in perg or 'embasamento' in perg or 'ies_que_usa' in perg:
                            tem_refs = True
                            break
        
        if tem_refs:
            avisos.append(f"⚠️ {perguntas_file} contém referências bibliográficas (versão antiga?)")
        else:
            ok.append(f"✅ {perguntas_file} SEM referências (LIMPO - correto)")
        
        # Contar perguntas
        total_perguntas = 0
        if 'dimensoes' in perguntas_data:
            for dim in perguntas_data['dimensoes']:
                if 'perguntas' in dim:
                    total_perguntas += len(dim['perguntas'])
        
        if total_perguntas == 44:
            ok.append(f"✅ Total de perguntas: {total_perguntas} (CORRETO)")
        else:
            avisos.append(f"⚠️ Total de perguntas: {total_perguntas} (Esperado: 44)")
    
except Exception as e:
    erros.append(f"❌ Erro ao ler perguntas: {e}")

print()

# ============================================================================
# 4. TESTAR IMPORTAÇÕES
# ============================================================================

print("🔧 4. TESTANDO IMPORTAÇÕES...")
print("-" * 80)

try:
    from avaliacao_docente_v4 import processar_avaliacao
    ok.append("✅ avaliacao_docente_v4.processar_avaliacao importado")
except ImportError as e:
    erros.append(f"❌ Erro ao importar avaliacao_docente_v4: {e}")

try:
    from util import carregar_perguntas
    ok.append("✅ util.carregar_perguntas importado")
except ImportError as e:
    erros.append(f"❌ Erro ao importar util: {e}")

try:
    from estilo import get_custom_css
    ok.append("✅ estilo.get_custom_css importado")
except ImportError as e:
    erros.append(f"❌ Erro ao importar estilo: {e}")

print()

# ============================================================================
# 5. RESULTADO FINAL
# ============================================================================

print("=" * 80)
print("RESULTADO DO TESTE")
print("=" * 80)
print()

if ok:
    print("✅ SUCESSOS:")
    for item in ok:
        print(f"   {item}")
    print()

if avisos:
    print("⚠️ AVISOS:")
    for item in avisos:
        print(f"   {item}")
    print()

if erros:
    print("❌ ERROS:")
    for item in erros:
        print(f"   {item}")
    print()

# Status final
print("=" * 80)
if erros:
    print("❌ TESTE FALHOU - Corrija os erros antes do deployment!")
    print("=" * 80)
    sys.exit(1)
elif avisos:
    print("⚠️ TESTE PASSOU COM AVISOS - Revise antes do deployment")
    print("=" * 80)
    sys.exit(0)
else:
    print("✅ TESTE PASSOU - Sistema pronto para deployment!")
    print("=" * 80)
    sys.exit(0)
