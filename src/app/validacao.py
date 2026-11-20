"""Modelos e validação de entrada. Lógica pura, apenas biblioteca padrão."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

TAMANHO_MAX_CORPO = 1024 * 1024  # 1 MB
TAMANHO_MAX_TEXTO = 256
NOME_TAREFA_MIN = 1
PRIORIDADE_MIN = 1
PRIORIDADE_MAX = 5
ETIQUETAS_MAX_ITENS = 10
ETIQUETA_MAX_TAMANHO = 32


@dataclass(frozen=True)
class Erro:
    campo: str
    motivo: str


@dataclass(frozen=True)
class PedidoEntrada:
    nome_tarefa: str  # 1..256 caracteres
    descricao: str  # 0..256 caracteres
    prioridade: int  # 1..5
    etiquetas: tuple[str, ...]  # até 10 itens de até 32 caracteres


@dataclass(frozen=True)
class ResultadoValidacao:
    valido: bool
    entrada: Optional[PedidoEntrada]
    erros: tuple[Erro, ...]
    # Verdadeiro quando o corpo excede 1 MB (a camada HTTP responde 413).
    corpo_excedido: bool = False


def _invalido(*erros: Erro, corpo_excedido: bool = False) -> ResultadoValidacao:
    return ResultadoValidacao(False, None, tuple(erros), corpo_excedido)


def _erros_texto(campo: str, valor: object, minimo: int, maximo: int) -> list[Erro]:
    if not isinstance(valor, str):
        return [Erro(campo, "deve ser um texto")]
    if len(valor) > maximo:
        return [Erro(campo, f"excede {maximo} caracteres")]
    if len(valor) < minimo:
        return [Erro(campo, "não pode ser vazio" if minimo == 1 else f"deve ter ao menos {minimo} caracteres")]
    return []


def validar_texto(valor: object) -> ResultadoValidacao:
    """Valida um valor de texto (até 256 caracteres). Nunca lança exceção."""
    try:
        erros = _erros_texto("texto", valor, 0, TAMANHO_MAX_TEXTO)
    except Exception:  # defesa: o contrato é nunca lançar
        erros = [Erro("texto", "valor inválido")]
    if erros:
        return _invalido(*erros)
    return ResultadoValidacao(True, None, ())


def _validar_etiquetas(valor: object) -> tuple[list[Erro], tuple[str, ...]]:
    if not isinstance(valor, list):
        return [Erro("etiquetas", "deve ser uma lista de textos")], ()
    if len(valor) > ETIQUETAS_MAX_ITENS:
        return [Erro("etiquetas", f"excede {ETIQUETAS_MAX_ITENS} itens")], ()
    erros: list[Erro] = []
    for i, item in enumerate(valor):
        if not isinstance(item, str):
            erros.append(Erro(f"etiquetas[{i}]", "deve ser um texto"))
        elif len(item) > ETIQUETA_MAX_TAMANHO:
            erros.append(Erro(f"etiquetas[{i}]", f"excede {ETIQUETA_MAX_TAMANHO} caracteres"))
    return erros, tuple(valor) if not erros else ()


def validar_pedido(corpo: bytes) -> ResultadoValidacao:
    """Valida o corpo bruto da requisição. Nunca lança exceção."""
    try:
        return _validar_pedido(corpo)
    except Exception:  # defesa: o contrato é nunca lançar
        return _invalido(Erro("corpo", "conteúdo inválido"))


def _validar_pedido(corpo: bytes) -> ResultadoValidacao:
    if not isinstance(corpo, (bytes, bytearray)):
        return _invalido(Erro("corpo", "deve ser um JSON"))
    if len(corpo) > TAMANHO_MAX_CORPO:
        return _invalido(Erro("corpo", "excede 1 MB"), corpo_excedido=True)

    try:
        dados = json.loads(bytes(corpo).decode("utf-8"))
    except (ValueError, RecursionError):
        return _invalido(Erro("corpo", "deve ser um JSON válido em UTF-8"))
    if not isinstance(dados, dict):
        return _invalido(Erro("corpo", "deve ser um objeto JSON"))

    erros: list[Erro] = []

    nome = dados.get("nome_tarefa")
    if "nome_tarefa" not in dados:
        erros.append(Erro("nome_tarefa", "campo obrigatório ausente"))
    else:
        erros += _erros_texto("nome_tarefa", nome, NOME_TAREFA_MIN, TAMANHO_MAX_TEXTO)

    descricao = dados.get("descricao", "")
    erros += _erros_texto("descricao", descricao, 0, TAMANHO_MAX_TEXTO)

    prioridade = dados.get("prioridade")
    if "prioridade" not in dados:
        erros.append(Erro("prioridade", "campo obrigatório ausente"))
    elif isinstance(prioridade, bool) or not isinstance(prioridade, int):
        erros.append(Erro("prioridade", "deve ser um número inteiro"))
    elif not PRIORIDADE_MIN <= prioridade <= PRIORIDADE_MAX:
        erros.append(Erro("prioridade", f"deve estar entre {PRIORIDADE_MIN} e {PRIORIDADE_MAX}"))

    erros_etiquetas, etiquetas = _validar_etiquetas(dados.get("etiquetas", []))
    erros += erros_etiquetas

    if erros:
        return _invalido(*erros)
    return ResultadoValidacao(True, PedidoEntrada(nome, descricao, prioridade, etiquetas), ())
