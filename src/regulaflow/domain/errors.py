class DomainError(Exception):
    """Quebra de regra de negócio. Não representa falha técnica."""


class InvalidStatusTransitionError(DomainError):
    """Tentativa de mover um processamento para um status incompatível."""

    def __init__(self, current: str, target: str) -> None:
        self.current = current
        self.target = target
        super().__init__(f"Transição inválida de {current} para {target}.")
