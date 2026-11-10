from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.firebase import get_firestore_client
from app.model.client import ClientCreateRequest, ClientFirestoreModel, ClientUpdateRequest
from app.repository.client_repository import ClientRepository
from app.service.client_service import ClientService


def get_client_service() -> ClientService:
    return ClientService(ClientRepository(get_firestore_client()))


router = APIRouter(prefix="/api/v1", tags=["Clients"])


@router.get("/clients", response_model=list[ClientFirestoreModel])
def list_clients(
    status: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    dueBefore: Optional[str] = Query(default=None, alias="dueBefore"),
    dueAfter: Optional[str] = Query(default=None, alias="dueAfter"),
    sort: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    service: ClientService = Depends(get_client_service),
):
    return service.list_clients(
        status=status,
        q=q,
        due_before=dueBefore,
        due_after=dueAfter,
        sort=sort,
        page=page,
        limit=limit,
    )


@router.post("/clients", response_model=ClientFirestoreModel, status_code=status.HTTP_201_CREATED)
def create_client(
    payload: ClientCreateRequest,
    service: ClientService = Depends(get_client_service),
):
    return service.create_client(payload)


@router.get("/clients/{client_id}", response_model=ClientFirestoreModel)
def get_client(
    client_id: str,
    service: ClientService = Depends(get_client_service),
):
    client = service.get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client


@router.patch("/clients/{client_id}", response_model=ClientFirestoreModel)
def update_client(
    client_id: str,
    payload: ClientUpdateRequest,
    service: ClientService = Depends(get_client_service),
):
    client = service.update_client(client_id, payload)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client


@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: str,
    service: ClientService = Depends(get_client_service),
):
    deleted = service.delete_client(client_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/clients/{client_id}/complete", response_model=dict)
def complete_client(
    client_id: str,
    service: ClientService = Depends(get_client_service),
):
    try:
        result = service.complete_client(client_id)
        return result
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/clients/{client_id}/reopen", response_model=ClientFirestoreModel)
def reopen_client(
    client_id: str,
    service: ClientService = Depends(get_client_service),
):
    try:
        client = service.reopen_client(client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        return client
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/dashboard/summary")
def dashboard_summary(service: ClientService = Depends(get_client_service)):
    return service.dashboard_summary()


@router.get("/dashboard/deadline-alerts")
def deadline_alerts(
    days: int = Query(default=3, ge=0),
    service: ClientService = Depends(get_client_service),
):
    return {"days": days, "items": service.deadline_alerts(days)}


@router.get("/team")
def team_totals(service: ClientService = Depends(get_client_service)):
    return service.team_totals()