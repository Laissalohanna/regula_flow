class DomainError(Exception):
    pass


class DuplicateBatchError(DomainError):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        super().__init__(f"Lote {identifier} já foi recebido.")


class BatchNotFoundError(DomainError):
    def __init__(self, batch_id: str) -> None:
        self.batch_id = batch_id
        super().__init__(f"Lote {batch_id} não encontrado.")


class NotReprocessableError(DomainError):
    def __init__(self, status: str) -> None:
        self.status = status
        super().__init__(f"Lote com status {status} não pode ser reprocessado.")


class InvalidStatusTransitionError(DomainError):
    def __init__(self, current: str, target: str) -> None:
        self.current = current
        self.target = target
        super().__init__(f"Transição inválida de {current} para {target}.")
