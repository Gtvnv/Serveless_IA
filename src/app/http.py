"""Adaptadores de gatilhos: mapeiam o resultado da lógica de negócio para HTTP.

Sem dependência do runtime do Azure Functions.
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass, field
from typing import Any, Callable

from app.logging_seguro import registrar_erro
from app.negocio import processar_pedido
from app.validacao import validar_pedido

FUNCAO_HTTP = "tratar_http"
FUNCAO_EVENTO = "tratar_evento"
CONTENT_TYPE_JSON = "application/json"
MENSAGEM_ERRO_GENERICO = "Erro interno. Tente novamente mais tarde."
MENSAGEM_CORPO_EXCEDIDO = "O corpo da requisição excede 1 MB."


@dataclass(frozen=True)
class RespostaHttp:
    status: int
    corpo: str
    cabecalhos: dict = field(default_factory=lambda: {"Content-Type": CONTENT_TYPE_JSON})


def _resposta_json(status: int, dados: Any) -> RespostaHttp:
    return RespostaHttp(
        status=status,
        corpo=json.dumps(dados, ensure_ascii=False),
        cabecalhos={"Content-Type": CONTENT_TYPE_JSON},
    )


def _coletar_textos(valor: Any, destino: list[str], profundidade: int = 0) -> None:
    """Coleta todos os textos (chaves e valores) de uma estrutura JSON para redação."""
    if profundidade > 20:
        return
    if isinstance(valor, str):
        if valor:
            destino.append(valor)
    elif isinstance(valor, dict):
        for k, v in valor.items():
            _coletar_textos(k, destino, profundidade + 1)
            _coletar_textos(v, destino, profundidade + 1)
    elif isinstance(valor, (list, tuple)):
        for item in valor:
            _coletar_textos(item, destino, profundidade + 1)


def _valores_sensiveis(payload: Any) -> tuple[str, ...]:
    """Extrai valores do pedido que devem ser removidos dos logs. Nunca lança exceção."""
    try:
        textos: list[str] = []
        dados = payload
        if isinstance(payload, (bytes, bytearray)):
            texto = bytes(payload).decode("utf-8", errors="replace")
            textos.append(texto)
            dados = json.loads(texto)
        elif isinstance(payload, str):
            textos.append(payload)
            dados = json.loads(payload)
        elif dataclasses.is_dataclass(payload) and not isinstance(payload, type):
            dados = dataclasses.asdict(payload)
        _coletar_textos(dados, textos)
        return tuple(dict.fromkeys(textos))
    except Exception:  # noqa: BLE001 - corpo malformado: usa apenas o que foi coletado
        try:
            if isinstance(payload, (bytes, bytearray)):
                return (bytes(payload).decode("utf-8", errors="replace"),)
            if isinstance(payload, str):
                return (payload,)
        except Exception:  # noqa: BLE001
            pass
        return ()


def tratar_http(
    req_corpo: bytes,
    invocacao: str,
    logger,
    processar: Callable = processar_pedido,
) -> RespostaHttp:
    """Valida o corpo, chama ``processar`` e mapeia o resultado para HTTP (413/400/200/500)."""
    try:
        resultado = validar_pedido(req_corpo)

        if resultado.corpo_excedido:
            return _resposta_json(413, {"erro": MENSAGEM_CORPO_EXCEDIDO})

        if not resultado.valido:
            return _resposta_json(
                400,
                {"erros": [{"campo": e.campo, "motivo": e.motivo} for e in resultado.erros]},
            )

        saida = processar(resultado.entrada)
        return _resposta_json(200, dataclasses.asdict(saida))
    except Exception as exc:  # noqa: BLE001 - qualquer falha vira 500 genérico
        registrar_erro(logger, FUNCAO_HTTP, invocacao, exc, _valores_sensiveis(req_corpo))
        return _resposta_json(500, {"erro": MENSAGEM_ERRO_GENERICO})


def tratar_evento(
    payload: Any,
    invocacao: str,
    logger,
    processar: Callable = processar_pedido,
) -> None:
    """Executa ``processar`` para um evento (temporizador, fila ou blob).

    Em caso de exceção, registra o erro estruturado e relança a exceção original.
    """
    try:
        processar(payload)
    except Exception as exc:
        registrar_erro(logger, FUNCAO_EVENTO, invocacao, exc, _valores_sensiveis(payload))
        raise
