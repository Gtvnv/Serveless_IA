"""Teste de propriedade do verificador de Termos_Proibidos.

Os termos são sintéticos (gerados pelo teste). O arquivo real
``tools/termos_proibidos.txt`` não é usado.
"""

import contextlib
import io
import tempfile
from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import verificador_seguranca as vs

# Alfabeto do termo disjunto das letras usadas nos nomes/conteúdos neutros.
_termos = st.text(alphabet="zxj", min_size=6, max_size=10)
_modos = st.sampled_from(["arquivo", "pasta", "conteudo"])


def _variar_caixa(termo: str, bits: list[bool]) -> str:
    return "".join(c.upper() if bits[i % len(bits)] else c.lower() for i, c in enumerate(termo))


def _instantaneo(raiz: Path) -> dict[str, bytes | None]:
    return {
        p.relative_to(raiz).as_posix(): (p.read_bytes() if p.is_file() else None)
        for p in sorted(raiz.rglob("*"))
    }


def _rodar(raiz: Path, termos: Path) -> tuple[int, list[str]]:
    saida = io.StringIO()
    with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(io.StringIO()):
        codigo = vs.main(["--raiz", str(raiz), "--termos", str(termos), "--sem-git"])
    return codigo, saida.getvalue().splitlines()


def _montar_neutra(raiz: Path) -> None:
    (raiz / "pasta_a").mkdir()
    (raiz / "pasta_a" / "arquivo_1.dat").write_text("conteudo ok\nlinha dois\n", encoding="utf-8")
    (raiz / "arquivo_0.dat").write_text("nada a ver\n", encoding="utf-8")


# Feature: serverless-ai-agent-azure-functions, Property 11: Verificador de Termos_Proibidos
# **Validates: Requirements 11.1, 11.2, 11.3**
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    termo=_termos,
    bits=st.lists(st.booleans(), min_size=1, max_size=10),
    modo=_modos,
    linha_extra=st.integers(min_value=0, max_value=3),
)
def test_termo_injetado_e_detectado_sem_alterar_arquivos(termo, bits, modo, linha_extra):
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        raiz = base / "raiz"
        raiz.mkdir()
        arq_termos = base / "termos.txt"
        arq_termos.write_text(termo + "\n", encoding="utf-8")
        _montar_neutra(raiz)
        injetado = _variar_caixa(termo, bits)

        if modo == "arquivo":
            alvo = f"arq_{injetado}.dat"
            (raiz / alvo).write_text("neutro\n", encoding="utf-8")
            esperado = alvo
        elif modo == "pasta":
            (raiz / f"dir_{injetado}").mkdir()
            alvo = f"dir_{injetado}/interno.dat"
            (raiz / alvo).write_text("neutro\n", encoding="utf-8")
            esperado = alvo
        else:
            linhas = ["neutro"] * linha_extra + [f"texto {injetado} fim"] + ["neutro"]
            alvo = "pasta_a/doc.dat"
            (raiz / alvo).write_text("\n".join(linhas) + "\n", encoding="utf-8")
            esperado = f"{alvo}:{linha_extra + 1}"

        antes = _instantaneo(raiz)
        codigo, linhas_saida = _rodar(raiz, arq_termos)
        depois = _instantaneo(raiz)

        assert codigo != 0
        assert any(l.startswith(esperado + " ") for l in linhas_saida), (esperado, linhas_saida)
        assert antes == depois


# Feature: serverless-ai-agent-azure-functions, Property 11: Verificador de Termos_Proibidos
# **Validates: Requirements 11.1, 11.2, 11.3**
@settings(max_examples=100, deadline=None)
@given(termos=st.lists(_termos, min_size=1, max_size=3))
def test_arvore_sem_termos_retorna_zero(termos):
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        raiz = base / "raiz"
        raiz.mkdir()
        arq_termos = base / "termos.txt"
        arq_termos.write_text("\n".join(termos) + "\n", encoding="utf-8")
        _montar_neutra(raiz)

        antes = _instantaneo(raiz)
        codigo, linhas_saida = _rodar(raiz, arq_termos)

        assert codigo == 0
        assert linhas_saida == []
        assert antes == _instantaneo(raiz)
