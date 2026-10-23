# -*- coding: utf-8 -*-
"""
Agendador que roda em segundo plano dentro do próprio processo Flask,
buscando dados novos do INPE periodicamente — sem precisar de um
serviço externo (cron, Celery etc.), o que mantém o projeto simples
o bastante para rodar em qualquer máquina do grupo.
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler

import database
import inpe_client
from config import INTERVALO_ATUALIZACAO_HORAS

logger = logging.getLogger("eco_sertao.scheduler")

# Guarda o último total conhecido de focos para permitir que o
# frontend detecte "aumento" e decida notificar o usuário.
estado_atualizacao = {
    "ultima_atualizacao": None,
    "novos_focos_na_ultima_rodada": 0,
    "erro": None,
}


def atualizar_dados(dias=None):
    from datetime import datetime, timezone

    try:
        if dias:
            focos = inpe_client.baixar_focos_recentes(dias)
        else:
            focos = inpe_client.baixar_focos_recentes()
        inseridos = database.inserir_focos(focos)
        estado_atualizacao["ultima_atualizacao"] = datetime.now(timezone.utc).isoformat()
        estado_atualizacao["novos_focos_na_ultima_rodada"] = inseridos
        estado_atualizacao["erro"] = None
        logger.info("Atualização concluída: %s focos novos inseridos.", inseridos)
    except Exception as exc:  # noqa: BLE001 - queremos logar qualquer falha de rede/parse
        estado_atualizacao["erro"] = str(exc)
        logger.exception("Falha ao atualizar dados do INPE.")


def iniciar_agendador() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        atualizar_dados,
        "interval",
        hours=INTERVALO_ATUALIZACAO_HORAS,
        id="atualizacao_inpe",
    )
    scheduler.start()
    return scheduler
