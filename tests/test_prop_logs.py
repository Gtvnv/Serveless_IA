"""Teste de propriedade: logs não contêm Segredos nem dados pessoais (Requisito 8.10)."""

import json

import pytest
from hypothesis import given, settings, strategies as st

from app.http import FUNCAO_EVENTO, FUNCAO_HTTP, tratar_evento, tratar_http
from app.logging_seguro import redigir, registrar_erro

_MAIUSC = "QXZJKWVY"
_ALNUM = "abcdefghijklmnopqrstuvwxyz0123456789"


class _LoggerFake:
    def __init__(self):
        self.chamadas = []

    def error(self, msg, *args, **kwargs):
        self.chamadas.append(msg % args if args else msg)


def _palavra(min_size=4, max_size=8):
    return st.text(alphabet=_MAIUSC, min_size=min_size, max_size=max_size).map(str.capitalize)


_nomes = st.lists(_palavra(), min_size=1, max_size=3).map(" ".join)
_emails = st.builds(
    lambda u, d, t: f"{u}@{d}.{t}",
    st.text(alphabet=_ALNUM, min_size=1, max_size=10),
    st.text(alphabet=_ALNUM, min_size=2, max_size=10),
    st.sampled_from(["com", "com.br", "org", "net"]),
)
# Local-part igual ao nome (caso "joao@x.com" com nome "joao").
_cpfs = st.one_of(
    st.from_regex(r"\A\d{3}\.\d{3}\.\d{3}-\d{2}\Z"),
    st.from_regex(r"\A\d{11}\Z"),
)
_telefones = st.one_of(
    st.from_regex(r"\A\(\d{2}\) 9\d{4}-\d{4}\Z"),
    st.from_regex(r"\A\+55 \d{2} 9\d{4}-\d{4}\Z"),
    st.from_regex(r"\A\d{2}9\d{8}\Z"),
)
_enderecos = st.builds(
    lambda tipo, rua, num: f"{tipo} {rua}, {num}",
    st.sampled_from(["Rua", "Avenida", "Alameda", "Travessa"]),
    _nomes,
    st.integers(min_value=1, max_value=9999),
)
_segredos = st.one_of(
    st.text(alphabet=_ALNUM, min_size=24, max_size=40).map(lambda s: "sk-" + s),
    st.text(alphabet=_ALNUM + "+/", min_size=30, max_size=50).map(lambda s: "AccountKey=" + s + "=="),
    st.text(alphabet=_ALNUM, min_size=20, max_size=40).map(lambda s: "ghp_" + s),
)

# E-mail cujo usuário coincide com um nome informado (ex.: "joao@x.com" com nome "joao").
_nome_simples = st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=4, max_size=8)
_emails_com_nome = st.builds(
    lambda n, d: (n, f"{n}@{d}.com"),
    _nome_simples,
    st.text(alphabet=_ALNUM, min_size=2, max_size=8),
)

_pessoais = st.one_of(
    _nomes,
    _emails,
    _cpfs,
    _telefones,
    _enderecos,
    _emails_com_nome.map(lambda t: t[1]),
)


def _extrair_valor_segredo(s: str) -> str:
    return s.split("=", 1)[1] if s.startswith("AccountKey=") else s


class _Caso:
    def __init__(self, pessoais, segredos, campo_pii, etiqueta_curta):
        self.pessoais = pessoais
        self.segredos = segredos
        self.campo_pii = campo_pii
        self.etiqueta_curta = etiqueta_curta

    def sensiveis(self):
        return list(self.pessoais) + [_extrair_valor_segredo(s) for s in self.segredos]

    def corpo(self):
        valores = self.sensiveis()
        etiquetas = [self.etiqueta_curta] + [v for v in valores if len(v) <= 32]
        return {
            "nome_tarefa": "Tarefa " + valores[0],
            "descricao": " ".join(valores),  # <= 256 caracteres pelos limites dos geradores
            "prioridade": 3,
            "etiquetas": etiquetas[:10],
        }


