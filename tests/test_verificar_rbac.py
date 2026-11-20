"""Testes de exemplo do verificador de RBAC (Requisitos 7.3, 7.8, 7.9)."""

import json

import pytest

import verificar_rbac as v

BLOB = "ba92f5b4-2d11-453d-a403-e96b0029c9fe"
ESCOPO_OK = "[resourceId('Microsoft.Storage/storageAccounts', parameters('st'))]"


def _atrib(scope=ESCOPO_OK, role=BLOB, **extra):
    return {"name": "a", "scope": scope, "roleDefinitionId": role, **extra}


def test_atribuicao_conforme():
    assert v.verificar_atribuicoes([_atrib()]) == []


@pytest.mark.parametrize(
    "guid", ["8e3af657-a8ff-443c-a75c-2fe8c4bcb635", "B24988AC-6180-42A0-AB88-20F7382DD24C",
             "18d7d88d-d35e-4fb5-a5c3-7773c20a72d9"]
)
def test_funcoes_proibidas_por_guid(guid):
    role = f"/subscriptions/s/providers/Microsoft.Authorization/roleDefinitions/{guid}"
    assert [x.codigo for x in v.verificar_atribuicoes([_atrib(role=role)])] == ["funcao"]


def test_funcao_proibida_por_nome_e_nome_parecido_permitido():
    assert v.verificar_atribuicoes([_atrib(role=None, roleName="owner")])
    assert v.verificar_atribuicoes([_atrib(role=None, roleName="Storage Blob Data Contributor")]) == []


@pytest.mark.parametrize(
    "escopo",
    [None, "", "/subscriptions/abc", "/subscriptions/abc/resourceGroups/rg", "[subscription().id]",
     "[resourceGroup().id]", "[subscriptionResourceId('Microsoft.Resources/resourceGroups', 'rg')]",
     "/providers/Microsoft.Management/managementGroups/mg", "qualquer coisa"],
)
def test_escopos_amplos_ou_desconhecidos_reprovam(escopo):
    assert [x.codigo for x in v.verificar_atribuicoes([_atrib(scope=escopo)])] == ["escopo"]


def test_escopo_literal_de_recurso():
    s = "/subscriptions/a/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/st"
    assert v.verificar_atribuicoes([_atrib(scope=s)]) == []


def test_funcao_nao_identificavel_reprova():
    assert v.verificar_atribuicoes([_atrib(role=None)])


def test_template_resolve_variaveis(tmp_path):
    tpl = {
        "variables": {"papel": f"[subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b24988ac-6180-42a0-ab88-20f7382dd24c')]"},
        "resources": [
            {"type": "Microsoft.Authorization/roleAssignments", "name": "ra", "scope": ESCOPO_OK,
             "properties": {"roleDefinitionId": "[variables('papel')]"}},
            {"type": "Microsoft.Web/sites", "name": "f"},
        ],
    }
    assert [x.codigo for x in v.verificar_template(tpl)] == ["funcao"]
    p = tmp_path / "t.json"
    p.write_text(json.dumps(tpl), encoding="utf-8")
    assert v.main([str(p)]) == 1
    tpl["variables"]["papel"] = BLOB
    p.write_text(json.dumps(tpl), encoding="utf-8")
    assert v.main([str(p)]) == 0


def test_main_arquivo_inexistente(tmp_path):
    assert v.main([str(tmp_path / "nao.json")]) == 2
