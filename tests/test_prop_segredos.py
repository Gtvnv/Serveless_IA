"""Teste de propriedade para falha no Key Vault."""

import logging

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from app.segredos import obter_segredo

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

_nomes = st.text(min_size=1, max_size=40)
_valores = st.text(alphabet="0123456789abcdef", min_size=16, max_size=32).map(
    lambda s: "VALOR-SECRETO-" + s
)


class _ClienteFalho:
    def __init__(self, exc):
        self._exc = exc

    def get_secret(self, nome):
        raise self._exc


# Feature: serverless-ai-agent-azure-functions, Property 9: Falha no Key Vault recusa a operação sem valor padrão
# **Validates: Requirements 8.9**
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    tipo=st.sampled_from(_TIPOS_EXCECAO),
    nome=_nomes,
    valor=_valores,
)
def test_falha_key_vault_propaga_sem_vazar_valor(tipo, nome, valor, caplog):
    caplog.clear()
    exc = tipo(f"falha ao ler segredo (valor={valor})")
    resultado = None

    with caplog.at_level(logging.DEBUG):
        with pytest.raises(tipo) as info:
            resultado = obter_segredo(nome, _ClienteFalho(exc))

    assert info.value is exc
    assert resultado is None
    assert valor not in caplog.text
    assert all(valor not in r.getMessage() for r in caplog.records)
