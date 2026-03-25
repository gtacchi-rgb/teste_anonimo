"""
Configurações do Sistema de Avaliação Docente V4.0
CEFET-MG Engenharia Química

Contém todos os pesos, cruzamentos e configurações do sistema
"""

# ============================================================================
# INFORMAÇÕES DO SISTEMA
# ============================================================================

VERSAO = "4.0"
DATA = "2026-03-01"
INSTITUICAO = "CEFET-MG"
CURSO = "Engenharia Química"
CAMPUS = "Contagem"

# ============================================================================
# PESOS DAS DIMENSÕES (V4.0 - Mantidos da solicitação do usuário)
# ============================================================================

PESOS_DIMENSOES = {
    'D1': 0.00,  # Autoavaliação (Calibrador, não pontuado)
    'D2': 0.19,  # Organização e Clareza (reduzido de 0.22)
    'D3': 0.18,  # Didático-Pedagógico (reduzido de 0.20)
    'D4': 0.13,  # Métodos e Recursos (mantido)
    'D5': 0.15,  # Avaliação e Retorno (reduzido de 0.17)
    'D6': 0.11,  # Relacionamento (mantido)
    'D7': 0.07,  # Entusiasmo (mantido)
    'D8': 0.07,  # Perspectiva EQ (mantido)
    'D9': 0.10,  # Global (AUMENTADO de 0.03 para 0.10) ⭐
}

NOMES_DIMENSOES = {
    'D1': 'Autoavaliação do Estudante',
    'D2': 'Organização, Clareza e Profissionalismo',
    'D3': 'Desempenho Didático-Pedagógico',
    'D4': 'Métodos e Recursos Didáticos',
    'D5': 'Critérios de Avaliação e Retorno',
    'D6': 'Relacionamento, Interação e Suporte',
    'D7': 'Entusiasmo, Conhecimento e Inovação',
    'D8': 'Perspectiva e Conexão com a Engenharia Química',
    'D9': 'Avaliação Global',
}

# ============================================================================
# PESOS DAS PERGUNTAS DENTRO DE CADA DIMENSÃO
# ============================================================================

PESOS_PERGUNTAS = {
    # D1 - Autoavaliação (para cálculo de engajamento)
    'Q001': 0.20,  # Presença
    'Q002': 0.10,  # Base prévia
    'Q003': 0.15,  # Entregas
    'Q004': 0.20,  # Rotina
    'Q005': 0.10,  # Busca ajuda
    'Q006': 0.15,  # Participação
    'Q007': 0.10,  # Locus controle
    
    # D2 - Organização e Clareza
    'Q008': 0.30,  # Explicações claras
    'Q009': 0.25,  # Sequência lógica
    'Q010': 0.20,  # Objetivos claros
    'Q011': 0.15,  # Materiais organizados
    'Q012': 0.10,  # Comunicação mudanças
    
    # D3 - Didático-Pedagógico
    'Q013': 0.35,  # Domínio completo
    'Q014': 0.30,  # Explica porquês
    'Q015': 0.20,  # Exemplos práticos
    'Q016': 0.15,  # Rigor justo
    
    # D4 - Métodos e Recursos
    'Q017': 0.30,  # Material de qualidade
    'Q018': 0.30,  # Exemplos práticos/reais
    'Q019': 0.20,  # Práticas inovadoras
    'Q020': 0.20,  # Recursos de apoio
    
    # D5 - Avaliação e Retorno (todas iguais - todas críticas)
    'Q021': 0.25,  # Coerência
    'Q022': 0.25,  # Justiça
    'Q023': 0.25,  # Critérios claros
    'Q024': 0.25,  # Feedback útil
    
    # D6 - Relacionamento
    'Q025': 0.30,  # Acessível
    'Q026': 0.25,  # Respeitoso
    'Q027': 0.25,  # Ambiente respeitoso
    'Q028': 0.10,  # Pontualidade
    'Q029': 0.10,  # Comunicação
    
    # D7 - Entusiasmo
    'Q030': 0.40,  # Entusiasmo
    'Q031': 0.35,  # Mantém interesse
    'Q032': 0.25,  # Atualizado
    
    # D8 - Perspectiva EQ
    'Q033': 0.35,  # Conexões interdisciplinares
    'Q034': 0.35,  # Aprendizado valioso
    'Q035': 0.30,  # Visão ampliada
    
    # D9 - Global
    'Q036': 0.20,  # Recomendaria (NPS)
    'Q037': 0.25,  # Nota geral
    'Q038': 0.15,  # Dificuldade
    'Q039': 0.20,  # Vs outros do curso
    'Q040': 0.15,  # Vs outros do período
    'Q041': 0.05,  # Interesse aumentou
}

