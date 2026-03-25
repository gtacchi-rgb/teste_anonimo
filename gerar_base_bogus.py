#!/usr/bin/env python3
"""
Gerador de BASE_DISCENTES bogus para demonstração do sistema de Avaliação Docente.
Todos os dados são 100% fictícios. Nenhum dado real está presente.

Regras de geração:
- Alunos: entre 20-40, quantidade NÃO terminada em 0 ou 5 → escolhido 27
- Disciplinas por aluno: 3 a 11, média final = 8.5
- Discentes: músicos brasileiros famosos dos últimos 15 anos
- Docentes: atores de Hollywood muito famosos
- Matrículas: 2027MEC99XX (XX decrescente)
- SIAPEs: 999888XX-X (XX < 77, X > 5)
- Datas: feriados brasileiros com ano 2027
- CPF/RG: letras aleatórias
- Telefones: formato Hollywood (55)
- E-mails: nome.sobrenome@(inimigo do Superman).ext
"""

import csv, random, string, os

# ══════════════════════════════════════════════════════════════════════════════
# DADOS-FONTE PARA GERAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

# 27 músicos brasileiros famosos dos últimos 15 anos (nome artístico + sobrenome fictício)
MUSICOS = [
    ("Anitta", "Larissa Machado"),      ("Ludmilla", "Oliveira Santos"),
    ("IZA", "Arantes Pereira"),          ("Luisa", "Sonza Batista"),
    ("Jao", "Ferreira Lima"),            ("Silva", "Costa Ribeiro"),
    ("Liniker", "Barros Nascimento"),     ("Emicida", "Ramos Correia"),
    ("Criolo", "Vieira Souza"),          ("Projota", "Almeida Nunes"),
    ("Tiago", "Iorc Mendes"),            ("Marilia", "Donato Rocha"),
    ("Gloria", "Groove Martins"),         ("Xama", "Teixeira Gomes"),
    ("Rashid", "Freitas Araujo"),        ("Marina", "Sena Cavalcanti"),
    ("Baco", "Exu Cardoso"),             ("Djonga", "Pinto Barbosa"),
    ("Duda", "Beat Fernandes"),          ("Vitao", "Moreira Castro"),
    ("Lexa", "Duarte Fonseca"),          ("Pabllo", "Vittar Cunha"),
    ("Alok", "Ferraz Monteiro"),         ("Karol", "Conka Medeiros"),
    ("Majur", "Rezende Lopes"),          ("Rincon", "Sapiencia Dias"),
    ("Agnes", "Nunes Oliveira"),
]

# 10 atores de Hollywood (nome + SIAPE bogus)
ATORES = [
    ("TOM HANKS",            "99988812-6"),
    ("MERYL STREEP",         "99988823-7"),
    ("LEONARDO DICAPRIO",    "99988831-8"),
    ("DENZEL WASHINGTON",    "99988842-9"),
    ("CATE BLANCHETT",       "99988853-6"),
    ("BRAD PITT",            "99988864-7"),
    ("VIOLA DAVIS",          "99988875-8"),
    ("MORGAN FREEMAN",       "99988807-6"),
    ("NATALIE PORTMAN",      "99988819-9"),
    ("ROBERT DOWNEY JR",     "99988826-7"),
]

# 16 disciplinas reais do curso de Engenharia Química (código + nome + CH)
DISCIPLINAS = [
    ("G11QORG1.01", "QUIMICA ORGANICA",                          60, "T01"),
    ("G11QANA1.01", "QUIMICA ANALITICA",                         60, "T01"),
    ("G11QIEX1.01", "QUIMICA INORGANICA EXPERIMENTAL",           30, "P01"),
    ("G11FTRA1.01", "FENOMENOS DE TRANSPORTE I",                  60, "T01"),
    ("G11QOEX1.01", "QUIMICA ORGANICA EXPERIMENTAL",              30, "P01"),
    ("G11QAEX1.01", "QUIMICA ANALITICA EXPERIMENTAL",             30, "P01"),
    ("G11DTEC1.01", "DESENHO TECNICO",                            60, "T01"),
    ("G11OFTE1.01", "FUNDAMENTOS DE OFT",                         60, "T01"),
    ("G11QAMB1.01", "QUIMICA AMBIENTAL",                          60, "T01"),
    ("G11EDOR1.01", "EQUACOES DIFERENCIAIS ORDINARIAS",           60, "T01"),
    ("G11FEST1.01", "FUNDAMENTOS DE ESTATICA",                     60, "T01"),
    ("G11CFVR1.01", "CALCULO COM FUNCOES DE UMA VARIAVEL REAL",   90, "T01"),
    ("G11CFVV2.01", "CALCULO COM FUNCOES DE VARIAS VARIAVEIS II", 60, "T01"),
    ("G11FOFT1.01", "FISICA EXPERIMENTAL - OFT",                   30, "P01"),
    ("G11GAAL1.01", "GEOMETRIA ANALITICA E ALGEBRA LINEAR",       60, "T01"),
    ("G11FQEX1.01", "FISICO-QUIMICA EXPERIMENTAL",                30, "P01"),
]

