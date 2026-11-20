#!/usr/bin/env python3
"""Verificador_Seguranca: procura Segredos e Termos_Proibidos no repositório.

Uso:
    python tools/verificador_seguranca.py [--raiz DIR] [--termos ARQUIVO]

- Varre os arquivos versionados (``git ls-files``). Se ``--raiz`` não for a raiz
  de um repositório Git, varre a árvore de arquivos (ignorando ``.git``,
  ``node_modules``, ``.venv`` e similares).
- Padrões de Segredos: chaves privadas, chaves de acesso, connection strings e
  tokens. Termos_Proibidos: lista em ``tools/termos_proibidos.txt``, sem
  diferenciar maiúsculas de minúsculas, em nomes de pastas, nomes de arquivos
  e conteúdo de arquivos de texto.
- Imprime ``caminho:linha categoria`` (``caminho`` para ocorrências em nomes),
  nunca o valor encontrado. Não altera nenhum arquivo.
- Código de saída: 0 sem ocorrências; 1 com ocorrências; 2 para erro de uso.

EXCLUSÃO EXPLÍCITA: o arquivo de termos (``--termos``) é excluído da varredura,
pois contém os próprios termos. Nenhum outro arquivo é excluído.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

ARQUIVO_TERMOS_PADRAO = Path(__file__).resolve().parent / "termos_proibidos.txt"

# Pastas ignoradas apenas no modo sem Git (com Git, vale ``git ls-files``).
PASTAS_IGNORADAS_SEM_GIT = {".git", "node_modules", ".venv", "__pycache__"}

CATEGORIA_TERMO = "termo_proibido"

# Placeholders aceitos como valor (não são Segredos).
_VALOR = r"(?![<${%\[])[A-Za-z0-9+/=_\-.~]{8,}"

PADROES_SEGREDO: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("chave_privada", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("chave_acesso_aws", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("token_github", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})\b")),
    ("token_slack", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("chave_api_google", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("token_jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    (
        "connection_string",
        re.compile(
            r"(?i)\b(?:AccountKey|SharedAccessKey|SharedAccessSignature|Password|Pwd)\s*=\s*" + _VALOR
        ),
    ),
    (
        "connection_string_url",
        re.compile(r"(?i)\b[a-z][a-z0-9+.\-]*://[^\s:/@'\"]+:(?![<${%\[])[^\s@'\"/]{3,}@"),
    ),
    (
        "segredo_atribuido",
        re.compile(
            r"(?i)\b(?:api[_\-]?key|secret|client[_\-]?secret|access[_\-]?token|auth[_\-]?token|token)"
            r"[\"']?\s*[:=]\s*[\"']" + _VALOR + r"[\"']"
        ),
    ),
)


@dataclass(frozen=True)
class Ocorrencia:
    """Ocorrência encontrada. Nunca contém o valor encontrado."""

    caminho: str
    linha: Optional[int]
    categoria: str

    def formatar(self) -> str:
        local = self.caminho if self.linha is None else f"{self.caminho}:{self.linha}"
        return f"{local} {self.categoria}"


def carregar_termos(arquivo: Path) -> list[str]:
    """Lê os termos (um por linha; ignora vazias e comentários com '#')."""
    if not arquivo.is_file():
        return []
    termos: list[str] = []
    for bruta in arquivo.read_text(encoding="utf-8", errors="replace").splitlines():
        termo = bruta.strip()
        if termo and not termo.startswith("#"):
            termos.append(termo.casefold())
    return termos


def _listar_com_git(raiz: Path) -> Optional[list[str]]:
    """Retorna os arquivos versionados, ou None se ``raiz`` não for raiz de repo Git."""
    try:
        topo = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=raiz, capture_output=True, text=True, check=True,
        ).stdout.strip()
        if not topo or Path(topo).resolve() != raiz.resolve():
            return None
        saida = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=raiz, capture_output=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    return [p for p in saida.decode("utf-8", errors="replace").split("\0") if p]


def _listar_sem_git(raiz: Path) -> list[str]:
    arquivos: list[str] = []
    for caminho in raiz.rglob("*"):
        relativo = caminho.relative_to(raiz)
        if PASTAS_IGNORADAS_SEM_GIT.intersection(relativo.parts):
            continue
        if caminho.is_file():
            arquivos.append(relativo.as_posix())
    return sorted(arquivos)


def listar_arquivos(raiz: Path, usar_git: bool = True) -> list[str]:
    """Lista os caminhos relativos (com '/') a varrer."""
    if usar_git:
        versionados = _listar_com_git(raiz)
        if versionados is not None:
            return versionados
    return _listar_sem_git(raiz)


def _ler_linhas(arquivo: Path) -> Iterable[str]:
    try:
        dados = arquivo.read_bytes()
    except OSError:
        return []
    if b"\0" in dados[:8192]:  # arquivo binário: só o nome é verificado
        return []
    return dados.decode("utf-8", errors="replace").splitlines()


def verificar(
    raiz: Path,
    arquivo_termos: Optional[Path] = None,
    usar_git: bool = True,
) -> list[Ocorrencia]:
    """Varre ``raiz`` e devolve as ocorrências de Segredos e Termos_Proibidos.

    O ``arquivo_termos`` é excluído da varredura (exclusão explícita).
    """
    raiz = raiz.resolve()
    caminho_termos = (arquivo_termos or ARQUIVO_TERMOS_PADRAO).resolve()
    termos = carregar_termos(caminho_termos)
    ocorrencias: list[Ocorrencia] = []

    for relativo in listar_arquivos(raiz, usar_git):
        arquivo = raiz / relativo
        if arquivo.resolve() == caminho_termos:
            continue  # exclusão explícita da lista de termos
        if not arquivo.is_file():  # versionado, mas removido da árvore de trabalho
            continue

        nome_casefold = relativo.casefold()
        if any(t in nome_casefold for t in termos):
            ocorrencias.append(Ocorrencia(relativo, None, CATEGORIA_TERMO))

        for numero, texto in enumerate(_ler_linhas(arquivo), start=1):
            texto_casefold = texto.casefold()
            if any(t in texto_casefold for t in termos):
                ocorrencias.append(Ocorrencia(relativo, numero, CATEGORIA_TERMO))
            for categoria, padrao in PADROES_SEGREDO:
                if padrao.search(texto):
                    ocorrencias.append(Ocorrencia(relativo, numero, categoria))

    return ocorrencias


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Procura Segredos e Termos_Proibidos.")
    parser.add_argument("--raiz", type=Path, default=Path.cwd(), help="diretório raiz (padrão: atual)")
    parser.add_argument("--termos", type=Path, default=ARQUIVO_TERMOS_PADRAO, help="arquivo de termos")
    parser.add_argument("--sem-git", action="store_true", help="varre a árvore sem usar git ls-files")
    args = parser.parse_args(argv)

    if not args.raiz.is_dir():
        print(f"Diretório raiz inválido: {args.raiz}", file=sys.stderr)
        return 2
    if not args.termos.is_file():
        print(f"Aviso: arquivo de termos não encontrado: {args.termos}", file=sys.stderr)

    ocorrencias = verificar(args.raiz, args.termos, usar_git=not args.sem_git)
    for oc in ocorrencias:
        print(oc.formatar())
    if ocorrencias:
        print(f"{len(ocorrencias)} ocorrência(s) encontrada(s).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