# ============================================================================
# MAPEAMENTO: PERGUNTAS → DIMENSÕES
# ============================================================================

PERGUNTAS_POR_DIMENSAO = {
    'D1': ['Q001', 'Q002', 'Q003', 'Q004', 'Q005', 'Q006', 'Q007'],
    'D2': ['Q008', 'Q009', 'Q010', 'Q011', 'Q012'],
    'D3': ['Q013', 'Q014', 'Q015', 'Q016'],
    'D4': ['Q017', 'Q018', 'Q019', 'Q020'],
    'D5': ['Q021', 'Q022', 'Q023', 'Q024'],
    'D6': ['Q025', 'Q026', 'Q027', 'Q028', 'Q029'],
    'D7': ['Q030', 'Q031', 'Q032'],
    'D8': ['Q033', 'Q034', 'Q035'],
    'D9': ['Q036', 'Q037', 'Q038', 'Q039', 'Q040', 'Q041'],
}

# ============================================================================
# ESCALAS DE RESPOSTA
# ============================================================================

ESCALA_LIKERT = {
    1: "Discordo Totalmente",
    2: "Discordo",
    3: "Neutro / Não se aplica",
    4: "Concordo",
    5: "Concordo Totalmente"
}

# ============================================================================
# CATEGORIAS DE NOTA FINAL
# ============================================================================

CATEGORIAS_NOTA = {
    'EXCELENTE': {'min': 8.5, 'max': 10.0, 'cor': '#00C853', 'emoji': '⭐⭐⭐⭐⭐'},
    'MUITO BOM': {'min': 7.0, 'max': 8.5, 'cor': '#64DD17', 'emoji': '⭐⭐⭐⭐'},
    'BOM': {'min': 5.5, 'max': 7.0, 'cor': '#FFB300', 'emoji': '⭐⭐⭐'},
    'REGULAR': {'min': 4.0, 'max': 5.5, 'cor': '#FF6F00', 'emoji': '⭐⭐'},
    'INSUFICIENTE': {'min': 1.0, 'max': 4.0, 'cor': '#D32F2F', 'emoji': '⭐'},
}

CATEGORIAS_ENGAJAMENTO = {
    'ALTO': {'min': 7.0, 'max': 10.0, 'cor': '#00C853'},
    'MÉDIO': {'min': 5.0, 'max': 7.0, 'cor': '#FFB300'},
    'MODERADO BAIXO': {'min': 3.0, 'max': 5.0, 'cor': '#FF6F00'},
    'CRÍTICO BAIXO': {'min': 1.0, 'max': 3.0, 'cor': '#D32F2F'},
}

# ============================================================================
# CONFIGURAÇÃO DOS 16 CRUZAMENTOS
# ============================================================================

