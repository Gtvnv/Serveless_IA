"""Acesso a Segredos via Azure Key Vault.

Não existe valor padrão: se o Segredo não puder ser lido, a exceção do
cliente é propagada e a operação deve ser recusada pelo chamador.
"""

import logging

_logger = logging.getLogger(__name__)


def obter_segredo(nome: str, cliente) -> str:
    """Lê o valor do Segredo `nome` usando `cliente` (ex.: SecretClient).

    Em qualquer falha do cliente, registra um erro sem o valor do Segredo
    (apenas o nome e o tipo da exceção) e relança a exceção original.
    """
    try:
        return cliente.get_secret(nome).value
    except Exception as exc:
        _logger.error(
            "Falha ao obter segredo do Key Vault: nome=%s tipo_excecao=%s",
            nome,
            type(exc).__name__,
        )
        raise
