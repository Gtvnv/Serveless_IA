#!/usr/bin/env python3
"""Validar_Documentacao: confere que cada customização está em docs/customizacoes.md.

Uso:
    python tools/validar_documentacao.py [--raiz DIR]

- Customizações: ``.github/copilot-instructions.md``,
  ``.github/instructions/*.instructions.md``, ``.github/prompts/*.prompt.md`` e
  ``.github/chatmodes/*.chatmode.md``.
- Uma customização tem entrada se o nome do arquivo (ex.:
  ``revisar.prompt.md``) aparece como token inteiro em ``docs/customizacoes.md``.
- Se ``docs/customizacoes.md`` não existir, todas as customizações faltam.
- Imprime um nome por linha para cada customização sem entrada. Não altera
  arquivos. Código de saída: 0 sem pendências; 1 com pendências; 2 erro de uso.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable, List, Optional

ARQUIVO_DOCUMENTACAO = Path("docs") / "customizacoes.md"

_PADROES = (
    ("instructions", "*.instructions.md"),
    ("prompts", "*.prompt.md"),
    ("chatmodes", "*.chatmode.md"),
)


def listar_customizacoes(raiz: Path) -> List[str]:
    """Retorna os nomes (ordenados, sem duplicatas) dos arquivos de customização."""
    github = Path(raiz) / ".github"
    nomes = set()
    if (github / "copilot-instructions.md").is_file():
        nomes.add("copilot-instructions.md")
    for pasta, padrao in _PADROES:
        diretorio = github / pasta
        if diretorio.is_dir():
            nomes.update(p.name for p in diretorio.glob(padrao) if p.is_file())
    return sorted(nomes)


def _tem_entrada(nome: str, texto: str) -> bool:
    padrao = r"(?<![\w.\-])" + re.escape(nome) + r"(?![\w\-])"
    return re.search(padrao, texto) is not None


def nomes_sem_descricao(
    nomes_customizacoes: Iterable[str], texto_documentacao: Optional[str]
) -> List[str]:
    """Retorna exatamente os nomes sem entrada no texto (``None`` = sem documento)."""
    texto = texto_documentacao or ""
    unicos = sorted(set(nomes_customizacoes))
    return [n for n in unicos if not _tem_entrada(n, texto)]


def validar(raiz: Path) -> List[str]:
    """Valida a árvore em ``raiz`` e retorna os nomes sem descrição."""
    raiz = Path(raiz)
    doc = raiz / ARQUIVO_DOCUMENTACAO
    texto = doc.read_text(encoding="utf-8") if doc.is_file() else None
    return nomes_sem_descricao(listar_customizacoes(raiz), texto)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raiz", default=".", help="raiz do repositório")
    args = parser.parse_args(argv)
    raiz = Path(args.raiz)
    if not raiz.is_dir():
        print(f"Raiz inexistente: {raiz}", file=sys.stderr)
        return 2
    faltando = validar(raiz)
    for nome in faltando:
        print(f"{nome}: sem entrada em {ARQUIVO_DOCUMENTACAO.as_posix()}")
    return 1 if faltando else 0


if __name__ == "__main__":
    sys.exit(main())
