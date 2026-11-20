"""Teste de propriedade: exceção em função HTTP gera 500 genérico e log estruturado (Requisito 4.5)."""

import json

from hypothesis import given, settings, strategies as st

from app.http import FUNCAO_HTTP, MENSAGEM_ERRO_GENERICO, tratar_http

_CORPO_VALIDO = json.dumps(
    {"nome_tarefa": "Tarefa #1", "descricao": "Desc #2", "prioridade": 3, "etiquetas": ["#e1"]}
).encode("utf-8")

# Letras maiúsculas raras: o redator não as altera e não ocorrem na mensagem genérica.
_mensagens = st.text(alphabet="QXZJKW", min_size=6, max_size=60)
_nomes_tipo = st.text(alphabet="QXZJKW", min_size=6, max_size=30).map(lambda s: "Err" + s)
_invocacoes = st.text(alphabet="abcdef0123456789-", min_size=8, max_size=36).filter(
    lambda s: s.replace("-", "").isalnum() and not s[0].isdigit()
)
_bases = st.sampled_from([Exception, ValueError, RuntimeError, KeyError, OSError, TypeError])


class _LoggerFake:
    def __init__(self):
        self.chamadas = []

    def error(self, msg, *args, **kwargs):
        self.chamadas.append(msg % args if args else msg)


# Feature: serverless-ai-agent-azure-functions, Property 6: Exceção em função HTTP gera 500 genérico e log estruturado
# **Validates: Requirements 4.5**
@settings(max_examples=100, deadline=None)
@given(_bases, _nomes_tipo, _mensagens, _invocacoes)
def test_excecao_gera_500_generico_e_log_estruturado(base, nome_tipo, mensagem, invocacao):
    tipo = type(nome_tipo, (base,), {})

    def processar(_entrada):
        raise tipo(mensagem)

    logger = _LoggerFake()
    resposta = tratar_http(_CORPO_VALIDO, invocacao, logger, processar=processar)

    assert resposta.status == 500
    assert json.loads(resposta.corpo) == {"erro": MENSAGEM_ERRO_GENERICO}
    assert mensagem not in resposta.corpo
    assert nome_tipo not in resposta.corpo
    assert "Traceback" not in resposta.corpo

    assert len(logger.chamadas) == 1
    log = logger.chamadas[0]
    assert f"funcao={FUNCAO_HTTP}" in log
    assert f"invocacao={invocacao}" in log
    assert f"tipo_excecao={nome_tipo}" in log
    assert f"mensagem={str(tipo(mensagem))}" in log
    assert "Traceback" not in log