# Feriados e datas comemorativas brasileiras (dia, mês)
FERIADOS = [
    (1,1),(20,1),(25,1),(4,3),(8,3),(21,4),(1,5),(12,6),(24,6),(29,6),
    (7,9),(12,10),(15,10),(2,11),(15,11),(20,11),(25,12),(31,12),
    (19,3),(23,4),(13,5),(15,8),(3,10),(28,10),(8,12),(13,6),(11,8),
]

# Inimigos do Superman para domínios de e-mail
VILOES = [
    "lexluthor","doomsday","brainiac","generalzod","darkseid",
    "bizarro","metallo","parasite","mongul","cyborg",
    "toyman","mxyzptlk","livewire","ultraman","lobo",
]
EXTS = ["org","net","com","xyz","dev","app","io","sci"]

# Cidades de MG e dados geográficos
CIDADES_MG = [
    ("Belo Horizonte","Central","MG"), ("Contagem","Central","MG"),
    ("Betim","Central","MG"), ("Ribeirao das Neves","Central","MG"),
    ("Santa Luzia","Central","MG"), ("Ibirite","Central","MG"),
    ("Sabara","Central","MG"), ("Nova Lima","Central","MG"),
    ("Vespasiano","Central","MG"), ("Lagoa Santa","Central","MG"),
    ("Sete Lagoas","Central","MG"), ("Divinopolis","Oeste","MG"),
    ("Governador Valadares","Leste","MG"), ("Juiz de Fora","Mata","MG"),
    ("Montes Claros","Norte","MG"), ("Uberlandia","Triangulo","MG"),
    ("Ouro Preto","Central","MG"), ("Mariana","Central","MG"),
]

HORARIOS = [
    "SEG/QUA 07:00-08:40", "SEG/QUA 08:50-10:30", "SEG/QUA 10:40-12:20",
    "TER/QUI 07:00-08:40", "TER/QUI 08:50-10:30", "TER/QUI 10:40-12:20",
    "SEG/QUA 13:00-14:40", "TER/QUI 13:00-14:40", "SEX 07:00-08:40",
    "SEG/QUA 19:00-20:40", "TER/QUI 19:00-20:40", "SEG/QUA 20:50-22:30",
]

TIPOS_ENTRADA = ["ENEM/SISU", "ENEM/SISU", "ENEM/SISU", "ENEM/SISU",
                  "TRANSFERENCIA", "OBTENTOR DE NOVO TITULO", "ENEM/SISU"]
QUALIF_ENTRADA = ["Ampla Concorrencia", "Cota Lei 12.711", "Ampla Concorrencia",
                   "Cota Lei 12.711", "Ampla Concorrencia"]
COTAS_ESCOLA = ["Nao", "Sim", "Nao", "Sim", "Nao", "Nao"]
COTAS_RENDA = ["Nao", "Nao", "Nao", "Sim", "Nao", "Nao"]
COTAS_ETNIA = ["Nao", "Nao", "Nao", "Nao", "Sim", "Nao"]
SITUACOES = ["MATRICULADO", "MATRICULADO", "MATRICULADO", "TRANCADO"]


# ══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES DE GERAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

def letras_aleatorias(n):
    return ''.join(random.choices(string.ascii_uppercase, k=n))

def cpf_bogus():
    l = letras_aleatorias(11)
    return f"{l[0:3]}.{l[3:6]}.{l[6:9]}-{l[9:11]}"

def rg_bogus():
    l = letras_aleatorias(9)
    return f"{l[0:2]}.{l[2:5]}.{l[5:8]}-{l[8]}"

def email_bogus(nome, sobrenome):
    n = nome.lower().replace("ã","a").replace("í","i").replace("ú","u").replace("é","e").replace("ó","o")
    s = sobrenome.split()[0].lower().replace("ã","a").replace("í","i")
    return f"{n}.{s}@{random.choice(VILOES)}.{random.choice(EXTS)}"

def distribuir_disciplinas(n_alunos, media_alvo=8.5, min_d=3, max_d=11):
    """
    Gera lista de quantidades de disciplinas por aluno,
    garantindo média próxima de 8.5 e valores entre 3 e 11.
    """
    total_alvo = round(n_alunos * media_alvo)
    
    # Iniciar com valores aleatórios
    qtds = [random.randint(min_d, max_d) for _ in range(n_alunos)]
    
    # Ajustar para atingir o total
    for _ in range(500):
        diff = sum(qtds) - total_alvo
        if diff == 0:
            break
        idx = random.randint(0, n_alunos - 1)
        if diff > 0 and qtds[idx] > min_d:
            qtds[idx] -= 1
        elif diff < 0 and qtds[idx] < max_d:
            qtds[idx] += 1
    
    return qtds


