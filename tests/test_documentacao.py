"""Testes de exemplo da documentação (README, tutorial, solução de problemas e avisos).

Validates: Requirements 7.7, 9.5, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 11.6
"""

from __future__ import annotations

import re
from pathlib import Path

from validar_documentacao import validar

RAIZ = Path(__file__).resolve().parent.parent
README = RAIZ / "README.md"
TUTORIAL = RAIZ / "docs" / "tutorial.md"
PROBLEMAS = RAIZ / "docs" / "solucao-de-problemas.md"
ETICA = RAIZ / "ETICA.md"
SECURITY = RAIZ / "SECURITY.md"
LICENCA = RAIZ / "LICENSE"


def _ler(caminho: Path) -> str:
    return caminho.read_text(encoding="utf-8")


def _norm(texto: str) -> str:
    return re.sub(r"\s+", " ", texto.lower())


def _titulos(texto: str, nivel: int) -> list[str]:
    """Títulos Markdown do nível dado, ignorando blocos de código."""
    sem_codigo = re.sub(r"```.*?```", "", texto, flags=re.DOTALL)
    padrao = r"^" + "#" * nivel + r"\s+(.+?)\s*$"
    return re.findall(padrao, sem_codigo, flags=re.MULTILINE)


def _secao(texto: str, titulo_regex: str) -> str:
    """Conteúdo de uma seção '## ...' até a próxima '## ...'."""
    sem_codigo_marcado = texto
    m = re.search(
        r"^##\s+" + titulo_regex + r".*?$(.*?)(?=^##\s|\Z)",
        sem_codigo_marcado,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert m, f"seção não encontrada: {titulo_regex}"
    return m.group(1)


# ------------------------------------------------------------------ README


def test_readme_tem_as_quatro_secoes():
    titulos = [_norm(t) for t in _titulos(_ler(README), 2)]
    for esperado in (
        "visão geral",
        "pré-requisitos",
        "estrutura de pastas",
        "início rápido",
    ):
        assert any(esperado in t for t in titulos), esperado


def test_readme_tem_aviso_de_independencia():
    texto = _norm(_ler(README))
    assert "material de estudo independente" in texto
    assert "afiliação" in texto
    assert "patrocínio" in texto
    assert "endosso" in texto
    assert "organização educacional" in texto


def test_readme_liga_para_etica_em_um_clique():
    texto = _ler(README)
    destinos = re.findall(r"\[[^\]]+\]\(([^)\s]+)\)", texto)
    assert "ETICA.md" in destinos
    assert (RAIZ / "ETICA.md").is_file()


def test_readme_lista_os_seis_prerequisitos():
    secao = _norm(_secao(_ler(README), r"Pré-requisitos"))
    for item in (
        "conta azure",
        "github copilot",
        "visual studio code",
        "azure functions core tools",
        "azure cli",
        "git",
    ):
        assert item in secao, item


# ---------------------------------------------------------------- tutorial


def test_tutorial_tem_cinco_secoes_numeradas_na_ordem():
    titulos = _titulos(_ler(TUTORIAL), 2)
    numerados = [t for t in titulos if re.match(r"^\d+\.\s", t)]
    assert len(numerados) == 5, numerados
    esperados = [
        "configurar o ambiente",
        "usar o agente_copilot",
        "criar funções",
        "testar localmente",
        "fazer deploy",
    ]
    for i, (titulo, esperado) in enumerate(zip(numerados, esperados), start=1):
        assert titulo.startswith(f"{i}."), titulo
        assert esperado in _norm(titulo), (titulo, esperado)


def test_tutorial_tem_seis_prerequisitos_com_link_http():
    secao = _secao(_ler(TUTORIAL), r"Pré-requisitos")
    linhas = [
        l for l in secao.splitlines() if re.match(r"^\|\s*\d+\s*\|", l.strip())
    ]
    assert len(linhas) == 6, linhas
    for linha in linhas:
        assert re.search(r"\]\(https?://[^)\s]+\)", linha), linha
    texto = _norm(secao)
    for item in (
        "conta azure",
        "assinatura do github copilot",
        "visual studio code",
        "azure functions core tools",
        "azure cli",
        "git",
    ):
        assert item in texto, item


def _blocos_mermaid(texto: str) -> list[str]:
    return re.findall(r"```mermaid\s*\n(.*?)```", texto, flags=re.DOTALL)


def test_tutorial_tem_diagrama_mermaid_com_componentes():
    blocos = _blocos_mermaid(_ler(TUTORIAL))
    assert blocos, "bloco ```mermaid ausente"
    bloco = blocos[0]
    for termo in ("VS Code", "Agente_Copilot", "Azure Functions", "Azure"):
        assert termo in bloco, termo


def test_tutorial_mermaid_sintaxe_heuristica():
    bloco = _blocos_mermaid(_ler(TUTORIAL))[0]
    linhas = [l for l in bloco.splitlines() if l.strip()]
    assert re.match(r"^(flowchart|graph)\s+(LR|RL|TB|TD|BT)\s*$", linhas[0].strip())
    corpo = "\n".join(linhas[1:])
    # Colchetes, chaves, parênteses e aspas balanceados.
    for abre, fecha in (("[", "]"), ("{", "}"), ("(", ")")):
        assert corpo.count(abre) == corpo.count(fecha), (abre, fecha)
    assert corpo.count('"') % 2 == 0
    # Há ao menos uma aresta e toda aresta tem origem e destino.
    arestas = [l for l in linhas[1:] if "-->" in l]
    assert arestas
    for linha in arestas:
        esquerda, _, direita = linha.partition("-->")
        assert esquerda.strip(), linha
        assert re.sub(r"^\|[^|]*\|", "", direita.strip()), linha


# ------------------------------------------------- solução de problemas


def _problemas(texto: str) -> list[tuple[str, str]]:
    """Pares (título, corpo) das seções '## N. ...'."""
    partes = re.split(r"^##\s+(?=\d+\.\s)", texto, flags=re.MULTILINE)[1:]
    resultado = []
    for parte in partes:
        titulo, _, corpo = parte.partition("\n")
        corpo = re.split(r"^##\s", corpo, flags=re.MULTILINE)[0]
        resultado.append((titulo.strip(), corpo))
    return resultado


def test_solucao_de_problemas_tem_ao_menos_cinco_com_sintoma_e_solucao():
    problemas = _problemas(_ler(PROBLEMAS))
    assert len(problemas) >= 5, len(problemas)
    for titulo, corpo in problemas:
        assert re.search(r"\*\*Sintoma\*\*", corpo), titulo
        assert re.search(r"\*\*Solução\*\*", corpo), titulo
        solucao = corpo.split("**Solução**", 1)[1]
        assert solucao.strip(), titulo


def test_custo_em_usd_e_comando_de_remocao():
    texto = _ler(PROBLEMAS)
    assert "USD" in texto
    assert re.search(r"custo mensal estimado", texto, flags=re.IGNORECASE)
    assert re.search(r"USD\s*\d|\d[\d,.]*\s*USD|\(USD\)", texto)
    assert re.search(r"^az group delete --name \S+", texto, flags=re.MULTILINE)


# ---------------------------------------------------- validar_documentacao


def test_validar_documentacao_sem_pendencias():
    assert validar(RAIZ) == []


# ---------------------------------------------------------------- LICENSE


def test_license_tem_texto_ano_e_titular():
    texto = _ler(LICENCA)
    assert re.search(r"^(MIT License|Apache License|BSD)", texto, flags=re.MULTILINE)
    assert "Permission is hereby granted" in texto
    m = re.search(r"^Copyright \(c\) (\d{4}) (\S.*)$", texto, flags=re.MULTILINE)
    assert m, "linha de copyright com ano e titular ausente"
    assert 2000 <= int(m.group(1)) <= 2100
    assert m.group(2).strip()


# ----------------------------------------------------- ETICA e SECURITY


def test_etica_tem_as_quatro_secoes_e_exemplos():
    texto = _ler(ETICA)
    titulos = [_norm(t) for t in _titulos(texto, 2)]
    assert len(titulos) >= 4
    for esperado in (
        "revisão humana",
        "o que não enviar",
        "erros, vulnerabilidades e licenciamento",
        "assinaturas azure autorizadas",
    ):
        assert any(esperado in t for t in titulos), esperado
    norm = _norm(texto)
    for termo in ("segredo", "dados pessoais", "código proprietário"):
        assert termo in norm, termo
    assert "exemplo" in norm


def test_security_menciona_prazo_de_cinco_dias_uteis():
    texto = _norm(_ler(SECURITY))
    assert re.search(r"\b5 dias úteis", texto)
