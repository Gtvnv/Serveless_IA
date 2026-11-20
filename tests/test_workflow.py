"""Testes de exemplo (análise estática) do workflow .github/workflows/ci-cd.yml.

Validates: Requirements 6.1, 6.4, 6.5, 6.6, 6.7, 8.5, 11.4
"""
import re
from pathlib import Path

import pytest
import yaml

WORKFLOW = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "ci-cd.yml"
GUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


@pytest.fixture(scope="module")
def texto():
    return WORKFLOW.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def wf(texto):
    return yaml.safe_load(texto)


def _idx(steps, pred):
    for i, s in enumerate(steps):
        if pred(s):
            return i
    raise AssertionError("etapa não encontrada")


def _run(s):
    return s.get("run", "")


def _uses(s):
    return s.get("uses", "")


def test_ordem_das_etapas_do_job_de_testes(wf):
    steps = wf["jobs"]["testes"]["steps"]
    checkout = _idx(steps, lambda s: _uses(s).startswith("actions/checkout"))
    verif = _idx(steps, lambda s: "verificador_seguranca" in _run(s))
    instal = _idx(steps, lambda s: "pip install" in _run(s))
    compil = _idx(steps, lambda s: "compileall" in _run(s))
    testes = _idx(steps, lambda s: "pytest" in _run(s))
    assert checkout < verif < instal < compil < testes


def test_login_e_publicacao_apos_testes_no_deploy(wf):
    steps = wf["jobs"]["deploy"]["steps"]
    checkout = _idx(steps, lambda s: _uses(s).startswith("actions/checkout"))
    login = _idx(steps, lambda s: _uses(s).startswith("azure/login"))
    publ = _idx(steps, lambda s: _uses(s).startswith("Azure/functions-action"))
    assert checkout < login < publ


def test_verificador_antes_de_build_testes_e_deploy(wf):
    steps = wf["jobs"]["testes"]["steps"]
    verif = _idx(steps, lambda s: "verificador_seguranca" in _run(s))
    build = _idx(steps, lambda s: "compileall" in _run(s))
    testes = _idx(steps, lambda s: "pytest" in _run(s))
    assert verif < build and verif < testes
    # O deploy depende do job que contém o verificador.
    assert wf["jobs"]["deploy"]["needs"] == "testes" or "testes" in wf["jobs"]["deploy"]["needs"]


def test_permissoes_minimas(wf):
    assert wf["permissions"] == {"contents": "read"}
    perms = wf["jobs"]["deploy"]["permissions"]
    assert perms == {"contents": "read", "id-token": "write"}
    assert "permissions" not in wf["jobs"]["testes"] or wf["jobs"]["testes"]["permissions"] == {"contents": "read"}


def test_sem_ids_literais_nem_credenciais_de_longa_duracao(texto):
    sem_comentarios = "\n".join(l.split("#", 1)[0] for l in texto.splitlines())
    assert not GUID.search(sem_comentarios)
    baixo = sem_comentarios.lower()
    for proibido in ("client-secret", "client_secret", "password", "senha", "creds:", "credentials"):
        assert proibido not in baixo
    # Nenhum segredo de longa duração: apenas IDs do OIDC são lidos de secrets.
    usados = set(re.findall(r"secrets\.([A-Za-z0-9_]+)", sem_comentarios))
    assert usados <= {"AZURE_CLIENT_ID", "AZURE_TENANT_ID", "AZURE_SUBSCRIPTION_ID"}


def test_login_oidc_com_secrets_ou_vars(wf):
    steps = wf["jobs"]["deploy"]["steps"]
    login = steps[_idx(steps, lambda s: _uses(s).startswith("azure/login"))]
    w = login["with"]
    assert set(w) == {"client-id", "tenant-id", "subscription-id"}
    for v in w.values():
        assert re.fullmatch(r"\$\{\{\s*(secrets|vars)\.[A-Z0-9_]+\s*\}\}", str(v))


def test_deploy_com_environment_e_needs(wf):
    deploy = wf["jobs"]["deploy"]
    assert deploy["environment"] == "production"
    assert "testes" in ([deploy["needs"]] if isinstance(deploy["needs"], str) else deploy["needs"])


def test_deploy_restrito_a_push_na_branch_principal(wf):
    cond = wf["jobs"]["deploy"]["if"]
    assert "github.event_name == 'push'" in cond
    assert "refs/heads/main" in cond
    assert "testes" not in wf["jobs"] or "if" not in wf["jobs"]["testes"]
    # PyYAML interpreta a chave `on` como True.
    gatilhos = wf.get("on", wf.get(True))
    assert "push" in gatilhos and "pull_request" in gatilhos
    assert gatilhos["push"]["branches"] == ["main"]
