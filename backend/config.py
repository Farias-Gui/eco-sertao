# -*- coding: utf-8 -*-
"""
Configurações do Eco Sertão.

Ajuste os valores abaixo conforme a necessidade do grupo (por exemplo,
para focar em outro estado ou bioma).
"""

import os

# URL base dos dados abertos do INPE (Programa Queimadas / BDQueimadas).
# O arquivo do dia é publicado no formato focos_diario_br_AAAAMMDD.csv
INPE_CSV_BASE_URL = (
    "https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/diario/Brasil"
)

# Bioma principal do projeto (Caatinga e Tecnologia).
BIOMA_ALVO = "Caatinga"

# Estados que também queremos acompanhar mesmo fora do polígono estrito
# do bioma Caatinga (ela se estende por vários estados do Nordeste/MG).
ESTADOS_MONITORADOS = [
    "BAHIA",
    "PERNAMBUCO",
    "PIAUÍ",
    "CEARÁ",
    "PARAÍBA",
    "RIO GRANDE DO NORTE",
    "ALAGOAS",
    "SERGIPE",
    "MINAS GERAIS",
]

# Caminho do banco SQLite (fica ao lado deste arquivo).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "eco_sertao.db"))

# De quantas em quantas horas o app tenta buscar dados novos no INPE.
# O INPE atualiza o arquivo diário várias vezes ao dia; 3 em 3 horas é
# um intervalo seguro e alinhado ao ciclo de atualização de satélites.
INTERVALO_ATUALIZACAO_HORAS = 3

# Quantos dias para trás baixar ao atualizar (cobre o caso de o arquivo
# do dia atual ainda estar incompleto ou o servidor ter atrasado).
DIAS_PARA_BAIXAR = 2

# Quantos dias de histórico manter no gráfico de tendência.
DIAS_HISTORICO_GRAFICO = 30

# Na primeira subida com o banco vazio (ex.: primeiro deploy), quantos
# dias baixar de uma vez para o gráfico de tendência já abrir preenchido.
DIAS_BACKFILL_INICIAL = 30
