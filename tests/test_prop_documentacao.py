# -*- coding: utf-8 -*-
"""Teste de propriedade do verificador de documentação (Requisitos 10.3 e 10.8)."""

import tempfile
from pathlib import Path

from hypothesis import HealthCheck, given, settings, strategies as st

import validar_documentacao as vd

_SUFIXOS = (".instructions.md", ".prompt.md", ".chatmode.md")
# Radicais curtos e parecidos entre si (prefixo/sufixo um do outro).
_RADICAIS = st.text(alphabet="ab-", min_size=1, max_size=4).filter(
    lambda s: s[0] != "-"
)
_NOMES = st.builds(lambda r, s: r + s, _RADICAIS, st.sampled_from(_SUFIXOS))

# Variações que NÃO devem contar como entrada do nome original.
_PREFIXOS = ("x", "x-", "x.", "a", "-")
_SUFIXOS_DECOY = ("x", "-x", "2", "_")


def _decoys(nome: str):
    return [p + nome for p in _PREFIXOS] + [nome + s for s in _SUFIXOS_DECOY]


@st.composite
def _cenarios(draw):
    nomes = draw(st.sets(_NOMES, max_size=8))
    ordenados = sorted(nomes)
    documentados = set(
        draw(st.sets(st.sampled_from(ordenados))) if ordenados else set()
    )
    # Entradas extras: nomes avulsos e variações parecidas de nomes reais.
    extras = draw(st.sets(_NOMES, max_size=5))
    for n in ordenados:
        extras.update(draw(st.lists(st.sampled_from(_decoys(n)), max_size=3)))
    return nomes, documentados, extras


def _texto(documentados, extras, formato):
    tokens = sorted(documentados | extras)
    if formato == 0:
        return "\n".join(f"- `{t}`: descrição." for t in tokens)
    if formato == 1:
        return "# Customizações\n\n" + "\n\n".join(f"## {t}\nTexto." for t in tokens)
    return "| Arquivo | Descrição |\n" + "\n".join(f"| {t} | x |" for t in tokens)


# Feature: serverless-ai-agent-azure-functions, Property 14: Verificador de documentação
# **Validates: Requirements 10.3, 10.8**
@settings(
    max_examples=200,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(cenario=_cenarios(), formato=st.integers(0, 2))
def test_reporta_exatamente_customizacoes_sem_descricao(cenario, formato):
    nomes, documentados, extras = cenario
    texto = _texto(documentados, extras, formato)
    # Entradas avulsas/decoys que coincidem com um nome real o documentam de fato.
    esperado = sorted(n for n in nomes if n not in (documentados | extras))

    assert vd.nomes_sem_descricao(nomes, texto) == esperado

    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        pastas = {
            ".instructions.md": "instructions",
            ".prompt.md": "prompts",
            ".chatmode.md": "chatmodes",
        }
        for n in nomes:
            for suf, pasta in pastas.items():
                if n.endswith(suf):
                    d = raiz / ".github" / pasta
                    d.mkdir(parents=True, exist_ok=True)
                    (d / n).write_text("x", encoding="utf-8")
        (raiz / "docs").mkdir()
        (raiz / "docs" / "customizacoes.md").write_text(texto, encoding="utf-8")
        assert vd.validar(raiz) == esperado


def test_sem_documento_todas_faltam():
    assert vd.nomes_sem_descricao(["a.prompt.md", "b.chatmode.md"], None) == [
        "a.prompt.md",
        "b.chatmode.md",
    ]
