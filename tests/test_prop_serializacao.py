"""Teste de propriedade do round-trip de serialização (Requisito 5.7)."""

from hypothesis import given, settings, strategies as st

from app.negocio import desserializar, serializar
from app.validacao import PedidoEntrada

# Unicode amplo (surrogates excluídos por não serem codificáveis em UTF-8),
# incluindo caracteres de controle, emojis e aspas/barras.
_alfabeto = st.characters(blacklist_categories=("Cs",))

_pedidos = st.builds(
    PedidoEntrada,
    nome_tarefa=st.text(alphabet=_alfabeto, min_size=1, max_size=256),
    descricao=st.text(alphabet=_alfabeto, min_size=0, max_size=256),
    prioridade=st.integers(min_value=1, max_value=5),
    etiquetas=st.lists(
        st.text(alphabet=_alfabeto, min_size=0, max_size=32), min_size=0, max_size=10
    ).map(tuple),
)


# Feature: serverless-ai-agent-azure-functions, Property 5: Round-trip de serialização
# **Validates: Requirements 5.7**
@settings(max_examples=200, deadline=None)
@given(_pedidos)
def test_round_trip_serializacao(pedido):
    assert desserializar(serializar(pedido)) == pedido
