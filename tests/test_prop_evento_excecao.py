"""Teste de propriedade para exceção em função não HTTP (temporizador/fila/blob)."""

import logging

import pytest
from hypothesis import given, settings, strategies as st

from app.http import FUNCAO_EVENTO, tratar_evento
from app.logging_seguro import redigir

_TIPOS_EXCECAO = [
    Exception,
    RuntimeError,
    ValueError,
    KeyError,
    PermissionError,
    ConnectionError,
    TimeoutError,
    OSError,
]

_mensagens = st.text(min_size=0, max_size=60)
_invocacoes = st.text(alphabet="abcdef0123456789-", min_size=1, max_size=36)
# Alfabeto disjunto do de ``_invocacoes`` para que a redação do payload não altere a invocação.
_texto_payload = st.text(alphabet="XYZ", max_size=30)
_payloads = st.one_of(
    st.none(), _texto_payload, _texto_payload.map(str.encode), st.integers(), st.just(object())
)


class _LogCapturado(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.DEBUG)
        self.registros = []

    def emit(self, record):
        self.registros.append(record)


# Feature: serverless-ai-agent-azure-functions, Property 7: Exceção em função não HTTP é registrada e propagada
# **Validates: Requirements 4.6**
@settings(max_examples=100, deadline=None)
@given(
    tipo=st.sampled_from(_TIPOS_EXCECAO),
    mensagem=_mensagens,
    invocacao=_invocacoes,
    payload=_payloads,
)
def test_excecao_em_evento_e_registrada_e_propagada(tipo, mensagem, invocacao, payload):
    excecao = tipo(mensagem)

    def processar(_):
        raise excecao

    logger = logging.getLogger("teste.evento.excecao")
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    handler = _LogCapturado()
    logger.addHandler(handler)
    try:
        with pytest.raises(BaseException) as info:
            tratar_evento(payload, invocacao, logger, processar=processar)
    finally:
        logger.removeHandler(handler)

    # Relança a mesma instância.
    assert info.value is excecao

    # Registra exatamente um erro com funcao, invocacao, tipo_excecao e mensagem.
    assert len(handler.registros) == 1
    registro = handler.registros[0]
    assert registro.levelno == logging.ERROR
    texto = registro.getMessage()
    assert f"funcao={FUNCAO_EVENTO}" in texto
    assert "invocacao=" in texto
    assert f"tipo_excecao={tipo.__name__}" in texto
    assert "mensagem=" in texto
    assert registro.args[0] == FUNCAO_EVENTO
    assert registro.args[1] == redigir(invocacao)
    assert registro.args[2] == tipo.__name__
