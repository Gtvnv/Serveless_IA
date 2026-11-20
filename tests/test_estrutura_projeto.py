"""Testes de exemplo da estrutura do Projeto_Exemplo (análise estática).

Não importa ``azure.functions``: ``src/function_app.py`` é lido e analisado via ``ast``.

**Validates: Requirements 4.1, 4.2, 8.11**
"""

import ast
import json
import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
FUNCTION_APP = SRC / "function_app.py"


def _arvore() -> ast.Module:
    return ast.parse(FUNCTION_APP.read_text(encoding="utf-8"))


def _decoradores_de_funcoes() -> dict:
    """Mapeia nome da função -> lista de decoradores (ast.Call/ast.expr)."""
    return {
        no.name: no.decorator_list
        for no in ast.walk(_arvore())
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _nome_decorador(dec: ast.expr) -> str:
    alvo = dec.func if isinstance(dec, ast.Call) else dec
    return alvo.attr if isinstance(alvo, ast.Attribute) else getattr(alvo, "id", "")


def _decoradores_por_tipo(tipo: str) -> list:
    return [
        d
        for decs in _decoradores_de_funcoes().values()
        for d in decs
        if _nome_decorador(d) == tipo
    ]


def test_function_app_existe():
    assert FUNCTION_APP.is_file()


def test_funcao_http_presente():
    assert _decoradores_por_tipo("route"), "Função HTTP (@app.route) ausente"


def test_funcao_temporizador_fila_ou_blob_presente():
    gatilhos = {"timer_trigger", "queue_trigger", "blob_trigger"}
    presentes = [
        d
        for decs in _decoradores_de_funcoes().values()
        for d in decs
        if _nome_decorador(d) in gatilhos
    ]
    assert presentes, "Função de temporizador/fila/blob ausente"


def test_auth_level_http_nao_e_anonymous():
    rotas = _decoradores_por_tipo("route")
    assert rotas
    for rota in rotas:
        niveis = [kw.value for kw in rota.keywords if kw.arg == "auth_level"]
        assert niveis, "auth_level deve ser declarado explicitamente"
        assert "ANONYMOUS" not in ast.unparse(niveis[0]).upper()


def test_anonymous_nao_aparece_no_codigo():
    assert not re.search(r"ANONYMOUS", FUNCTION_APP.read_text(encoding="utf-8"), re.I)


def test_host_json_presente_e_valido():
    caminho = SRC / "host.json"
    assert caminho.is_file()
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    assert dados.get("version") == "2.0"


def test_requirements_presente_e_com_azure_functions():
    caminho = SRC / "requirements.txt"
    assert caminho.is_file()
    linhas = [l.strip().lower() for l in caminho.read_text(encoding="utf-8").splitlines()]
    assert any(l.startswith("azure-functions") for l in linhas)


def test_local_settings_example_somente_placeholders():
    caminho = SRC / "local.settings.json.example"
    assert caminho.is_file()
    texto = caminho.read_text(encoding="utf-8")
    valores = json.loads(texto)["Values"]
    # Chaves sensíveis devem ser placeholders no formato <...>.
    for chave in ("AzureWebJobsStorage", "APPLICATIONINSIGHTS_CONNECTION_STRING"):
        assert re.fullmatch(r"<[^<>]+>", valores[chave]), chave
    assert "<" in valores["KEY_VAULT_URL"]
    # Nenhum padrão de credencial real.
    assert not re.search(r"AccountKey=|SharedAccessSignature|InstrumentationKey=[0-9a-f-]{36}", texto, re.I)
    assert not re.search(r"[A-Za-z0-9+/]{40,}={0,2}", texto)


def test_local_settings_real_ignorado_pelo_git():
    gitignore = (SRC.parent / ".gitignore").read_text(encoding="utf-8")
    assert "local.settings.json" in gitignore
