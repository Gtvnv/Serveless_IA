"""Logging seguro: redação de Segredos e dados pessoais e log estruturado de erros."""

from __future__ import annotations

import re
from typing import Iterable

MARCADOR_SEGREDO = "[SEGREDO]"
MARCADOR_PII = "[DADO_PESSOAL]"
TAMANHO_MIN_VALOR_SENSIVEL = 4

# Chaves de campos que carregam Segredos ou dados pessoais. O valor após a chave é removido.
_CHAVES_SEGREDO = (
    r"account[_-]?key|shared[_-]?access[_-]?key|sharedaccesssignature|access[_-]?key|"
    r"api[_-]?key|apikey|client[_-]?secret|secret|password|passwd|pwd|senha|"
    r"chave|token|authorization|connection[_-]?string|connectionstring|sig"
)
_CHAVES_PII = (
    r"nome(?:_[a-z]+)?|name|e-?mail|cpf|telefone|celular|phone|"
    r"endere[cç]o|endereco|address|logradouro"
)

_RE_BLOCO_CHAVE_PRIVADA = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(?:-----END [A-Z ]*PRIVATE KEY-----|$)", re.DOTALL
)
# Connection strings: sequência de pares chave=valor separados por ';' contendo chaves conhecidas.
_RE_CONNECTION_STRING = re.compile(
    r"(?:DefaultEndpointsProtocol|Endpoint|Server|Data Source|AccountName|AccountKey|"
    r"SharedAccessKeyName|SharedAccessKey|InstrumentationKey|Password|Pwd|User Id|Uid)"
    r"\s*=\s*[^;\r\n]*(?:;\s*[A-Za-z ]+\s*=\s*[^;\r\n]*)*;?",
    re.IGNORECASE,
)
_RE_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}(?:\.[A-Za-z0-9_-]*)?")
_RE_BEARER = re.compile(r"\b(Bearer|Basic)\s+[A-Za-z0-9._~+/=-]{8,}", re.IGNORECASE)
_RE_PREFIXOS_TOKEN = re.compile(
    r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{16,}|"
    r"AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,})"
)
# chave: valor / chave=valor / "chave": "valor"
_RE_PAR_SEGREDO = re.compile(
    r"(?P<k>[\"']?\b(?:" + _CHAVES_SEGREDO + r")[\"']?\s*[:=]\s*)(?P<v>\"[^\"]*\"|'[^']*'|[^\s,;&}\]]+)",
    re.IGNORECASE,
)
_RE_PAR_PII = re.compile(
    r"(?P<k>[\"']?\b(?:" + _CHAVES_PII + r")[\"']?\s*[:=]\s*)(?P<v>\"[^\"]*\"|'[^']*'|[^\s,;&}\]]+(?:[ \t]+[^\s,;&}\]:=]+){0,5}(?![^\s,;&}\]]*[:=]))",
    re.IGNORECASE,
)
_RE_EMAIL = re.compile(r"[A-Za-z0-9._%+'-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_RE_CPF = re.compile(r"(?<!\d)\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?!\d)")
_RE_TELEFONE = re.compile(
    r"(?<![\w])(?:\+?55[\s.-]?)?(?:\(?\d{2}\)?[\s.-]?)?(?:9[\s.-]?)?\d{4}[\s.-]?\d{4}(?!\w)"
)
_RE_ENDERECO = re.compile(
    r"\b(?:Rua|Avenida|Av\.|Alameda|Travessa|Rodovia|Estrada|Pra[cç]a)\s+[^,;\n]+(?:,\s*\d+[^,;\n]*)?",
    re.IGNORECASE,
)
_RE_CEP = re.compile(r"(?<!\d)\d{5}-\d{3}(?!\d)")


def _subst_par(marcador: str):
    def _f(m: re.Match) -> str:
        return f"{m.group('k')}{marcador}"

    return _f


def redigir(texto: str, valores_sensiveis: Iterable[str] = ()) -> str:
    """Remove Segredos e dados pessoais de ``texto``.

    ``valores_sensiveis`` permite informar valores exatos (por exemplo, campos do
    pedido) que também devem ser removidos. Nunca lança exceção.
    """
    if texto is None:
        return ""
    if not isinstance(texto, str):
        try:
            texto = str(texto)
        except Exception:  # noqa: BLE001 - objeto com __str__ defeituoso
            return MARCADOR_SEGREDO

    # E-mails antes dos valores exatos: evita deixar o domínio quando um nome coincide com o usuário.
    texto = _RE_EMAIL.sub(MARCADOR_PII, texto)

    # Valores exatos (mais longos antes, para evitar remoção parcial). Valores muito curtos
    # são ignorados: removê-los corromperia o restante do texto.
    for valor in sorted(
        {v for v in valores_sensiveis if isinstance(v, str) and len(v) >= TAMANHO_MIN_VALOR_SENSIVEL},
        key=len,
        reverse=True,
    ):
        texto = texto.replace(valor, MARCADOR_PII)

    # Segredos.
    texto = _RE_BLOCO_CHAVE_PRIVADA.sub(MARCADOR_SEGREDO, texto)
    texto = _RE_CONNECTION_STRING.sub(MARCADOR_SEGREDO, texto)
    texto = _RE_JWT.sub(MARCADOR_SEGREDO, texto)
    texto = _RE_BEARER.sub(lambda m: f"{m.group(1)} {MARCADOR_SEGREDO}", texto)
    texto = _RE_PREFIXOS_TOKEN.sub(MARCADOR_SEGREDO, texto)
    texto = _RE_PAR_SEGREDO.sub(_subst_par(MARCADOR_SEGREDO), texto)

    # Dados pessoais.
    texto = _RE_PAR_PII.sub(_subst_par(MARCADOR_PII), texto)
    texto = _RE_EMAIL.sub(MARCADOR_PII, texto)
    texto = _RE_CPF.sub(MARCADOR_PII, texto)
    texto = _RE_ENDERECO.sub(MARCADOR_PII, texto)
    texto = _RE_CEP.sub(MARCADOR_PII, texto)
    texto = _RE_TELEFONE.sub(MARCADOR_PII, texto)
    return texto


def registrar_erro(
    logger,
    funcao: str,
    invocacao: str,
    excecao: BaseException,
    valores_sensiveis: Iterable[str] = (),
) -> dict:
    """Registra um erro estruturado com ``funcao``, ``invocacao``, ``tipo_excecao`` e ``mensagem``.

    Todos os campos passam por ``redigir``. A pilha não é registrada. Retorna o
    registro emitido.
    """
    valores = tuple(valores_sensiveis)
    # Valores exatos e padrões de dados pessoais só se aplicam à mensagem. Campos técnicos
    # (funcao, invocacao, tipo_excecao) não carregam dados do pedido e não podem ser corrompidos
    # (ex.: um id de invocação numérico confundido com telefone).
    registro = {
        "funcao": funcao,
        "invocacao": invocacao,
        "tipo_excecao": type(excecao).__name__,
        "mensagem": redigir(str(excecao), valores),
    }
    try:
        logger.error(
            "funcao=%s invocacao=%s tipo_excecao=%s mensagem=%s",
            registro["funcao"],
            registro["invocacao"],
            registro["tipo_excecao"],
            registro["mensagem"],
        )
    except Exception:  # noqa: BLE001 - falha de log não pode mascarar o erro original
        pass
    return registro
