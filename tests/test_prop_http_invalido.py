"""Teste de propriedade: entrada inválida gera 400 sem vazamento."""

from __future__ import annotations

import json
import logging

from hypothesis import given, settings
from hypothesis import strategies as st

from app.http import tratar_http
from app.validacao import TAMANHO_MAX_CORPO

VALIDO = {"nome_tarefa": "tarefa", "descricao": "texto", "prioridade": 3, "etiquetas": ["a"]}
AUSENTE = object()

_texto = st.text(max_size=20)
_nao_texto = st.one_of(
    st.none(),
    st.integers(),
    st.booleans(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.lists(st.integers(), max_size=3),
    st.dictionaries(st.text(max_size=5), st.integers(), max_size=3),
)
_longo = st.integers(min_value=257, max_value=2000).map(lambda n: "x" * n)

_valores_invalidos = {
    "nome_tarefa": st.one_of(st.just(AUSENTE), _nao_texto, st.just(""), _longo),
    "descricao": st.one_of(_nao_texto, _longo),
    "prioridade": st.one_of(
        st.just(AUSENTE),
        _texto,
        st.booleans(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.integers(max_value=0),
        st.integers(min_value=6),
        st.none(),
    ),
    "etiquetas": st.one_of(
        _texto,
        st.none(),
        st.integers(),
        st.just(["a"] * 11),
        st.lists(st.integers(), min_size=1, max_size=5),
        st.just(["y" * 33]),
    ),
}


@st.composite
def _corpos_invalidos(draw):
    """Retorna (bytes do corpo, campos que devem ser reportados ou None se forem do 'corpo')."""
    tipo = draw(st.sampled_from(["campos", "campos", "campos", "json_malformado", "nao_objeto"]))
    if tipo == "json_malformado":
        bruto = draw(st.binary(max_size=200).filter(_nao_e_json))
        return bruto, {"corpo"}
    if tipo == "nao_objeto":
        valor = draw(st.one_of(st.none(), st.integers(), _texto, st.lists(st.integers(), max_size=3)))
        return json.dumps(valor).encode("utf-8"), {"corpo"}

    campos = draw(st.sets(st.sampled_from(sorted(_valores_invalidos)), min_size=1))
    dados = dict(VALIDO)
    for campo in campos:
        valor = draw(_valores_invalidos[campo])
        if valor is AUSENTE:
            dados.pop(campo)
        else:
            dados[campo] = valor
    return json.dumps(dados).encode("utf-8"), campos


def _nao_e_json(b: bytes) -> bool:
    try:
        json.loads(b.decode("utf-8"))
    except (ValueError, RecursionError):
        return True
    return False


def _processar_proibido(_entrada):
    raise AssertionError("processar não deve ser chamado para entrada inválida")


# Feature: serverless-ai-agent-azure-functions, Property 2: Entrada inválida gera 400 sem vazamento
# **Validates: Requirements 4.3**
@settings(max_examples=200, deadline=None)
@given(_corpos_invalidos())
def test_entrada_invalida_gera_400_sem_vazamento(caso):
    corpo, campos = caso
    assert len(corpo) <= TAMANHO_MAX_CORPO

    resposta = tratar_http(corpo, "inv-1", logging.getLogger("teste"), processar=_processar_proibido)

    assert resposta.status == 400
    dados = json.loads(resposta.corpo)
    assert set(dados) == {"erros"}
    erros = dados["erros"]
    assert erros and all(set(e) == {"campo", "motivo"} for e in erros)
    assert all(e["motivo"] for e in erros)

    reportados = {e["campo"].split("[")[0] for e in erros}
    assert campos <= reportados

    for trecho in ("Traceback", ".py", "Error", "File \"", "\\", "/src/"):
        assert trecho not in resposta.corpo
