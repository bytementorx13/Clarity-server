from __future__ import annotations

from typing import Optional

from app.model.client import ClientCreateRequest, ClientFirestoreModel, ClientUpdateRequest
from app.repository.client_repository import ClientRepository


class ClientService:
    def __init__(self, repository: ClientRepository):
        self.repository = repository

    def create_client(self, payload: ClientCreateRequest) -> ClientFirestoreModel:
        return self.repository.create(payload)

    def get_client_by_id(self, client_id: str) -> Optional[ClientFirestoreModel]:
        return self.repository.get_by_id(client_id)

    def list_clients(
        self,
        *,
        status: Optional[str] = None,
        q: Optional[str] = None,
        due_before: Optional[str] = None,
        due_after: Optional[str] = None,
        sort: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> list[ClientFirestoreModel]:
        return self.repository.list(
            status=status,
            q=q,
            due_before=due_before,
            due_after=due_after,
            sort=sort,
            page=page,
            limit=limit,
        )

    def update_client(self, client_id: str, payload: ClientUpdateRequest) -> Optional[ClientFirestoreModel]:
        return self.repository.update(client_id, payload)

    def delete_client(self, client_id: str) -> bool:
        return self.repository.delete(client_id)

    def complete_client(self, client_id: str) -> dict:
        return self.repository.complete(client_id)

    def reopen_client(self, client_id: str) -> Optional[ClientFirestoreModel]:
        return self.repository.reopen(client_id)

    def dashboard_summary(self) -> dict[str, int]:
        return self.repository.summary()

    def deadline_alerts(self, days: int) -> list[dict]:
        return self.repository.deadline_alerts(days)

    def team_totals(self) -> dict[str, list[dict[str, Any]]]:
        return self.repository.team_totals()
