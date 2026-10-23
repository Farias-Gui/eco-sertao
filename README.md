# Eco Sertão

App web de monitoramento de queimadas na Caatinga, usando dados reais e
gratuitos do **Programa Queimadas do INPE** (BDQueimadas) — sem
necessidade de treinar nenhum modelo de IA.

## Stack escolhida (e por quê)

| Camada       | Tecnologia                  | Motivo |
|--------------|------------------------------|--------|
| Backend      | Python + Flask               | Você já usa Python; Flask é leve, sem a complexidade de Django, e ótimo para expor uma API simples. |
| Dados        | SQLite                       | Banco em arquivo único, sem servidor para instalar — roda em qualquer notebook do grupo. |
| Agendamento  | APScheduler                  | Busca dados novos do INPE automaticamente, dentro do próprio processo Python, sem precisar de cron. |
| Frontend     | HTML + CSS + JavaScript puro | Você já usa HTML; sem necessidade de build (Webpack, npm install pesado) para apresentar o projeto. |
| Mapa         | Leaflet.js (arquivo local em `frontend/vendor/`) | Biblioteca de mapas leve; embutida no projeto para não depender de CDN externo (algumas redes de escola bloqueiam isso). |
| Gráfico      | Chart.js (arquivo local em `frontend/vendor/`)   | Gráfico de tendência histórica; também embutido pelo mesmo motivo. |
| Notificações | Web Notifications API         | Nativa do navegador, não exige backend de push nem configuração extra. |

## Como rodar

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Depois abra **http://localhost:5000** no navegador.

Na primeira execução, o app já baixa os focos dos últimos 2 dias do
INPE automaticamente. A partir daí, atualiza sozinho a cada 3 horas
(configurável em `backend/config.py`).

## Estrutura do projeto

```
eco-sertao/
├── backend/
│   ├── app.py           # rotas da API e servidor Flask
│   ├── config.py        # bioma/estados monitorados, intervalos
│   ├── database.py      # schema e consultas SQLite
│   ├── inpe_client.py   # baixa e filtra o CSV diário do INPE
│   ├── scheduler.py     # atualização automática em background
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── css/style.css
    └── js/app.js         # mapa, gráfico, ranking, notificações
```

## Fonte dos dados

Os focos vêm diretamente do arquivo CSV diário público do INPE:
`https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/diario/Brasil/`

O app filtra automaticamente apenas os focos do bioma **Caatinga** e
dos estados do Nordeste + Minas Gerais (onde a Caatinga também
ocorre). Isso é configurável em `backend/config.py`.

## Ideias para evoluir (se sobrar tempo até a apresentação)

- **Filtro por município**: adicionar um campo de busca no frontend.
- **Exportar relatório**: botão para baixar um PDF/CSV do período
  selecionado (dá pra reaproveitar a skill de PDF que já usamos em
  outros trabalhos).
- **Deploy simples**: publicar no PythonAnywhere ou Render para o
  professor acessar sem precisar instalar nada.
- **Comparar com chuva**: cruzar `numero_dias_sem_chuva` com o risco
  de fogo num segundo gráfico.


## Publicar na internet (Render, grátis)

1. Suba esta pasta para um repositório no GitHub (`backend/` e `frontend/` lado a lado na raiz).
2. Em https://render.com, entre com o GitHub e clique em **New → Blueprint**, escolhendo o repositório.
   O arquivo `render.yaml` já traz toda a configuração. Clique em **Apply**.
3. Em alguns minutos o site fica em `https://eco-sertao.onrender.com` (ou similar).

Configuração manual (se preferir não usar o Blueprint): Root Directory `backend`,
Build `pip install -r requirements.txt`, Start
`gunicorn app:app --workers 1 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT`.

**Limitações do plano grátis**
- O serviço dorme após ~15 min sem acesso; o primeiro acesso depois disso leva ~30-60 s.
  Abra o link alguns minutos antes de apresentar.
- O disco é efêmero: o SQLite é recriado a cada reinício. Por isso, com o banco vazio, o app
  baixa os últimos 30 dias do INPE (`DIAS_BACKFILL_INICIAL` em `config.py`) e o gráfico enche
  em ~1 minuto após acordar.
- Mantenha `--workers 1`: o agendador roda dentro do processo.
