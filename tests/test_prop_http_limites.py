"""Teste de propriedade dos limites de tamanho na camada HTTP (Requisito 4.8)."""

import json
import logging

from hypothesis import HealthCheck, given, settings, strategies as st

from app.http import tratar_http

LIMITE_CORPO = 1048576  # 1 MB
LIMITE_TEXTO = 256


def _processar_nao_deve_ser_chamado(entrada):
    raise AssertionError("processar não deve ser chamado para corpo rejeitado")


_logger = logging.getLogger("teste_http_limites")

# Corpos grandes por repetição (não por st.binary), sempre > 1 MB.
_corpos_excedidos = st.builds(
    lambda bloco, excesso: (bloco * (LIMITE_CORPO // len(bloco) + 2))[: LIMITE_CORPO + excesso],
    st.sampled_from([b"a", b"{", b" ", b'{"nome_tarefa": "x"}', b"\xff\xfe", b"0123456789"]),
    st.integers(min_value=1, max_value=20_000),
)

_caractere = st.characters(blacklist_categories=("Cs",), blacklist_characters='"\\')


@st.composite
def _corpos_com_texto_longo(draw):
    """Corpo JSON de até 1 MB com um campo de texto de mais de 256 caracteres."""
    base = draw(st.sampled_from(["a", "é", "日", "😀"]))
    extra = draw(st.integers(min_value=1, max_value=2000))
    longo = draw(st.one_of(st.just(base), _caractere)) * (LIMITE_TEXTO + extra)
    campo = draw(st.sampled_from(["nome_tarefa", "descricao"]))
    dados = {"nome_tarefa": "tarefa", "descricao": "", "prioridade": 3, "etiquetas": []}
    dados[campo] = longo
    # Preenchimento opcional para aproximar o corpo do limite de 1 MB.
    if draw(st.booleans()):
        dados["preenchimento"] = "p" * draw(st.integers(min_value=0, max_value=900_000))
    corpo = json.dumps(dados, ensure_ascii=draw(st.booleans())).encode("utf-8")
    assert len(corpo) <= LIMITE_CORPO
    return corpo


# Feature: serverless-ai-agent-azure-functions, Property 3: Limites de tamanho
# **Validates: Requirements 4.8**
@settings(max_examples=100, deadline=None, suppress_health_check=list(HealthCheck))
@given(_corpos_excedidos)
def test_corpo_acima_de_1mb_responde_413(corpo):
    assert len(corpo) > LIMITE_CORPO
    resposta = tratar_http(corpo, "inv-1", _logger, _processar_nao_deve_ser_chamado)
    assert resposta.status == 413


# Feature: serverless-ai-agent-azure-functions, Property 3: Limites de tamanho
# **Validates: Requirements 4.8**
@settings(max_examples=100, deadline=None, suppress_health_check=list(HealthCheck))
@given(_corpos_com_texto_longo())
def test_texto_acima_de_256_caracteres_responde_400(corpo):
    assert len(corpo) <= LIMITE_CORPO
    resposta = tratar_http(corpo, "inv-2", _logger, _processar_nao_deve_ser_chamado)
    assert resposta.status == 400