CRUZAMENTOS = [
    # ========================================================================
    # CRUZAMENTOS ORIGINAIS (CR01-CR16)
    # ========================================================================
    {
        'id': 'CR01',
        'nome': 'Exposição Mínima',
        'descricao': 'Presença baixa reduz validade da observação',
        'severidade': 'ALTA',
        'cor': '#D32F2F',
        'ativo': True,
    },
    {
        'id': 'CR02',
        'nome': 'Engajamento Composto',
        'descricao': 'Baixo engajamento aumenta risco de avaliação reativa',
        'severidade': 'MÉDIA',
        'cor': '#FF6F00',
        'ativo': True,
    },
    {
        'id': 'CR03',
        'nome': 'Conhecimento Prévio × Dificuldade',
        'descricao': 'Evita penalizar docente quando dificuldade é por base fraca',
        'severidade': 'MÉDIA',
        'cor': '#FF6F00',
        'ativo': True,
    },
    {
        'id': 'CR04',
        'nome': 'Integridade Acadêmica',
        'descricao': 'Risco de resposta reativa por frustração',
        'severidade': 'MÉDIA',
        'cor': '#FF6F00',
        'ativo': True,
    },
    {
        'id': 'CR05',
        'nome': 'Clareza vs Halo Global',
        'descricao': 'Controla efeito halo/contágio de simpatia',
        'severidade': 'MÉDIA',
        'cor': '#FF6F00',
        'ativo': True,
    },
    {
        'id': 'CR06',
        'nome': 'Alinhamento Construtivo',
        'descricao': 'Quando objetivos claros, incoerência avaliativa é grave',
        'severidade': 'DIAGNÓSTICO',
        'cor': '#2196F3',
        'ativo': True,
    },
    {
        'id': 'CR07',
        'nome': 'Rigor sem Injustiça',
        'descricao': 'Protege professor exigente mas justo',
        'severidade': 'PROTEÇÃO+',
        'cor': '#00C853',
        'ativo': True,
    },
    {
        'id': 'CR08',
        'nome': 'Organização de Materiais',
        'descricao': 'Quando organização falha, apoio vira sinal forte',
        'severidade': 'DIAGNÓSTICO',
        'cor': '#2196F3',
        'ativo': True,
    },
    {
        'id': 'CR09',
        'nome': 'Suporte Disponível vs Uso',
        'descricao': 'Se não busca ajuda, críticas têm menor peso causal',
        'severidade': 'CALIBRAÇÃO',
        'cor': '#9C27B0',
        'ativo': True,
    },
    {
        'id': 'CR10',
        'nome': 'Clima de Sala e Participação',
        'descricao': 'Clima ruim explica baixa participação',
        'severidade': 'CALIBRAÇÃO',
        'cor': '#9C27B0',
        'ativo': True,
    },
    {
        'id': 'CR11',
        'nome': 'Teoria–Prática',
        'descricao': 'Exemplos relevantes fortalecem valor percebido',
        'severidade': 'REFORÇO+',
        'cor': '#00C853',
        'ativo': True,
    },
    {
        'id': 'CR12',
        'nome': 'Inovação com Carga Cognitiva',
        'descricao': 'Inovação sem estrutura eleva carga cognitiva',
        'severidade': 'ALERTA',
        'cor': '#F57C00',
        'ativo': True,
    },
    {
        'id': 'CR13',
        'nome': 'Atualização com Perspectiva',
        'descricao': 'Atualização só agrega quando conectada a contexto',
        'severidade': 'CALIBRAÇÃO',
        'cor': '#9C27B0',
        'ativo': True,
    },
    {
        'id': 'CR14',
        'nome': 'Pontualidade e Organização',
        'descricao': 'Problemas operacionais afetam percepção',
        'severidade': 'PROTEÇÃO',
        'cor': '#00C853',
        'ativo': True,
    },
    {
        'id': 'CR15',
        'nome': 'Comparativos vs Nota Absoluta',
        'descricao': 'Comparativos sofrem forte efeito de contraste',
        'severidade': 'CALIBRAÇÃO',
        'cor': '#9C27B0',
        'ativo': True,
    },
    {
        'id': 'CR16',
        'nome': 'Abertas Obrigatórias em Extremos',
        'descricao': 'Avaliações extremas precisam evidências qualitativas',
        'severidade': 'VALIDAÇÃO',
        'cor': '#FF9800',
        'ativo': True,
    },
    
    # ========================================================================
    # CRUZAMENTOS NOVOS V4.1 (CR17-CR26)
    # ========================================================================
    {
        'id': 'CR17',
        'nome': 'Sobrecarga Cognitiva vs Tempo',
        'descricao': 'Disciplina difícil + sem preparação pode ser sobrecarga real',
        'severidade': 'DIAGNÓSTICO',
        'cor': '#2196F3',
        'ativo': True,
    },
    {
        'id': 'CR18',
        'nome': 'Pré-requisitos Não Atendidos',
        'descricao': 'Base insuficiente + muito difícil = problema de pré-requisito',
        'severidade': 'CALIBRAÇÃO',
        'cor': '#9C27B0',
        'ativo': True,
    },
    {
        'id': 'CR19',
        'nome': 'Carga Horária Percebida Excessiva',
        'descricao': 'Aluno dedicado mas perde interesse = carga excessiva?',
        'severidade': 'ALERTA',
        'cor': '#F57C00',
        'ativo': True,
    },
    {
        'id': 'CR20',
        'nome': 'Feedback Qualitativo Rico',
        'descricao': 'Respostas abertas detalhadas = atenção e reflexão genuína',
        'severidade': 'VALIDAÇÃO+',
        'cor': '#00C853',
        'ativo': True,
    },
    {
        'id': 'CR21',
        'nome': 'Consistência Interna D2-D3-D4',
        'descricao': 'Dimensões correlatas não devem ter discrepância >2.5',
        'severidade': 'VALIDAÇÃO',
        'cor': '#FF9800',
        'ativo': True,
    },
    {
        'id': 'CR22',
        'nome': 'Locus de Controle Externo',
        'descricao': 'Atribui desempenho a fatores externos = viés reativo',
        'severidade': 'CALIBRAÇÃO',
        'cor': '#9C27B0',
        'ativo': True,
    },
    {
        'id': 'CR23',
        'nome': 'Viés de Recenticidade',
        'descricao': 'Perguntas finais podem refletir apenas últimas semanas',
        'severidade': 'ALERTA',
        'cor': '#F57C00',
        'ativo': True,
    },
    {
        'id': 'CR24',
        'nome': 'Expectativa Disciplina Prática vs Teórica',
        'descricao': 'Exemplos bons mas não vê valor = expectativa desalinhada',
        'severidade': 'CALIBRAÇÃO',
        'cor': '#9C27B0',
        'ativo': True,
    },
    {
        'id': 'CR25',
        'nome': 'Comparação com Média da Turma',
        'descricao': 'Avaliação muito discrepante da média = caso atípico',
        'severidade': 'VALIDAÇÃO',
        'cor': '#FF9800',
        'ativo': False,  # Requer agregação - implementar depois
    },
    {
        'id': 'CR26',
        'nome': 'Resposta Central Excessiva',
        'descricao': 'Excesso de Neutro sugere falta de reflexão',
        'severidade': 'ALERTA',
        'cor': '#F57C00',
        'ativo': True,
    },
]

