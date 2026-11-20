"""Testes unitários da lógica de negócio e dos adaptadores (Requisitos 4.7, 5.1 a 5.4).

Sem rede, credenciais nem runtime do Azure Functions.
"""

import json
import logging

import pytest

from app.http import tratar_http
from app.negocio import desserializar, processar_pedido, serializar
from app.validacao import (
    TAMANHO_MAX_CORPO,
    PedidoEntrada,
    validar_pedido,
    validar_texto,
)

LOGGER = logging.getLogger("teste_unitario")


def _pedido(**sobrescrever) -> PedidoEntrada:
    dados = dict(nome_tarefa="Escrever relatório", descricao="Mensal", prioridade=3, etiquetas=("a", "b"))
    dados.update(sobrescrever)
    return PedidoEntrada(**dados)


def _corpo(**sobrescrever) -> bytes:
    dados = {"nome_tarefa": "Escrever relatório", "descricao": "Mensal", "prioridade": 3, "etiquetas": ["a"]}
    dados.update(sobrescrever)
    return json.dumps(dados).encode("utf-8")


# --- processar_pedido -------------------------------------------------------


def test_processar_pedido_sucesso():
    saida = processar_pedido(_pedido())
    assert saida.prioridade == 3
    assert len(saida.id) == 32
    assert "Escrever relatório" in saida.resumo
    assert saida == processar_pedido(_pedido())  # determinístico


def test_processar_pedido_nome_longo_e_truncado_no_resumo():
    saida = processar_pedido(_pedido(nome_tarefa="x" * 256))
    assert "x" * 256 not in saida.resumo
    assert "…" in saida.resumo


# --- serializar / desserializar ---------------------------------------------


def test_serializar_desserializar_round_trip():
    p = _pedido()
    assert desserializar(serializar(p)) == p


def test_desserializar_json_sem_campo_obrigatorio_falha():
    with pytest.raises(KeyError):
        desserializar(json.dumps({"nome_tarefa": "x"}))
    with pytest.raises(ValueError):
        desserializar("não é json")


# --- validar_pedido ---------------------------------------------------------


def test_validar_pedido_sucesso():
    r = validar_pedido(_corpo())
    assert r.valido
    assert r.entrada == _pedido(etiquetas=("a",))
    assert r.erros == ()


def test_validar_pedido_falha_lista_campos_invalidos():
    r = validar_pedido(_corpo(prioridade=9, nome_tarefa=""))
    assert not r.valido
    assert r.entrada is None
    assert {e.campo for e in r.erros} == {"prioridade", "nome_tarefa"}


def test_validar_pedido_json_malformado_e_corpo_excedido():
    assert not validar_pedido(b"{ruim").valido
    r = validar_pedido(b" " * (TAMANHO_MAX_CORPO + 1))
    assert not r.valido and r.corpo_excedido


# --- validar_texto ----------------------------------------------------------


def test_validar_texto_sucesso():
    assert validar_texto("olá").valido
    assert validar_texto("a" * 256).valido


def test_validar_texto_falha():
    assert not validar_texto("a" * 257).valido
    assert not validar_texto(123).valido
    assert not validar_texto(None).valido


# --- tratar_http ------------------------------------------------------------


def test_tratar_http_200_com_corpo_valido():
    resp = tratar_http(_corpo(), "inv-1", LOGGER)
    assert resp.status == 200
    assert resp.cabecalhos["Content-Type"] == "application/json"
    assert json.loads(resp.corpo)["prioridade"] == 3


def test_tratar_http_400_com_entrada_invalida():
    chamado = []
    resp = tratar_http(_corpo(prioridade="alta"), "inv-2", LOGGER, processar=chamado.append)
    assert resp.status == 400
    assert json.loads(resp.corpo)["erros"][0]["campo"] == "prioridade"
    assert chamado == []  # lógica de negócio não é chamada


def test_tratar_http_413_corpo_acima_de_1mb():
    resp = tratar_http(b" " * (TAMANHO_MAX_CORPO + 1), "inv-3", LOGGER)
    assert resp.status == 413


def test_tratar_http_500_generico_quando_negocio_lanca_excecao():
    def falha(_):
        raise RuntimeError("detalhe-interno-secreto")

    resp = tratar_http(_corpo(), "inv-4", LOGGER, processar=falha)
    assert resp.status == 500
    assert "detalhe-interno-secreto" not in resp.corpo
    assert "RuntimeError" not in resp.corpo