def gerar_base():
    N_ALUNOS = 27  # Entre 20-40, não termina em 0 nem 5
    
    # Matrículas com XX decrescentes
    xx_vals = sorted(random.sample(range(11, 99), N_ALUNOS), reverse=True)
    
    # Distribuir disciplinas (média 8.5)
    qtds_disc = distribuir_disciplinas(N_ALUNOS)
    
    registros = []
    periodos = [2, 3, 4, 5]  # Períodos disponíveis
    
    for i in range(N_ALUNOS):
        nome_art, sobrenome = MUSICOS[i]
        mat = f"2027MEC99{xx_vals[i]:02d}"
        discente = f"{nome_art.upper()} {sobrenome.upper()}"
        
        feriado = FERIADOS[i % len(FERIADOS)]
        data_nasc = f"{feriado[0]:02d}/{feriado[1]:02d}/2027"
        cpf = cpf_bogus()
        rg = rg_bogus()
        tel_fixo = f"(55) 5555-{random.randint(1000, 9999)}"
        tel_cel = f"(55) 99555-{random.randint(1000, 9999)}"
        email = email_bogus(nome_art, sobrenome)
        cidade, macro, uf = random.choice(CIDADES_MG)
        periodo = random.choice(periodos)
        entrada = f"2027/{random.choice([1,2])}"
        tipo_entrada = random.choice(TIPOS_ENTRADA)
        qualif = random.choice(QUALIF_ENTRADA)
        cota_esc = random.choice(COTAS_ESCOLA)
        cota_rend = random.choice(COTAS_RENDA)
        cota_etn = random.choice(COTAS_ETNIA)
        situacao = random.choice(SITUACOES)
        
        # Selecionar disciplinas para este aluno
        n_disc = qtds_disc[i]
        disc_sample = random.sample(DISCIPLINAS, min(n_disc, len(DISCIPLINAS)))
        
        for cod, nome_disc, ch, turma in disc_sample:
            prof_nome, prof_siape = random.choice(ATORES)
            horario = random.choice(HORARIOS)
            nota_parcial = round(random.uniform(0, 100), 1)
            matriculados = random.randint(15, 45)
            capacidade = random.choice([40, 45, 50])
            
            # CHAVE1: código + siape (sem matrícula!)
            chave1 = f"{cod}_{prof_siape[-4:]}"
            
            registros.append({
                "Matrícula": mat,
                "Discente": discente,
                "Entrada": entrada,
                "Período": periodo,
                "Código": cod,
                "Nome": nome_disc,
                "Turma": turma,
                "CH": ch,
                "CHAVE1": chave1,
                "Siape Prof": prof_siape,
                "Professor": prof_nome,
                "Horário": horario,
                "Nota": nota_parcial,
                "Matriculados": matriculados,
                "Capacidade": capacidade,
                "Situação": situacao,
                "TIPO DE ENTRADA": tipo_entrada,
                "QUALIFICAÇÃO DA ENTRADA": qualif,
                "COTA ESCOLA": cota_esc,
                "COTA RENDA": cota_rend,
                "COTA ETNIA": cota_etn,
                "Data de Nascimento": data_nasc,
                "CPF": cpf,
                "RG": rg,
                "Cidade Origem": cidade,
                "MACRORREGIÃO": macro,
                "UF": uf,
                "Telefone Fixo": tel_fixo,
                "Telefone Celular": tel_cel,
                "E-mail": email,
            })
    
    return registros, N_ALUNOS, qtds_disc


def main():
    registros, n_alunos, qtds = gerar_base()
    
    campos = [
        "Matrícula","Discente","Entrada","Período","Código","Nome","Turma",
        "CH","CHAVE1","Siape Prof","Professor","Horário","Nota",
        "Matriculados","Capacidade","Situação","TIPO DE ENTRADA",
        "QUALIFICAÇÃO DA ENTRADA","COTA ESCOLA","COTA RENDA","COTA ETNIA",
        "Data de Nascimento","CPF","RG","Cidade Origem","MACRORREGIÃO","UF",
        "Telefone Fixo","Telefone Celular","E-mail"
    ]
    
    output = "BASE_DISCENTES_BOGUS.csv"
    with open(output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(registros)
    
    media_real = len(registros) / n_alunos
    print(f"Base bogus gerada: {output}")
    print(f"  {n_alunos} alunos")
    print(f"  {len(registros)} registros")
    print(f"  Media: {media_real:.1f} disciplinas/aluno")
    print(f"  Distribuicao: {sorted(qtds)}")
    print(f"  Min: {min(qtds)}, Max: {max(qtds)}")


if __name__ == "__main__":
    main()
