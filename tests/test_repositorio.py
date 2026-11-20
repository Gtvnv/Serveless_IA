"""Executa os verificadores sobre o próprio repositório (Requisitos 8.3, 8.4, 11.1 e 11.2)."""

import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _executar(script: str, *extras: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(RAIZ / "tools" / script), "--raiz", str(RAIZ), *extras],
        capture_output=True,
        text=True,
        cwd=str(RAIZ),
        timeout=120,
    )


def test_verificador_seguranca_sem_ocorrencias():
    resultado = _executar("verificador_seguranca.py", "--sem-git")
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr


def test_validar_customizacoes_sem_nao_conformidades():
    resultado = _executar("validar_customizacoes.py")
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
