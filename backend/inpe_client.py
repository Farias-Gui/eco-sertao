# -*- coding: utf-8 -*-
"""
Cliente responsável por baixar o CSV diário de focos de queimada do
Programa Queimadas do INPE e filtrar apenas o que interessa ao projeto
(bioma Caatinga e estados monitorados).

Fonte oficial e gratuita, sem necessidade de treinar nenhum modelo de
IA: https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/diario/Brasil/
"""

import csv
import io
import logging
from datetime import datetime, timedelta, timezone

import requests

from config import (
    INPE_CSV_BASE_URL,
    BIOMA_ALVO,
    ESTADOS_MONITORADOS,
    DIAS_PARA_BAIXAR,
)

TIMEOUT_SEGUNDOS = 30

logger = logging.getLogger("eco_sertao.inpe")


def _url_do_dia(data: datetime) -> str:
    return f"{INPE_CSV_BASE_URL}/focos_diario_br_{data.strftime('%Y%m%d')}.csv"


def _linha_interessa(linha: dict) -> bool:
    bioma = (linha.get("bioma") or "").strip()
    estado = (linha.get("estado") or "").strip().upper()
    return bioma == BIOMA_ALVO or estado in ESTADOS_MONITORADOS


def _para_registro(linha: dict) -> dict:
    def _float_ou_none(valor):
        valor = (valor or "").strip()
        try:
            return float(valor)
        except ValueError:
            return None

    return {
        "id": linha.get("id"),
        "lat": _float_ou_none(linha.get("lat")),
        "lon": _float_ou_none(linha.get("lon")),
        "data_hora_gmt": linha.get("data_hora_gmt"),
        "satelite": linha.get("satelite"),
        "municipio": linha.get("municipio"),
        "estado": linha.get("estado"),
        "bioma": linha.get("bioma"),
        "dias_sem_chuva": linha.get("numero_dias_sem_chuva"),
        "precipitacao": linha.get("precipitacao"),
        "risco_fogo": linha.get("risco_fogo"),
        "frp": _float_ou_none(linha.get("frp")),
    }


def baixar_focos_do_dia(data: datetime) -> list[dict]:
    """Baixa o CSV de um dia específico e retorna apenas os focos do
    bioma/estados de interesse já convertidos para dicionários prontos
    para inserir no banco. Retorna lista vazia se o arquivo ainda não
    existir (comum para o dia corrente, publicado aos poucos)."""
    url = _url_do_dia(data)
    resposta = requests.get(url, timeout=TIMEOUT_SEGUNDOS)

    if resposta.status_code == 404:
        return []
    resposta.raise_for_status()

    resposta.encoding = "utf-8"
    leitor = csv.DictReader(io.StringIO(resposta.text))

    registros = []
    for linha in leitor:
        if _linha_interessa(linha):
            registro = _para_registro(linha)
            if registro["id"] and registro["lat"] is not None:
                registros.append(registro)
    return registros


def baixar_focos_recentes(dias: int = DIAS_PARA_BAIXAR) -> list[dict]:
    """Baixa e junta os focos dos últimos `dias` dias (hoje e dias
    anteriores), já filtrados por bioma/estado."""
    hoje = datetime.now(timezone.utc)
    todos = []
    falhas = 0
    ultimo_erro = None
    for offset in range(dias):
        dia = hoje - timedelta(days=offset)
        try:
            todos.extend(baixar_focos_do_dia(dia))
        except Exception as exc:  # noqa: BLE001 - um dia com erro não deve derrubar os outros
            falhas += 1
            ultimo_erro = exc
            logger.warning("Falha ao baixar %s: %s", dia.strftime("%Y-%m-%d"), exc)
    if falhas == dias and ultimo_erro is not None:
        raise ultimo_erro  # tudo falhou: deixa o agendador registrar o erro
    return todos
