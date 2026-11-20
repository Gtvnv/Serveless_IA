#!/usr/bin/env python3
"""Verificador de RBAC de menor privilégio (Requisitos 7.3, 7.8 e 7.9).

Uso:
    python tools/verificar_rbac.py CAMINHO_DO_TEMPLATE.json

O arquivo é o JSON compilado do Bicep (``bicep build infra/main.bicep``), isto é,
um ARM template. O verificador procura recursos ``Microsoft.Authorization/roleAssignments``
e reprova toda atribuição que:

- não tenha escopo de um único recurso (escopo de assinatura, de grupo de recursos,
  de grupo de gerenciamento, ausente ou não reconhecido); ou
- use a função Owner, Contributor ou User Access Administrator (por nome ou por
  GUID da role definition) ou cuja função não possa ser identificada.

Política "falha fechada": o que não puder ser classificado como seguro é violação.

Código de saída: 0 conforme; 1 com violações; 2 para erro de uso ou de leitura.

FORMATO DE ATRIBUIÇÃO SIMPLIFICADA (aceito por ``verificar_atribuicoes``)
-------------------------------------------------------------------------
Dicionário com as chaves (todas opcionais, mas ``scope`` e uma função são
necessários para a atribuição ser conforme):

- ``name``: texto, identificador para os relatórios.
- ``scope``: ID do escopo. Aceita ID literal
  (``/subscriptions/<id>/resourceGroups/<rg>/providers/Microsoft.Storage/storageAccounts/<nome>``)
  ou expressão ARM (``[resourceId('Microsoft.Storage/storageAccounts', 'x')]``).
  Ausente ou vazio equivale ao escopo do grupo de recursos (violação).
- ``roleDefinitionId``: ID da role definition (qualquer texto que contenha o GUID, por
  exemplo ``/subscriptions/<id>/providers/Microsoft.Authorization/roleDefinitions/<guid>``
  ou o próprio GUID).
- ``roleName``: nome da função (ex.: ``"Owner"``), comparado sem diferenciar
  maiúsculas de minúsculas.

Em um template, ``scope`` e ``properties.roleDefinitionId`` são lidos do recurso, com
``variables('x')`` e ``parameters('x')`` (``defaultValue``) substituídos quando
possível.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

FUNCOES_PROIBIDAS_GUID: dict[str, str] = {
    "8e3af657-a8ff-443c-a75c-2fe8c4bcb635": "Owner",
    "b24988ac-6180-42a0-ab88-20f7382dd24c": "Contributor",
    "18d7d88d-d35e-4fb5-a5c3-7773c20a72d9": "User Access Administrator",
}
FUNCOES_PROIBIDAS_NOME: dict[str, str] = {
    nome.lower(): nome for nome in FUNCOES_PROIBIDAS_GUID.values()
}

ESCOPO_RECURSO = "recurso"
ESCOPO_ASSINATURA = "assinatura"
ESCOPO_GRUPO_RECURSOS = "grupo_recursos"
ESCOPO_GRUPO_GERENCIAMENTO = "grupo_gerenciamento"
ESCOPO_AUSENTE = "ausente"
ESCOPO_DESCONHECIDO = "desconhecido"

_GUID = re.compile(r"[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}")
# Tipos que NÃO são um recurso individual (contêineres de escopo ou definições).
_TIPOS_NAO_RECURSO = re.compile(
    r"Microsoft\.Resources/(?:resourceGroups|subscriptions)\b"
    r"|Microsoft\.Management/managementGroups\b"
    r"|Microsoft\.Authorization/roleDefinitions\b",
    re.IGNORECASE,
)
_TIPO_EXPRESSAO = re.compile(r"Microsoft\.[A-Za-z0-9.]+/[A-Za-z0-9]+", re.IGNORECASE)
_RECURSO_LITERAL = re.compile(
    r"/providers/(Microsoft\.[A-Za-z0-9.]+)/([A-Za-z0-9]+)/[^/\s'\"\[\]]+", re.IGNORECASE
)
_VARIAVEL = re.compile(r"(variables|parameters)\(\s*'([^']+)'\s*\)")


@dataclass(frozen=True)
class Violacao:
    """Uma violação encontrada: ``atribuicao`` é o nome, ``codigo`` a categoria."""

    atribuicao: str
    codigo: str  # "escopo" ou "funcao"
    motivo: str

    def __str__(self) -> str:
        return f"{self.atribuicao}: [{self.codigo}] {self.motivo}"


def classificar_escopo(escopo: object) -> str:
    """Classifica um escopo como uma das constantes ``ESCOPO_*``."""
    if not isinstance(escopo, str) or not escopo.strip():
        return ESCOPO_AUSENTE
    texto = escopo.strip()
    if "managementgroups" in texto.lower():
        return ESCOPO_GRUPO_GERENCIAMENTO

    if texto.startswith("/") and "[" not in texto:
        if _RECURSO_LITERAL.search(texto) and not _TIPOS_NAO_RECURSO.search(texto):
            return ESCOPO_RECURSO
        if re.fullmatch(r"/subscriptions/[^/]+/?", texto, re.IGNORECASE):
            return ESCOPO_ASSINATURA
        if re.fullmatch(r"/subscriptions/[^/]+/resourceGroups/[^/]+/?", texto, re.IGNORECASE):
            return ESCOPO_GRUPO_RECURSOS
        return ESCOPO_DESCONHECIDO

    # Expressão ARM: um tipo de recurso (que não seja contêiner) indica recurso único.
    sem_conteineres = _TIPOS_NAO_RECURSO.sub("", texto)
    if _TIPO_EXPRESSAO.search(sem_conteineres):
        return ESCOPO_RECURSO
    minusculo = texto.lower()
    if "resourcegroup()" in minusculo or "resourcegroups" in minusculo:
        return ESCOPO_GRUPO_RECURSOS
    if "subscription()" in minusculo or "subscriptionresourceid(" in minusculo or "subscriptions" in minusculo:
        return ESCOPO_ASSINATURA
    return ESCOPO_DESCONHECIDO


def funcoes_proibidas_em(role_definition_id: object = None, role_name: object = None) -> list[str]:
    """Nomes das funções proibidas referenciadas por GUID ou por nome."""
    encontradas: list[str] = []
    if isinstance(role_definition_id, str):
        for guid in _GUID.findall(role_definition_id):
            nome = FUNCOES_PROIBIDAS_GUID.get(guid.lower())
            if nome and nome not in encontradas:
                encontradas.append(nome)
        nome = FUNCOES_PROIBIDAS_NOME.get(role_definition_id.strip().lower())
        if nome and nome not in encontradas:
            encontradas.append(nome)
    if isinstance(role_name, str):
        nome = FUNCOES_PROIBIDAS_NOME.get(role_name.strip().lower())
        if nome and nome not in encontradas:
            encontradas.append(nome)
    return encontradas


def _funcao_identificavel(role_definition_id: object, role_name: object) -> bool:
    if isinstance(role_name, str) and role_name.strip():
        return True
    return isinstance(role_definition_id, str) and bool(_GUID.search(role_definition_id))


def verificar_atribuicoes(atribuicoes: Iterable[dict[str, Any]]) -> list[Violacao]:
    """Verifica atribuições no formato simplificado e devolve as violações.

    Lista vazia significa conforme. Entradas que não são dicionários são violações.
    """
    violacoes: list[Violacao] = []
    for indice, atribuicao in enumerate(atribuicoes):
        if not isinstance(atribuicao, dict):
            violacoes.append(Violacao(f"#{indice}", "escopo", "atribuição inválida (não é um objeto)"))
            continue
        nome = str(atribuicao.get("name") or f"#{indice}")
        escopo = classificar_escopo(atribuicao.get("scope"))
        if escopo != ESCOPO_RECURSO:
            violacoes.append(
                Violacao(nome, "escopo", f"escopo deve ser de um único recurso (encontrado: {escopo})")
            )
        role_id = atribuicao.get("roleDefinitionId")
        role_nome = atribuicao.get("roleName")
        for funcao in funcoes_proibidas_em(role_id, role_nome):
            violacoes.append(Violacao(nome, "funcao", f"função proibida: {funcao}"))
        if not _funcao_identificavel(role_id, role_nome):
            violacoes.append(Violacao(nome, "funcao", "função não identificável (sem GUID nem nome)"))
    return violacoes


def _resolver(valor: object, template: dict[str, Any]) -> object:
    """Substitui ``variables('x')``/``parameters('x')`` por valores do template (até 5 níveis)."""
    if not isinstance(valor, str):
        return valor
    variaveis = template.get("variables") if isinstance(template.get("variables"), dict) else {}
    parametros = template.get("parameters") if isinstance(template.get("parameters"), dict) else {}

    def trocar(m: re.Match[str]) -> str:
        if m.group(1) == "variables":
            achado = variaveis.get(m.group(2))
        else:
            definicao = parametros.get(m.group(2))
            achado = definicao.get("defaultValue") if isinstance(definicao, dict) else None
        if achado is None:
            return m.group(0)
        if isinstance(achado, str):
            return achado[1:-1] if achado.startswith("[") and achado.endswith("]") else achado
        return json.dumps(achado)

    for _ in range(5):
        novo = _VARIAVEL.sub(trocar, valor)
        if novo == valor:
            break
        valor = novo
    return valor


def _tipo_e_atribuicao(recurso: dict[str, Any]) -> bool:
    tipo = str(recurso.get("type", "")).lower()
    return tipo == "microsoft.authorization/roleassignments" or tipo.endswith("/providers/roleassignments")


def _percorrer(recursos: object) -> Iterable[dict[str, Any]]:
    """Itera recursos (lista, ou dicionário em ``languageVersion`` 2.0), incluindo aninhados."""
    if isinstance(recursos, dict):
        recursos = list(recursos.values())
    if not isinstance(recursos, list):
        return
    for recurso in recursos:
        if not isinstance(recurso, dict):
            continue
        yield recurso
        yield from _percorrer(recurso.get("resources"))
        propriedades = recurso.get("properties")
        if isinstance(propriedades, dict) and isinstance(propriedades.get("template"), dict):
            yield from _percorrer(propriedades["template"].get("resources"))


def extrair_atribuicoes(template: dict[str, Any]) -> list[dict[str, Any]]:
    """Extrai de um ARM template as atribuições, no formato simplificado."""
    resultado: list[dict[str, Any]] = []
    if not isinstance(template, dict):
        return resultado
    for recurso in _percorrer(template.get("resources")):
        if not _tipo_e_atribuicao(recurso):
            continue
        propriedades = recurso.get("properties") if isinstance(recurso.get("properties"), dict) else {}
        escopo = recurso.get("scope")
        tipo = str(recurso.get("type", ""))
        if not escopo and tipo.lower().endswith("/providers/roleassignments"):
            # Forma legada: o escopo é o recurso pai (prefixo do tipo).
            escopo = f"[resourceId('{tipo[: -len('/providers/roleAssignments')]}', 'pai')]"
        resultado.append(
            {
                "name": str(recurso.get("name", "")) or f"#{len(resultado)}",
                "scope": _resolver(escopo, template),
                "roleDefinitionId": _resolver(propriedades.get("roleDefinitionId"), template),
            }
        )
    return resultado


def verificar_template(template: dict[str, Any]) -> list[Violacao]:
    """Verifica um ARM template (dict) e devolve as violações."""
    return verificar_atribuicoes(extrair_atribuicoes(template))


def verificar_arquivo(caminho: Path) -> list[Violacao]:
    """Lê o JSON em ``caminho`` e o verifica. Lança ``OSError``/``ValueError`` se ilegível."""
    with open(caminho, encoding="utf-8-sig") as f:
        template = json.load(f)
    if not isinstance(template, dict):
        raise ValueError("o JSON raiz deve ser um objeto")
    return verificar_template(template)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Verifica RBAC de menor privilégio no JSON compilado do Bicep.")
    parser.add_argument("template", type=Path, help="caminho do JSON compilado (ARM template)")
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    try:
        violacoes = verificar_arquivo(args.template)
    except (OSError, ValueError) as e:
        print(f"erro ao ler {args.template}: {e}", file=sys.stderr)
        return 2
    for v in violacoes:
        print(v)
    if violacoes:
        return 1
    print("RBAC conforme: todas as atribuições têm escopo de um único recurso e usam funções permitidas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
