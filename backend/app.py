# -*- coding: utf-8 -*-
"""
Eco Sertão — backend Flask.

Endpoints:
    GET  /api/focos/atual            -> focos das últimas 48h (para o mapa)
    GET  /api/focos/historico?dias=N -> série diária de contagem (para o gráfico)
    GET  /api/focos/ranking?dias=N   -> top municípios com mais focos
    GET  /api/status                 -> info da última atualização
    POST /api/atualizar               -> força uma busca imediata no INPE

Local:     python app.py  ->  http://localhost:5000
Produção:  gunicorn app:app --workers 1 --threads 4 --bind 0.0.0.0:$PORT
"""

import logging
import os
import threading

from flask import Flask, jsonify, request, send_from_directory

import database
import scheduler
from config import DIAS_HISTORICO_GRAFICO, DIAS_BACKFILL_INICIAL

logging.basicConfig(level=logging.INFO)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")


# ---------- Frontend ----------

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


# ---------- API ----------

@app.route("/api/focos/atual")
def api_focos_atual():
    dias = request.args.get("dias", default=2, type=int)
    focos = database.focos_recentes(dias=dias)
    return jsonify(focos)


@app.route("/api/focos/historico")
def api_focos_historico():
    dias = request.args.get("dias", default=DIAS_HISTORICO_GRAFICO, type=int)
    return jsonify(database.historico_diario(dias=dias))


@app.route("/api/focos/ranking")
def api_focos_ranking():
    dias = request.args.get("dias", default=DIAS_HISTORICO_GRAFICO, type=int)
    limite = request.args.get("limite", default=10, type=int)
    return jsonify(database.ranking_municipios(dias=dias, limite=limite))


@app.route("/api/status")
def api_status():
    return jsonify({
        **scheduler.estado_atualizacao,
        "total_focos_no_banco": database.total_focos(),
    })


@app.route("/api/atualizar", methods=["POST"])
def api_atualizar():
    scheduler.atualizar_dados()
    return jsonify(scheduler.estado_atualizacao)


def _primeira_carga():
    """Roda em segundo plano na subida do servidor. Se o banco estiver
    vazio (primeiro deploy, ou disco efêmero reiniciado), baixa um
    período maior para o gráfico de tendência não abrir vazio."""
    if database.total_focos() == 0:
        scheduler.atualizar_dados(dias=DIAS_BACKFILL_INICIAL)
    else:
        scheduler.atualizar_dados()


def iniciar_tudo():
    database.inicializar_banco()
    # A busca inicial roda em thread para não atrasar a subida do
    # servidor (o Render derruba serviços que demoram a abrir a porta).
    threading.Thread(target=_primeira_carga, daemon=True).start()
    scheduler.iniciar_agendador()


# Executa ao importar o módulo: funciona tanto com `python app.py`
# quanto com gunicorn (que só importa `app` e nunca chama main()).
iniciar_tudo()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
