"""Testes de exemplo do template Bicep (Requisitos 7.1 a 7.5, 7.8 e 7.9).

Compila ``infra/main.bicep`` com ``bicep build --stdout`` (ou ``az bicep build``) e
inspeciona o ARM template resultante. O JSON fica apenas em memória e em um
diretório temporário. Sem a CLI, os testes são ignorados.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
BICEP = RAIZ / "infra" / "main.bicep"
BICEPPARAM = RAIZ / "infra" / "main.bicepparam"

sys.path.insert(0, str(RAIZ / "tools"))
import verificar_rbac  # noqa: E402

FUNCOES_PROIBIDAS = (
    "8e3af657-a8ff-443c-a75c-2fe8c4bcb635",  # Owner
    "b24988ac-6180-42a0-ab88-20f7382dd24c",  # Contributor
    "18d7d88d-d35e-4fb5-a5c3-7773c20a72d9",  # User Access Administrator
)


def _comando_compilacao() -> list[str] | None:
    bicep = shutil.which("bicep")
    if bicep:
        return [bicep, "build", str(BICEP), "--stdout"]
    az = shutil.which("az")
    if az:
        return [az, "bicep", "build", "--file", str(BICEP), "--stdout"]
    return None


@pytest.fixture(scope="module")
def template() -> dict:
    comando = _comando_compilacao()
    if comando is None:
        pytest.skip("CLI do Bicep (bicep ou az bicep) não encontrada")
    try:
        r = subprocess.run(comando, capture_output=True, timeout=180)
    except (OSError, subprocess.TimeoutExpired) as e:
        pytest.skip(f"CLI do Bicep indisponível: {e}")
    saida = r.stdout.decode("utf-8", errors="replace")
    if r.returncode != 0:
        pytest.fail(f"bicep build falhou: {r.stderr.decode('utf-8', errors='replace')}")
    return json.loads(saida.lstrip("\ufeff"))


@pytest.fixture(scope="module")
def recursos(template: dict) -> list[dict]:
    r = template["resources"]
    return list(r.values()) if isinstance(r, dict) else r


def _do_tipo(recursos: list[dict], tipo: str) -> list[dict]:
    return [r for r in recursos if r["type"].lower() == tipo.lower()]


def test_recursos_exatos(recursos: list[dict]) -> None:
    """Req. 7.1: Function_App, plano, armazenamento, Application Insights e RBAC."""
    tipos = sorted(r["type"] for r in recursos)
    assert tipos == sorted(
        [
            "Microsoft.Storage/storageAccounts",
            "Microsoft.Insights/components",
            "Microsoft.Web/serverfarms",
            "Microsoft.Web/sites",
            "Microsoft.Authorization/roleAssignments",
        ]
    )


def test_identidade_gerenciada_de_sistema(recursos: list[dict]) -> None:
    """Req. 7.2."""
    (site,) = _do_tipo(recursos, "Microsoft.Web/sites")
    assert site["identity"]["type"] == "SystemAssigned"


def test_https_e_tls(recursos: list[dict]) -> None:
    """Req. 7.4 e 7.5."""
    (site,) = _do_tipo(recursos, "Microsoft.Web/sites")
    assert site["properties"]["httpsOnly"] is True
    assert site["properties"]["siteConfig"]["minTlsVersion"] == "1.2"


def test_parametros_para_nomes_regiao_e_sku(template: dict) -> None:
    """Req. 7.6: nomes, região e SKU são parâmetros."""
    parametros = template["parameters"]
    esperados = {
        "nomeFunctionApp",
        "nomePlano",
        "nomeContaArmazenamento",
        "nomeApplicationInsights",
        "regiao",
        "skuPlano",
        "skuArmazenamento",
    }
    assert esperados <= set(parametros)


def test_sem_segredos(template: dict) -> None:
    """Req. 7.4/8: sem chaves, senhas nem connection strings com valor no template."""
    texto = json.dumps(template)
    texto += BICEP.read_text(encoding="utf-8") + BICEPPARAM.read_text(encoding="utf-8")
    assert not re.search(r"AccountKey\s*=", texto, re.IGNORECASE)
    assert not re.search(r"(SharedAccessKey|SharedAccessSignature|sig)=", texto)
    assert not re.search(r"listKeys|listAccountSas|listConnectionStrings", texto, re.IGNORECASE)
    assert not re.search(r"(password|senha|secret|client_?secret)\s*[:=]\s*['\"][^'\"]+['\"]", texto, re.IGNORECASE)
    # Nenhum parâmetro é secure (não há segredo a receber) e nenhum aceita chave.
    for nome, definicao in template["parameters"].items():
        assert definicao["type"] not in ("securestring", "secureObject"), nome
        assert not re.search(r"key|senha|password|secret|token", nome, re.IGNORECASE), nome
    # O armazenamento do host usa identidade gerenciada, não chave.
    (site,) = _do_tipo(template["resources"], "Microsoft.Web/sites")
    nomes = {s["name"] for s in site["properties"]["siteConfig"]["appSettings"]}
    assert "AzureWebJobsStorage__accountName" in nomes
    assert "AzureWebJobsStorage" not in nomes


def test_rbac_no_recurso_sem_funcoes_proibidas(recursos: list[dict]) -> None:
    """Req. 7.3: escopo em um recurso, dependência da criação dele e sem Owner/Contributor/UAA."""
    atribuicoes = _do_tipo(recursos, "Microsoft.Authorization/roleAssignments")
    assert atribuicoes
    for a in atribuicoes:
        assert "Microsoft.Storage/storageAccounts" in a["scope"]
        assert any("Microsoft.Storage/storageAccounts" in d for d in a["dependsOn"])
        assert any("Microsoft.Web/sites" in d for d in a["dependsOn"])
        assert "principalId" in a["properties"]
    texto = json.dumps(atribuicoes).lower()
    assert not any(g in texto for g in FUNCOES_PROIBIDAS)


def test_verificar_rbac_sem_violacoes(template: dict, tmp_path: Path) -> None:
    """Req. 7.8 e 7.9: verificar_template e verificar_arquivo não reportam violações."""
    assert verificar_rbac.verificar_template(template) == []
    arquivo = tmp_path / "main.json"
    arquivo.write_text(json.dumps(template), encoding="utf-8")
    assert verificar_rbac.verificar_arquivo(arquivo) == []
