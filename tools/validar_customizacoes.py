#!/usr/bin/env python3
"""Validador das customizações do Agente_Copilot (frontmatter).

Uso:
    python tools/validar_customizacoes.py [--raiz DIR]

Arquivos verificados (relativos à raiz):
- ``.github/instructions/*.instructions.md``: ``applyTo`` obrigatório, não
  vazio e que case ao menos um arquivo existente (globs com ``**``, ``*``,
  ``?`` e chaves ``{a,b}``; vários padrões separados por vírgula).
- ``.github/prompts/*.prompt.md``: ``description`` obrigatório (não vazio, até
  200 caracteres) e ``mode`` obrigatório (``ask``, ``edit`` ou ``agent``).
- ``.github/chatmodes/*.chatmode.md``: ``tools`` obrigatório, lista explícita,
  não vazia e sem curinga. ``description`` e ``mode``, se presentes, seguem as
  mesmas regras dos prompts.

Em qualquer tipo, ``description`` e ``mode`` presentes são validados.
Imprime ``caminho: motivo`` por não conformidade. Código de saída: 0 sem
não conformidades; 1 com não conformidades; 2 para erro de uso.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

MODOS_VALIDOS = ("ask", "edit", "agent")
TAMANHO_MAXIMO_DESCRICAO = 200
PASTAS_IGNORADAS = {".git", "node_modules", ".venv", "__pycache__"}

TIPOS = (
    (".github/instructions", ".instructions.md", "instructions"),
    (".github/prompts", ".prompt.md", "prompts"),
    (".github/chatmodes", ".chatmode.md", "chatmodes"),
)


@dataclass(frozen=True)
class NaoConformidade:
    caminho: str
    motivo: str

    def __str__(self) -> str:
        return f"{self.caminho}: {self.motivo}"


# ---------------------------------------------------------------- frontmatter

def _remover_aspas(valor: str) -> str:
    valor = valor.strip()
    if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
        return valor[1:-1]
    return valor


def _dividir_lista_inline(texto: str) -> list[str]:
    itens: list[str] = []
    atual: list[str] = []
    aspas = ""
    for c in texto:
        if aspas:
            if c == aspas:
                aspas = ""
            atual.append(c)
        elif c in "\"'":
            aspas = c
            atual.append(c)
        elif c == ",":
            itens.append("".join(atual))
            atual = []
        else:
            atual.append(c)
    itens.append("".join(atual))
    return [_remover_aspas(i) for i in itens if i.strip()]


def _valor_escalar_ou_lista(bruto: str) -> object:
    bruto = bruto.strip()
    if bruto.startswith("[") and bruto.endswith("]"):
        return _dividir_lista_inline(bruto[1:-1])
    return _remover_aspas(bruto)


def extrair_frontmatter(texto: str) -> Optional[dict[str, object]]:
    """Retorna o frontmatter como dict (valores str ou list[str]) ou None se ausente.

    Parser mínimo: ``chave: valor``, listas inline ``[a, b]`` e listas em bloco
    (``- item``). Chaves repetidas mantêm a última ocorrência.
    """
    linhas = texto.lstrip("\ufeff").splitlines()
    if not linhas or linhas[0].strip() != "---":
        return None
    fim = None
    for i in range(1, len(linhas)):
        if linhas[i].strip() == "---":
            fim = i
            break
    if fim is None:
        return None

    dados: dict[str, object] = {}
    chave_atual: Optional[str] = None
    for linha in linhas[1:fim]:
        if not linha.strip() or linha.lstrip().startswith("#"):
            continue
        item = re.match(r"^\s+-\s*(.*)$", linha) or re.match(r"^-\s*(.*)$", linha)
        if item and chave_atual is not None:
            atual = dados.get(chave_atual)
            if not isinstance(atual, list):
                atual = []
                dados[chave_atual] = atual
            atual.append(_remover_aspas(item.group(1)))
            continue
        m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", linha)
        if m:
            chave_atual = m.group(1)
            dados[chave_atual] = _valor_escalar_ou_lista(m.group(2))
    return dados


# ----------------------------------------------------------------------- glob

def _expandir_chaves(padrao: str) -> list[str]:
    """Expande ``{a,b}`` (inclusive aninhado) em uma lista de padrões."""
    inicio = padrao.find("{")
    if inicio < 0:
        return [padrao]
    nivel = 0
    partes: list[str] = []
    ultimo = inicio + 1
    for i in range(inicio, len(padrao)):
        c = padrao[i]
        if c == "{":
            nivel += 1
        elif c == "}":
            nivel -= 1
            if nivel == 0:
                partes.append(padrao[ultimo:i])
                prefixo, sufixo = padrao[:inicio], padrao[i + 1:]
                resultado: list[str] = []
                for p in partes:
                    resultado.extend(_expandir_chaves(prefixo + p + sufixo))
                return resultado
        elif c == "," and nivel == 1:
            partes.append(padrao[ultimo:i])
            ultimo = i + 1
    return [padrao]  # chave sem fechamento: trata literalmente


def _glob_para_regex(padrao: str) -> re.Pattern[str]:
    i, saida = 0, []
    while i < len(padrao):
        c = padrao[i]
        if c == "*":
            if padrao[i:i + 2] == "**":
                i += 2
                if padrao[i:i + 1] == "/":
                    i += 1
                    saida.append(r"(?:.*/)?")
                else:
                    saida.append(r".*")
                continue
            saida.append(r"[^/]*")
        elif c == "?":
            saida.append(r"[^/]")
        else:
            saida.append(re.escape(c))
        i += 1
    return re.compile("^" + "".join(saida) + "$")


def casa_glob(padrao: str, caminho: str) -> bool:
    """True se ``caminho`` (separador ``/``) casa com o glob ``padrao``."""
    padrao = padrao.strip().replace("\\", "/")
    if padrao.startswith("./"):
        padrao = padrao[2:]
    if not padrao:
        return False
    if "/" not in padrao:
        padrao = "**/" + padrao
    return any(_glob_para_regex(p).match(caminho) for p in _expandir_chaves(padrao))


def listar_arquivos(raiz: Path) -> list[str]:
    arquivos: list[str] = []
    for pasta, subpastas, nomes in os.walk(raiz):
        subpastas[:] = [d for d in subpastas if d not in PASTAS_IGNORADAS]
        for nome in nomes:
            rel = Path(pasta, nome).relative_to(raiz).as_posix()
            arquivos.append(rel)
    return arquivos


def _padroes_apply_to(valor: object) -> list[str]:
    if isinstance(valor, list):
        itens = [str(v) for v in valor]
    else:
        # separa por vírgula apenas fora de chaves
        itens, atual, nivel = [], [], 0
        for c in str(valor):
            if c == "{":
                nivel += 1
            elif c == "}":
                nivel = max(0, nivel - 1)
            if c == "," and nivel == 0:
                itens.append("".join(atual))
                atual = []
            else:
                atual.append(c)
        itens.append("".join(atual))
    return [i.strip() for i in itens if i.strip()]


# ------------------------------------------------------------------ validação

def _validar_apply_to(fm: dict, caminho: str, arquivos: list[str]) -> list[NaoConformidade]:
    if "applyTo" not in fm:
        return [NaoConformidade(caminho, "applyTo ausente")]
    padroes = _padroes_apply_to(fm["applyTo"])
    if not padroes:
        return [NaoConformidade(caminho, "applyTo vazio")]
    if not any(casa_glob(p, a) for p in padroes for a in arquivos):
        return [NaoConformidade(caminho, "applyTo sem correspondência com arquivo existente")]
    return []


def _validar_description(fm: dict, caminho: str, obrigatorio: bool) -> list[NaoConformidade]:
    if "description" not in fm:
        return [NaoConformidade(caminho, "description ausente")] if obrigatorio else []
    valor = fm["description"]
    texto = " ".join(valor) if isinstance(valor, list) else str(valor)
    if not texto.strip():
        return [NaoConformidade(caminho, "description vazio")]
    if len(texto) > TAMANHO_MAXIMO_DESCRICAO:
        return [NaoConformidade(
            caminho,
            f"description excede {TAMANHO_MAXIMO_DESCRICAO} caracteres ({len(texto)})",
        )]
    return []


def _validar_mode(fm: dict, caminho: str, obrigatorio: bool) -> list[NaoConformidade]:
    if "mode" not in fm:
        return [NaoConformidade(caminho, "mode ausente")] if obrigatorio else []
    valor = fm["mode"]
    if not isinstance(valor, str) or valor not in MODOS_VALIDOS:
        return [NaoConformidade(
            caminho, f"mode inválido (esperado: {', '.join(MODOS_VALIDOS)})"
        )]
    return []


def _validar_tools(fm: dict, caminho: str) -> list[NaoConformidade]:
    if "tools" not in fm:
        return [NaoConformidade(caminho, "tools ausente")]
    valor = fm["tools"]
    itens = valor if isinstance(valor, list) else _dividir_lista_inline(str(valor))
    itens = [str(i).strip() for i in itens if str(i).strip()]
    if not itens:
        return [NaoConformidade(caminho, "tools vazio")]
    if any("*" in i for i in itens):
        return [NaoConformidade(caminho, "tools contém curinga")]
    return []


def validar_arquivo(caminho_rel: str, texto: str, tipo: str, arquivos: list[str]) -> list[NaoConformidade]:
    """Valida um arquivo de customização. ``tipo``: instructions, prompts ou chatmodes."""
    fm = extrair_frontmatter(texto)
    if fm is None:
        return [NaoConformidade(caminho_rel, "frontmatter ausente ou malformado")]
    problemas: list[NaoConformidade] = []
    if tipo == "instructions":
        problemas += _validar_apply_to(fm, caminho_rel, arquivos)
    problemas += _validar_description(fm, caminho_rel, obrigatorio=tipo == "prompts")
    problemas += _validar_mode(fm, caminho_rel, obrigatorio=tipo == "prompts")
    if tipo == "chatmodes":
        problemas += _validar_tools(fm, caminho_rel)
    return problemas


def validar_repositorio(raiz: Path | str) -> list[NaoConformidade]:
    """Valida todas as customizações sob ``raiz`` e retorna as não conformidades."""
    raiz = Path(raiz)
    arquivos = listar_arquivos(raiz)
    problemas: list[NaoConformidade] = []
    for pasta, sufixo, tipo in TIPOS:
        diretorio = raiz / pasta
        if not diretorio.is_dir():
            continue
        for arq in sorted(diretorio.iterdir()):
            if not (arq.is_file() and arq.name.endswith(sufixo)):
                continue
            rel = arq.relative_to(raiz).as_posix()
            try:
                texto = arq.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as e:
                problemas.append(NaoConformidade(rel, f"não foi possível ler o arquivo ({type(e).__name__})"))
                continue
            problemas += validar_arquivo(rel, texto, tipo, arquivos)
    return problemas


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Valida o frontmatter das customizações do Agente_Copilot.")
    parser.add_argument("--raiz", default=str(Path(__file__).resolve().parent.parent),
                        help="raiz do repositório (padrão: pasta pai de tools/)")
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    raiz = Path(args.raiz)
    if not raiz.is_dir():
        print(f"erro: raiz inexistente: {raiz}", file=sys.stderr)
        return 2
    problemas = validar_repositorio(raiz)
    for p in problemas:
        print(p)
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
