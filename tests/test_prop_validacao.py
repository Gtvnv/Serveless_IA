"""Teste de propriedade da validação total (Requisito 5.6)."""

from hypothesis import given, settings, strategies as st

from app.validacao import ResultadoValidacao, validar_texto

# Texto de 0 a 10.000 caracteres, incluindo Unicode e caracteres de controle
# (surrogates excluídos por não serem codificáveis em UTF-8).
_textos = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",)), min_size=0, max_size=10_000
)
_controle = st.text(alphabet=st.characters(max_codepoint=0x1F), min_size=0, max_size=10_000)
_nao_textuais = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(),
    st.binary(max_size=1000),
    st.lists(st.integers(), max_size=20),
    st.dictionaries(st.text(max_size=10), st.integers(), max_size=10),
    st.just(object()),
)


# Feature: serverless-ai-agent-azure-functions, Property 1: Validação total
# **Validates: Requirements 5.6**
@settings(max_examples=200, deadline=None)
@given(st.one_of(_textos, _controle, _nao_textuais))
def test_validar_texto_nunca_lanca(valor):
    resultado = validar_texto(valor)
    assert isinstance(resultado, ResultadoValidacao)
    assert isinstance(resultado.valido, bool)
    if resultado.valido:
        assert isinstance(valor, str) and len(valor) <= 256
        assert resultado.erros == ()
    else:
        assert len(resultado.erros) >= 1
