"""Gatilhos do Azure Functions (modelo de programação v2).

Os gatilhos são finos: apenas adaptam a entrada do runtime e delegam aos adaptadores
em ``app.http``. Nenhuma regra de negócio fica aqui.
"""

import logging

import azure.functions as func

from app.http import tratar_evento, tratar_http
from app.negocio import executar_rotina_periodica

app = func.FunctionApp()

# Segunda função: roda a cada 5 minutos (NCRONTAB com seis campos).
AGENDA_TEMPORIZADOR = "0 */5 * * * *"


def _invocacao(context: "func.Context | None") -> str:
    """Retorna o id da invocação quando o runtime o fornece."""
    return getattr(context, "invocation_id", None) or "desconhecida"


@app.route(route="pedidos", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def pedidos_http(req: func.HttpRequest, context: func.Context = None) -> func.HttpResponse:
    resposta = tratar_http(req.get_body(), _invocacao(context), logging.getLogger("pedidos_http"))
    return func.HttpResponse(
        body=resposta.corpo,
        status_code=resposta.status,
        headers=resposta.cabecalhos,
    )


@app.timer_trigger(schedule=AGENDA_TEMPORIZADOR, arg_name="temporizador", run_on_startup=False)
def rotina_temporizador(temporizador: func.TimerRequest, context: func.Context = None) -> None:
    tratar_evento(
        temporizador,
        _invocacao(context),
        logging.getLogger("rotina_temporizador"),
        processar=executar_rotina_periodica,
    )
