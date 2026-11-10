from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from google.cloud.firestore import Client

from app.model.client import ClientCreateRequest, ClientFirestoreModel, ClientUpdateRequest


class ClientRepository:
    """Firestore repository for client/project CRUD and state transitions."""

    def __init__(self, firestore_client: Client):
        self.db = firestore_client
        self.collection = self.db.collection("clients")

    def _serialize(self, doc_id: str, data: dict[str, Any]) -> dict[str, Any]:
        payload = dict(data or {})
        payload["id"] = doc_id

        for field_name in ("createdAt", "updatedAt", "completedAt"):
            value = payload.get(field_name)
            if isinstance(value, datetime):
                payload[field_name] = value.isoformat()
            elif value is None:
                payload[field_name] = None

        return payload

    def create(self, client: ClientCreateRequest) -> ClientFirestoreModel:
        now = datetime.now(timezone.utc)
        payload = client.model_dump(exclude_none=True, exclude={"id"})
        payload["createdAt"] = now
        payload["updatedAt"] = now
        payload["completedAt"] = None

        doc_ref = self.collection.document()
        doc_ref.set(payload)

        saved = doc_ref.get().to_dict() or {}
        return ClientFirestoreModel.from_firestore(doc_ref.id, saved)

    def get_by_id(self, client_id: str) -> Optional[ClientFirestoreModel]:
        snapshot = self.collection.document(client_id).get()
        if not snapshot.exists:
            return None
        return ClientFirestoreModel.from_firestore(snapshot.id, snapshot.to_dict() or {})

    def _get_all_documents(self) -> list[ClientFirestoreModel]:
        docs = list(self.collection.stream())
        return [ClientFirestoreModel.from_firestore(doc.id, doc.to_dict() or {}) for doc in docs]

    def summary(self) -> dict[str, int]:
        clients = self._get_all_documents()
        return {
            "activeProjects": sum(1 for client in clients if client.status != "Completed"),
            "totalClients": len(clients),
            "totalProjectValue": sum(client.cost for client in clients),
            "completedCount": sum(1 for client in clients if client.status == "Completed"),
        }

    def deadline_alerts(self, days: int) -> list[dict[str, Any]]:
        clients = self._get_all_documents()
        target_date = datetime.now(timezone.utc).date()
        alerts: list[dict[str, Any]] = []

        for client in clients:
            if client.status == "Completed":
                continue

            try:
                due_date = datetime.strptime(client.due, "%Y-%m-%d").date()
            except ValueError:
                continue

            if due_date <= (target_date + __import__('datetime').timedelta(days=days)):
                alerts.append(
                    {
                        "id": client.id,
                        "name": client.name,
                        "status": client.status,
                        "due": client.due,
                        "daysLeft": (due_date - target_date).days,
                    }
                )

        alerts.sort(key=lambda item: item["due"])
        return alerts

    def team_totals(self) -> dict[str, list[dict[str, Any]]]:
        clients = self._get_all_documents()
        members = ["Sumit", "Shree", "Abhishek"]
        payload: list[dict[str, Any]] = []

        for member in members:
            worked = [client for client in clients if member in client.people]
            completed = [client for client in worked if client.status == "Completed"]
            amount_earned = 0
            amount_pending = 0

            for client in worked:
                percentage = self._member_share(client.people, member)
                amount = int((client.cost * percentage) / 100)
                if client.status == "Completed":
                    amount_earned += amount
                else:
                    amount_pending += amount

            payload.append(
                {
                    "name": member,
                    "projectsWorked": len(worked),
                    "projectsCompleted": len(completed),
                    "amountEarned": amount_earned,
                    "amountPending": amount_pending,
                }
            )

        return {"members": payload}

    def _member_share(self, people: list[str], member: str) -> int:
        if len(people) == 2:
            shares = {"Sumit": 80, "Shree": 20}
        else:
            shares = {"Sumit": 70, "Shree": 15, "Abhishek": 15}
        return shares.get(member, 0)

    def list(
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
        query = self.collection

        if status:
            query = query.where("status", "==", status)
        if due_before:
            query = query.where("due", "<=", due_before)
        if due_after:
            query = query.where("due", ">=", due_after)

        docs = list(query.stream())
        results: list[ClientFirestoreModel] = []

        for doc in docs:
            data = doc.to_dict() or {}
            if q:
                search_text = " ".join(
                    [
                        str(data.get("name", "")),
                        str(data.get("category", "")),
                        str(data.get("description", "")),
                        " ".join(str(person) for person in data.get("people", [])),
                    ]
                ).lower()
                if q.lower() not in search_text:
                    continue

            results.append(ClientFirestoreModel.from_firestore(doc.id, data))

        if sort == "due_asc":
            results.sort(key=lambda item: item.due or "")
        elif sort == "due_desc":
            results.sort(key=lambda item: item.due or "", reverse=True)

        start = (page - 1) * limit
        end = start + limit
        return results[start:end]

    def update(self, client_id: str, client: ClientUpdateRequest) -> Optional[ClientFirestoreModel]:
        doc_ref = self.collection.document(client_id)
        current = doc_ref.get()
        if not current.exists:
            return None

        payload = client.model_dump(exclude_none=True)
        if "people" in payload and payload["people"] is not None:
            payload["people"] = [person.strip() for person in payload["people"] if person and person.strip()]

        payload["updatedAt"] = datetime.now(timezone.utc)
        doc_ref.update(payload)

        updated = doc_ref.get().to_dict() or {}
        return ClientFirestoreModel.from_firestore(doc_ref.id, updated)

    def delete(self, client_id: str) -> bool:
        doc_ref = self.collection.document(client_id)
        if not doc_ref.get().exists:
            return False
        doc_ref.delete()
        return True

    def complete(self, client_id: str) -> dict[str, Any]:
        doc_ref = self.collection.document(client_id)
        snapshot = doc_ref.get()
        if not snapshot.exists:
            raise KeyError("Client not found")

        data = snapshot.to_dict() or {}
        if data.get("status") == "Completed":
            raise ValueError("Client is already completed")

        people = data.get("people", [])
        cost = int(data.get("cost", 0) or 0)

        if len(people) == 2:
            split = {"Sumit": 80, "Shree": 20}
        elif len(people) == 3:
            split = {"Sumit": 70, "Shree": 15, "Abhishek": 15}
        else:
            raise ValueError("people must contain 2 or 3 valid members")

        payouts: list[dict[str, Any]] = []
        for member, percent in split.items():
            if member in people:
                amount = int((cost * percent) / 100)
                payouts.append({"member": member, "percent": percent, "amount": amount})

        completed_at = datetime.now(timezone.utc)
        doc_ref.update(
            {
                "status": "Completed",
                "completedAt": completed_at,
                "updatedAt": completed_at,
            }
        )

        return {
            "id": doc_ref.id,
            "status": "Completed",
            "completedAt": completed_at.isoformat(),
            "payouts": payouts,
        }

    def reopen(self, client_id: str) -> Optional[ClientFirestoreModel]:
        doc_ref = self.collection.document(client_id)
        snapshot = doc_ref.get()
        if not snapshot.exists:
            return None

        data = snapshot.to_dict() or {}
        if data.get("status") != "Completed":
            raise ValueError("Only completed clients can be reopened")

        now = datetime.now(timezone.utc)
        doc_ref.update({"status": "Open", "completedAt": None, "updatedAt": now})
        updated = doc_ref.get().to_dict() or {}
        return ClientFirestoreModel.from_firestore(doc_ref.id, updated)
