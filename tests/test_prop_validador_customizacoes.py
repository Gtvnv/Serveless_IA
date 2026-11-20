"""Teste de propriedade do validador de customizações (tools/validar_customizacoes.py)."""

import contextlib
import io
import tempfile
from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import validar_customizacoes as vc

_letras = st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10)
_nomes_tool = st.lists(
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789._", min_size=1, max_size=12),
    min_size=1,
    max_size=5,
)
_descricoes_validas = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789 ", min_size=1, max_size=200
).filter(lambda s: s.strip() != "")
_descricoes_longas = st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=201, max_size=300)
_modos_invalidos = _letras.filter(lambda s: s not in vc.MODOS_VALIDOS)
_modos_validos = st.sampled_from(vc.MODOS_VALIDOS)
_ext_sem_correspondencia = st.text(alphabet="abc", min_size=1, max_size=5).map(lambda s: "zq" + s)


def _fm(*linhas: str) -> str:
    return "---\n" + "\n".join(linhas) + "\n---\nCorpo.\n"


def _caso(tipo: str, nome: str, linhas: list[str]) -> tuple[str, str]:
    pasta, sufixo = {
        "instructions": ("instructions", ".instructions.md"),
        "prompts": ("prompts", ".prompt.md"),
        "chatmodes": ("chatmodes", ".chatmode.md"),
    }[tipo]
    return f".github/{pasta}/{nome}{sufixo}", _fm(*linhas)


@st.composite
def _casos(draw):
    """Retorna (tipo, nome, linhas_frontmatter, conforme, trecho_do_motivo)."""
    nome = draw(_letras)
    tipo = draw(st.sampled_from(["instructions", "prompts", "chatmodes"]))
    if tipo == "instructions":
        opcao = draw(st.sampled_from(["ok", "ausente", "vazio", "sem_correspondencia"]))
        if opcao == "ok":
            return tipo, nome, ["applyTo: \"**/*.py\""], True, ""
        if opcao == "ausente":
            return tipo, nome, ["outro: x"], False, "applyTo ausente"
        if opcao == "vazio":
            return tipo, nome, ["applyTo: \"\""], False, "applyTo vazio"
        ext = draw(_ext_sem_correspondencia)
        return tipo, nome, [f"applyTo: \"**/*.{ext}\""], False, "applyTo sem correspondência"
    if tipo == "prompts":
        opcao = draw(st.sampled_from(["ok", "desc_vazio", "desc_longo", "mode_invalido"]))
        desc = draw(_descricoes_validas)
        modo = draw(_modos_validos)
        if opcao == "ok":
            return tipo, nome, [f'description: "{desc}"', f"mode: {modo}"], True, ""
        if opcao == "desc_vazio":
            return tipo, nome, ['description: ""', f"mode: {modo}"], False, "description vazio"
        if opcao == "desc_longo":
            longa = draw(_descricoes_longas)
            return tipo, nome, [f'description: "{longa}"', f"mode: {modo}"], False, "description excede"
        invalido = draw(_modos_invalidos)
        return tipo, nome, [f'description: "{desc}"', f"mode: {invalido}"], False, "mode inválido"
    opcao = draw(st.sampled_from(["ok", "vazio", "curinga", "ausente"]))
    if opcao == "ok":
        tools = draw(_nomes_tool)
        return tipo, nome, [f"tools: [{', '.join(tools)}]"], True, ""
    if opcao == "vazio":
        return tipo, nome, ["tools: []"], False, "tools vazio"
    if opcao == "ausente":
        return tipo, nome, ["description: \"x\""], False, "tools ausente"
    tools = draw(_nomes_tool) + ["*"]
    draw(st.randoms()).shuffle(tools)
    return tipo, nome, [f"tools: [{', '.join(tools)}]"], False, "tools contém curinga"


def _rodar_main(raiz: Path) -> tuple[int, str]:
    saida = io.StringIO()
    with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(io.StringIO()):
        codigo = vc.main(["--raiz", str(raiz)])
    return codigo, saida.getvalue()


# Feature: serverless-ai-agent-azure-functions, Property 12: Validador de customizações
# Validates: Requirements 1.6, 2.6, 3.2
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(caso=_casos())
def test_propriedade_validador_customizacoes(caso):
    tipo, nome, linhas, conforme, trecho = caso
    caminho, texto = _caso(tipo, nome, linhas)
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        (raiz / "src").mkdir()
        (raiz / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
        alvo = raiz / caminho
        alvo.parent.mkdir(parents=True)
        alvo.write_text(texto, encoding="utf-8")

        problemas = vc.validar_repositorio(raiz)
        codigo, saida = _rodar_main(raiz)

    if conforme:
        assert problemas == []
        assert codigo == 0
        assert saida == ""
    else:
        assert problemas, "não conformidade não reportada"
        assert all(p.caminho == caminho for p in problemas)
        assert any(trecho in p.motivo for p in problemas), [str(p) for p in problemas]
        assert codigo == 1
        assert caminho in saida
        assert trecho in saida
