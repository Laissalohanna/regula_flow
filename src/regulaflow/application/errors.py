from uuid import UUID


class ProcessingFailureError(Exception):
    def __init__(self, batch_id: UUID) -> None:
        self.batch_id = batch_id
        super().__init__("Falha no processamento.")