_casos = st.builds(
    _Caso,
    st.lists(_pessoais, min_size=1, max_size=3).flatmap(
        lambda ps: st.just(ps)
        if not any("@" in p for p in ps)
        else st.just(ps + [p.split("@")[0] for p in ps if "@" in p and len(p.split("@")[0]) >= 4][:1])
    ),
    st.lists(_segredos, min_size=0, max_size=1),
    st.sampled_from(["nome_tarefa", "descricao", "etiquetas"]),
    st.sampled_from(["a", "x", "ab", "1"]),
)


def _processar_com_excecao(caso):
    texto = "falha ao processar " + " | ".join(
        [f"valor {v}" for v in caso.pessoais] + list(caso.segredos)
    )

    def processar(_entrada):
        raise ValueError(texto)

    return processar


def _assert_sem_vazamento(logs, caso, funcao=None, invocacao=None):
    assert logs
    for linha in logs:
        # Campos técnicos não podem ser corrompidos pela redação (etiquetas curtas, etc.).
        if funcao is not None:
            assert f"funcao={funcao} " in linha
        if invocacao is not None:
            assert f"invocacao={invocacao} " in linha
        # Campos técnicos (funcao/invocacao/tipo_excecao) são verificados acima; o vazamento
        # é checado no restante da linha, evitando colisão com o id de invocação.
        resto = linha.split("mensagem=", 1)[-1] if invocacao is not None else linha
        for v in caso.sensiveis():
            assert v not in resto, f"vazou {v!r} em {linha!r}"


# Feature: serverless-ai-agent-azure-functions, Property 8: Logs não contêm Segredos nem dados pessoais
# **Validates: Requirements 8.10**
@settings(max_examples=150, deadline=None)
@given(_casos, st.text(alphabet="abcdef0123456789-", min_size=8, max_size=36))
def test_logs_http_sem_segredos_nem_dados_pessoais(caso, invocacao):
    logger = _LoggerFake()
    corpo = json.dumps(caso.corpo(), ensure_ascii=False).encode("utf-8")
    tratar_http(corpo, invocacao, logger, processar=_processar_com_excecao(caso))
    _assert_sem_vazamento(logger.chamadas, caso, FUNCAO_HTTP, invocacao)


# Feature: serverless-ai-agent-azure-functions, Property 8: Logs não contêm Segredos nem dados pessoais
# **Validates: Requirements 8.10**
@settings(max_examples=150, deadline=None)
@given(_casos, st.text(alphabet="abcdef0123456789-", min_size=8, max_size=36))
def test_logs_evento_sem_segredos_nem_dados_pessoais(caso, invocacao):
    logger = _LoggerFake()
    with pytest.raises(ValueError):
        tratar_evento(caso.corpo(), invocacao, logger, processar=_processar_com_excecao(caso))
    _assert_sem_vazamento(logger.chamadas, caso, FUNCAO_EVENTO, invocacao)


# Feature: serverless-ai-agent-azure-functions, Property 8: Logs não contêm Segredos nem dados pessoais
# **Validates: Requirements 8.10**
@settings(max_examples=150, deadline=None)
@given(_casos)
def test_redigir_e_registrar_erro_sem_vazamento(caso):
    texto = " ; ".join(
        [f"cliente {v} contato" for v in caso.pessoais] + list(caso.segredos)
    )
    # Sem valores exatos, a redação por padrão cobre tudo exceto nomes (não detectáveis por padrão).
    saida = redigir(texto)
    nomes = [v for v in caso.pessoais if v.replace(" ", "").isalpha() and not v.startswith(("Rua", "Avenida", "Alameda", "Travessa"))]
    nomes += [v for v in caso.pessoais if any(p.startswith(v + "@") for p in caso.pessoais)]
    assert not any(v in saida for v in caso.sensiveis() if v not in nomes)

    # Com os valores exatos informados, nada vaza.
    assert not any(v in redigir(texto, caso.sensiveis()) for v in caso.sensiveis())

    logger = _LoggerFake()
    registrar_erro(logger, "tratar_http", "abc12345", ValueError(texto), caso.sensiveis())
    _assert_sem_vazamento(logger.chamadas, caso)
