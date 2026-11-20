"""Teste de propriedade do verificador de Segredos (Requisitos 8.3 e 8.4)."""

import contextlib
import io
import tempfile
from pathlib import Path

from hypothesis import given, settings, strategies as st

from verificador_seguranca import main, verificar

_ALNUM = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
_MAIUSC_NUM = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def _tam(alfabeto: str, minimo: int, maximo: int):
    return st.text(alphabet=alfabeto, min_size=minimo, max_size=maximo)


# Cada estratégia gera um Segredo que casa com um dos padrões do verificador.
_segredos = st.one_of(
    st.just("-----BEGIN RSA " + "PRIVATE KEY-----"),
    _tam(_MAIUSC_NUM, 16, 16).map(lambda s: "AKIA" + s),
    _tam(_ALNUM, 36, 50).map(lambda s: "ghp_" + s),
    _tam(_ALNUM, 10, 30).map(lambda s: "xoxb-" + s),
    _tam(_ALNUM, 35, 35).map(lambda s: "AIza" + s),
    st.tuples(_tam(_ALNUM, 12, 20), _tam(_ALNUM, 12, 20), _tam(_ALNUM, 12, 20)).map(
        lambda t: f"eyJ{t[0]}.eyJ{t[1]}.{t[2]}"
    ),
    _tam(_ALNUM, 8, 30).map(lambda s: "AccountKey=" + s),
    _tam(_ALNUM, 8, 30).map(lambda s: "Password=" + s),
    st.tuples(_tam("abcdef", 3, 8), _tam(_ALNUM, 4, 20)).map(
        lambda t: f"postgres://{t[0]}:{t[1]}@host"
    ),
    _tam(_ALNUM, 8, 30).map(lambda s: f'api_key = "{s}"'),
)

# Linhas sem nenhum padrão de Segredo (alfabeto restrito, sem '=', ':' ou maiúsculas).
_linha_limpa = st.text(alphabet="abcdefghij klmnop0123456789", min_size=0, max_size=60)
_linha = st.one_of(
    _linha_limpa.map(lambda t: (False, t)),
    st.tuples(_linha_limpa, _segredos).map(lambda t: (True, f"{t[0]} {t[1]}")),
)
_nomes = st.text(alphabet="abcdefg", min_size=1, max_size=6)
_arvores = st.dictionaries(
    _nomes,
    st.lists(_linha, min_size=1, max_size=15),
    min_size=1,
    max_size=5,
)


def _escrever(raiz: Path, arvore: dict) -> None:
    for nome, linhas in arvore.items():
        destino = raiz / "sub" / f"{nome}.txt"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes("\n".join(texto for _, texto in linhas).encode("utf-8"))


def _executar_main(raiz: Path, termos: Path):
    saida, erro = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(erro):
        codigo = main(["--raiz", str(raiz), "--termos", str(termos), "--sem-git"])
    return codigo, saida.getvalue() + erro.getvalue()


# Feature: serverless-ai-agent-azure-functions, Property 10: Verificador de Segredos
# **Validates: Requirements 8.3, 8.4**
@settings(max_examples=100, deadline=None)
@given(_arvores)
def test_verificador_lista_local_sem_imprimir_valor(arvore):
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        termos = raiz / "termos-inexistente.txt"  # fora da varredura; sem termos
        _escrever(raiz, arvore)

        esperado = {
            (f"sub/{nome}.txt", i)
            for nome, linhas in arvore.items()
            for i, (segredo, _) in enumerate(linhas, start=1)
            if segredo
        }

        ocorrencias = verificar(raiz, termos, usar_git=False)
        encontrado = {(o.caminho, o.linha) for o in ocorrencias}
        assert encontrado == esperado

        codigo, saida = _executar_main(raiz, termos)
        if esperado:
            assert codigo != 0
            for caminho, linha in esperado:
                assert f"{caminho}:{linha} " in saida
            # Nenhum trecho de linha com Segredo é impresso.
            for linhas in arvore.values():
                for segredo, texto in linhas:
                    if segredo:
                        valor = texto.split(" ", 1)[1] if " " in texto else texto
                        assert valor.strip() not in saida
        else:
            assert codigo == 0
            assert ocorrencias == []


# Feature: serverless-ai-agent-azure-functions, Property 10: Verificador de Segredos
# **Validates: Requirements 8.3, 8.4**
@settings(max_examples=100, deadline=None)
@given(st.dictionaries(_nomes, st.lists(_linha_limpa, min_size=0, max_size=15), max_size=5))
def test_verificador_sem_segredos_retorna_zero(arvore):
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        termos = raiz / "termos-inexistente.txt"
        _escrever(raiz, {n: [(False, t) for t in ls] for n, ls in arvore.items()})

        assert verificar(raiz, termos, usar_git=False) == []
        codigo, _ = _executar_main(raiz, termos)
        assert codigo == 0
