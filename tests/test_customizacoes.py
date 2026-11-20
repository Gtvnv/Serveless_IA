"""Testes de exemplo das customizações do Agente_Copilot (.github/).

Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 9.6
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from validar_customizacoes import (
    MODOS_VALIDOS,
    extrair_frontmatter,
    validar_repositorio,
)

RAIZ = Path(__file__).resolve().parent.parent
GITHUB = RAIZ / ".github"
TAMANHO_MAXIMO_BYTES = 50 * 1024

PROMPTS_ESPERADOS = {
    "criar-http-trigger",
    "criar-trigger-temporizador-fila-blob",
    "gerar-testes",
    "deploy-azure",
    "revisar-seguranca",
}


def _ler(caminho: Path) -> str:
    return caminho.read_text(encoding="utf-8")


def _normalizar(texto: str) -> str:
    return re.sub(r"\s+", " ", texto.lower())


# ------------------------------------------------- copilot-instructions.md

class TestCopilotInstructions:
    arquivo = GITHUB / "copilot-instructions.md"

    def test_existe_e_tamanho_ate_50kb(self):
        assert self.arquivo.is_file()
        assert len(self.arquivo.read_bytes()) <= TAMANHO_MAXIMO_BYTES

    @pytest.mark.parametrize(
        "secao",
        ["Stack", "Estrutura de pastas", "Convenções de código", "Comandos de build e teste"],
    )
    def test_possui_secao_obrigatoria(self, secao: str):
        titulos = re.findall(r"^##\s+(.+?)\s*$", _ler(self.arquivo), flags=re.M)
        assert secao in titulos

    def test_possui_regra_de_segredos(self):
        texto = _ler(self.arquivo)
        assert re.search(r"^##\s+Segredos\s*$", texto, flags=re.M)
        norm = _normalizar(texto)
        assert "variáveis de ambiente" in norm
        assert "key vault" in norm
        assert "proibido escrever valores de segredos" in norm

    def test_possui_regra_de_recusa_de_codigo_malicioso_e_coleta_indevida(self):
        texto = _ler(self.arquivo)
        assert re.search(r"^##\s+Recusa de código malicioso", texto, flags=re.M)
        norm = _normalizar(texto)
        assert "recuse gerar código malicioso" in norm
        assert "coleta indevida de dados" in norm
        assert "informe ao usuário o motivo da recusa" in norm


# ------------------------------------------------------ Instrucoes_Escopo

class TestInstrucoesEscopo:
    pasta = GITHUB / "instructions"

    def test_azure_functions_apply_to(self):
        fm = extrair_frontmatter(_ler(self.pasta / "azure-functions.instructions.md"))
        assert fm is not None
        assert fm["applyTo"] == "src/**/*.py"

    def test_workflows_apply_to(self):
        fm = extrair_frontmatter(_ler(self.pasta / "workflows.instructions.md"))
        assert fm is not None
        assert fm["applyTo"] == ".github/workflows/*.{yml,yaml}"


# ------------------------------------------------------------ Prompt_Files

class TestPromptFiles:
    pasta = GITHUB / "prompts"

    def _arquivos(self) -> list[Path]:
        return sorted(self.pasta.glob("*.prompt.md"))

    def test_exatamente_cinco_prompts_esperados(self):
        nomes = {a.name.removesuffix(".prompt.md") for a in self._arquivos()}
        assert len(self._arquivos()) == 5
        assert nomes == PROMPTS_ESPERADOS

    @pytest.mark.parametrize("nome", sorted(PROMPTS_ESPERADOS))
    def test_frontmatter_valido(self, nome: str):
        fm = extrair_frontmatter(_ler(self.pasta / f"{nome}.prompt.md"))
        assert fm is not None
        descricao = fm["description"]
        assert isinstance(descricao, str) and descricao.strip()
        assert len(descricao) <= 200
        assert fm["mode"] in MODOS_VALIDOS

    @pytest.mark.parametrize("nome", sorted(PROMPTS_ESPERADOS))
    def test_placeholder_e_instrucoes_de_seguranca(self, nome: str):
        texto = _ler(self.pasta / f"{nome}.prompt.md")
        norm = _normalizar(texto)
        # placeholder de segredo
        assert "<NOME_DO_SEGREDO>" in texto
        # pedir dados ausentes sem alterar arquivos
        assert "peça" in norm or "solicite" in norm or "pergunte" in norm
        assert "não gere nem altere nenhum arquivo" in norm or "não gere nem altere arquivos" in norm
        # não gravar nem repetir segredos
        assert "não grave esse valor em nenhum arquivo" in norm
        assert "não o reproduza na resposta" in norm


# --------------------------------------------------------------- Chat_Mode

class TestChatMode:
    arquivo = GITHUB / "chatmodes" / "azure-functions.chatmode.md"

    def test_escopo_azure_functions(self):
        texto = _ler(self.arquivo)
        norm = _normalizar(texto)
        assert re.search(r"^##\s+Escopo\s*$", texto, flags=re.M)
        assert "azure functions" in norm
        assert "fora desse escopo" in norm

    def test_tools_explicito_sem_curinga(self):
        fm = extrair_frontmatter(_ler(self.arquivo))
        assert fm is not None
        tools = fm["tools"]
        assert isinstance(tools, list) and tools
        assert all(t.strip() and "*" not in t for t in tools)

    def test_confirmacao_explicita_antes_de_acoes_no_azure(self):
        norm = _normalizar(_ler(self.arquivo))
        assert "confirmação explícita" in norm
        assert "não execute o comando até receber uma resposta afirmativa" in norm
        assert "mantenha todos os recursos inalterados" in norm

    def test_portugues_do_brasil(self):
        norm = _normalizar(_ler(self.arquivo))
        assert "português do brasil" in norm


# -------------------------------------------------- validar_customizacoes

def test_validador_sem_nao_conformidades_no_repositorio():
    problemas = validar_repositorio(RAIZ)
    assert problemas == [], "\n".join(str(p) for p in problemas)