# ============================================================================
# CONFIGURAÇÕES DE CONFIABILIDADE
# ============================================================================

CONFIABILIDADE_CONFIG = {
    'engajamento_critico': {'limite': 3.0, 'penalizacao': 30},
    'engajamento_baixo': {'limite': 5.0, 'penalizacao': 15},
    'presenca_baixa': {'limite': 2, 'penalizacao': 25},
    'multiplos_cruzamentos': {'quantidade': 4, 'penalizacao': 20},
    'straight_lining': {'variancia_minima': 0.3, 'penalizacao': 25},
    'extremos': {'penalizacao': 10},
}

NIVEIS_CONFIABILIDADE = {
    'ALTA': {'min': 80, 'max': 100, 'cor': '#00C853'},
    'MODERADA': {'min': 60, 'max': 80, 'cor': '#FFB300'},
    'BAIXA': {'min': 40, 'max': 60, 'cor': '#FF6F00'},
    'CRÍTICA': {'min': 0, 'max': 40, 'cor': '#D32F2F'},
}

# ============================================================================
# CONFIGURAÇÕES DA INTERFACE
# ============================================================================

APP_CONFIG = {
    'titulo': 'Sistema de Avaliação Docente V4.0',
    'subtitulo': 'CEFET-MG Engenharia Química',
    'icone': '📊',
    'layout': 'wide',
    'tema': 'light',
    'barra_progresso': True,
    'modo_debug': False,
}

# ============================================================================
# TEXTOS E MENSAGENS
# ============================================================================

MENSAGENS = {
    'boas_vindas': """
    ## 👋 Bem-vindo(a) ao Sistema de Avaliação Docente!
    
    Este questionário nos ajuda a melhorar continuamente a qualidade do ensino. 
    Suas respostas são **anônimas** e serão usadas apenas para fins de melhoria institucional.
    
    **Tempo estimado:** 10-15 minutos
    """,
    
    'instrucoes': """
    ### 📋 Instruções:
    
    1. Responda com honestidade - não há respostas certas ou erradas
    2. Considere toda a experiência do semestre
    3. Use "Neutro" apenas se realmente não conseguir avaliar
    4. Suas respostas abertas são muito valiosas!
    """,
    
    'finalizacao': """
    ## ✅ Avaliação Concluída!
    
    Obrigado por dedicar seu tempo para avaliar esta disciplina.
    Seu feedback é fundamental para a melhoria contínua do curso.
    """,
    
    'processando': '⏳ Processando suas respostas e calculando resultados...',
    
    'erro_validacao': """
    ⚠️ **Atenção:** Algumas respostas obrigatórias estão faltando.
    Por favor, complete todas as perguntas marcadas com *.
    """,
}

# ============================================================================
# CONFIGURAÇÕES DE EXPORTAÇÃO
# ============================================================================

EXPORT_CONFIG = {
    'formatos': ['JSON', 'CSV', 'Excel', 'PDF'],
    'incluir_timestamp': True,
    'incluir_metadata': True,
    'compactar': False,
}
