"""Lógica de negócio e serialização. Pura, sem dependência do runtime do Azure Functions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from app.validacao import PedidoEntrada

RESUMO_MAX_TAMANHO = 80


@dataclass(frozen=True)
class SaidaPedido:
    id: str
    resumo: str
    prioridade: int


def serializar(p: PedidoEntrada) -> str:
    """Converte o pedido em JSON (etiquetas viram lista)."""
    return json.dumps(
        {
            "nome_tarefa": p.nome_tarefa,
            "descricao": p.descricao,
            "prioridade": p.prioridade,
            "etiquetas": list(p.etiquetas),
        },
        sort_keys=True,
    )


def desserializar(s: str) -> PedidoEntrada:
    """Reconstrói o pedido a partir do JSON gerado por `serializar` (etiquetas como tupla)."""
    dados = json.loads(s)
    return PedidoEntrada(
        nome_tarefa=dados["nome_tarefa"],
        descricao=dados["descricao"],
        prioridade=dados["prioridade"],
        etiquetas=tuple(dados["etiquetas"]),
    )


def processar_pedido(p: PedidoEntrada) -> SaidaPedido:
    """Processa um pedido válido. O id é determinístico (hash da serialização)."""
    id_pedido = hashlib.sha256(serializar(p).encode("utf-8")).hexdigest()[:32]
    nome = p.nome_tarefa
    if len(nome) > RESUMO_MAX_TAMANHO:
        nome = nome[: RESUMO_MAX_TAMANHO - 1] + "…"
    resumo = f"{nome} (prioridade {p.prioridade}, {len(p.etiquetas)} etiqueta(s))"
    return SaidaPedido(id=id_pedido, resumo=resumo, prioridade=p.prioridade)


def executar_rotina_periodica(_evento: object = None) -> str:
    """Rotina do temporizador. Pura e sem I/O externo; aceita (e ignora) o evento recebido."""
    return "rotina periódica executada"
