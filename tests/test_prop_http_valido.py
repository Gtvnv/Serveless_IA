"""Teste de propriedade: entrada válida gera 200 JSON (Requisito 4.4)."""

import json
import logging

from hypothesis import given, settings, strategies as st

from app.http import tratar_http

# Unicode amplo (surrogates excluídos por não serem codificáveis em UTF-8).
_alfabeto = st.characters(blacklist_categories=("Cs",))

_corpos_validos = st.fixed_dictionaries(
    {
        "nome_tarefa": st.text(alphabet=_alfabeto, min_size=1, max_size=256),
        "descricao": st.text(alphabet=_alfabeto, min_size=0, max_size=256),
        "prioridade": st.integers(min_value=1, max_value=5),
        "etiquetas": st.lists(
            st.text(alphabet=_alfabeto, min_size=0, max_size=32), min_size=0, max_size=10
        ),
    }
)


# Feature: serverless-ai-agent-azure-functions, Property 4: Entrada válida gera 200 JSON
# **Validates: Requirements 4.4**
@settings(max_examples=200, deadline=None)
@given(_corpos_validos, st.booleans())
def test_entrada_valida_gera_200_json(corpo, ensure_ascii):
    corpo_bytes = json.dumps(corpo, ensure_ascii=ensure_ascii).encode("utf-8")

    resposta = tratar_http(corpo_bytes, "inv-1", logging.getLogger("teste"))

    assert resposta.status == 200
    assert resposta.cabecalhos["Content-Type"] == "application/json"
    json.loads(resposta.corpo)  # não deve lançar
