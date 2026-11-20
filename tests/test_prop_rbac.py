"""Teste de propriedade do verificador de RBAC de menor privilégio.

# Feature: serverless-ai-agent-azure-functions, Property 13: Verificador de RBAC de menor privilégio

**Validates: Requirements 7.3, 7.8, 7.9**
"""

import uuid

from hypothesis import given, settings
from hypothesis import strategies as st

import verificar_rbac as v

PROIBIDAS_GUID = [
    "8e3af657-a8ff-443c-a75c-2fe8c4bcb635",  # Owner
    "b24988ac-6180-42a0-ab88-20f7382dd24c",  # Contributor
    "18d7d88d-d35e-4fb5-a5c3-7773c20a72d9",  # User Access Administrator
]
PROIBIDAS_NOME = ["Owner", "Contributor", "User Access Administrator"]
PERMITIDAS_NOME = [
    "Storage Blob Data Contributor",
    "Key Vault Secrets User",
    "Storage Blob Data Reader",
    "Reader",
]

_nome_recurso = st.from_regex(r"[a-z][a-z0-9]{2,15}", fullmatch=True)
_prefixo_sub = st.uuids().map(lambda u: f"/subscriptions/{u}")
_prefixo_rg = st.tuples(_prefixo_sub, _nome_recurso).map(lambda t: f"{t[0]}/resourceGroups/{t[1]}")
_tipo_recurso = st.sampled_from(
    [
        ("Microsoft.Storage", "storageAccounts"),
        ("Microsoft.KeyVault", "vaults"),
        ("Microsoft.Web", "sites"),
        ("Microsoft.CognitiveServices", "accounts"),
    ]
)

# Escopo de um único recurso: ID literal ou expressão resourceId.
escopo_recurso = st.one_of(
    st.tuples(_prefixo_rg, _tipo_recurso, _nome_recurso).map(
        lambda t: f"{t[0]}/providers/{t[1][0]}/{t[1][1]}/{t[2]}"
    ),
    st.tuples(_tipo_recurso, _nome_recurso).map(
        lambda t: f"[resourceId('{t[0][0]}/{t[0][1]}', '{t[1]}')]"
    ),
    _tipo_recurso.map(lambda t: f"[resourceId('{t[0]}/{t[1]}', parameters('nome'))]"),
)

# Escopos que NÃO são de um único recurso.
escopo_nao_recurso = st.one_of(
    st.just(None),
    st.just(""),
    st.just("   "),
    _prefixo_sub,
    _prefixo_rg,
    st.just("[subscription().id]"),
    st.just("[resourceGroup().id]"),
    st.just("[subscriptionResourceId('Microsoft.Resources/resourceGroups', 'rg')]"),
    _nome_recurso.map(lambda n: f"/providers/Microsoft.Management/managementGroups/{n}"),
    _nome_recurso.map(lambda n: f"[tenantResourceId('Microsoft.Management/managementGroups', '{n}')]"),
)


def _caixa(texto: str, modo: int) -> str:
    return (texto, texto.upper(), texto.lower())[modo]


def _guid_em(guid: str, forma: int) -> str:
    if forma == 0:
        return guid
    return f"/subscriptions/{uuid.uuid4()}/providers/Microsoft.Authorization/roleDefinitions/{guid}"


# Cada função é (kwargs da atribuição, é_proibida).
funcao_proibida = st.one_of(
    st.tuples(st.sampled_from(PROIBIDAS_GUID), st.integers(0, 1), st.integers(0, 2)).map(
        lambda t: ({"roleDefinitionId": _guid_em(_caixa(t[0], t[2]), t[1])}, True)
    ),
    st.tuples(st.sampled_from(PROIBIDAS_NOME), st.integers(0, 2)).map(
        lambda t: ({"roleName": _caixa(t[0], t[1])}, True)
    ),
)
funcao_permitida = st.one_of(
    st.tuples(st.uuids(), st.integers(0, 1))
    .filter(lambda t: str(t[0]) not in PROIBIDAS_GUID)
    .map(lambda t: ({"roleDefinitionId": _guid_em(str(t[0]), t[1])}, False)),
    st.sampled_from(PERMITIDAS_NOME).map(lambda n: ({"roleName": n}, False)),
)


@st.composite
def atribuicao(draw):
    """Gera (atribuição, esperada_conforme)."""
    escopo_ok = draw(st.booleans())
    escopo = draw(escopo_recurso if escopo_ok else escopo_nao_recurso)
    kwargs, proibida = draw(st.one_of(funcao_proibida, funcao_permitida))
    item = {"name": f"a{draw(st.integers(0, 10**6))}", "scope": escopo, **kwargs}
    return item, escopo_ok and not proibida


@st.composite
def conjunto(draw):
    itens = draw(st.lists(atribuicao(), min_size=0, max_size=8))
    return [i for i, _ in itens], all(ok for _, ok in itens)


@settings(max_examples=200, deadline=None)
@given(conjunto())
def test_conforme_se_e_somente_se_escopo_de_recurso_e_funcao_permitida(par):
    atribuicoes, esperado_conforme = par
    violacoes = v.verificar_atribuicoes(atribuicoes)
    assert (violacoes == []) is esperado_conforme


@settings(max_examples=100, deadline=None)
@given(st.lists(atribuicao(), min_size=1, max_size=8))
def test_cada_atribuicao_nao_conforme_gera_violacao(itens):
    # Verificar um conjunto equivale a verificar cada atribuição isoladamente.
    atribuicoes = [dict(i, name=f"x{n}") for n, (i, _) in enumerate(itens)]
    violacoes = v.verificar_atribuicoes(atribuicoes)
    com_violacao = {x.atribuicao for x in violacoes}
    esperados = {f"x{n}" for n, (_, ok) in enumerate(itens) if not ok}
    assert com_violacao == esperados
