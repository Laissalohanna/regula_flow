class DomainError(Exception):
    pass


class InvalidStatusTransitionError(DomainError):
    def __init__(self, current: str, target: str) -> None:
        self.current = current
        self.target = target
        super().__init__(f"Transição inválida de {current} para {target}.")
