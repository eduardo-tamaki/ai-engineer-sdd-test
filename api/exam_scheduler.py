"""
Mock da API de agendamento de exames.

Você pode modificar este arquivo livremente — documente as mudanças no CHANGES.md.

Para subir:
    uv run uvicorn api.exam_scheduler:app --reload --port 8080

Docs interativos em http://127.0.0.1:8080/docs.

---

Gatilhos determinísticos para testar cenários de erro (não são "easter eggs":
estão documentados para que você consiga exercitar todos os caminhos da spec):

- GET /availability?date=2099-01-01            -> 500 (falha de sistema)
- GET /availability?date=2099-01-02            -> 200 com lista vazia
- POST /appointments com date=2099-12-31       -> 409 (conflito)
- POST /appointments para slot já reservado    -> 409 (conflito)

Para o restante das datas, a disponibilidade é gerada deterministicamente a partir
do par (exam_id, date), sem aleatoriedade. Fins de semana retornam lista vazia
(clínica fechada).
"""

from __future__ import annotations

import hashlib
from datetime import date as date_cls, datetime, time, timedelta
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(
    title="Exam Scheduler API (mock)",
    description="API mockada para o teste de AI Engineer. Não usar em produção.",
    version="0.1.0",
)


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------


class Patient(BaseModel):
    id: str
    name: str


class Service(BaseModel):
    id: str
    name: str
    duration_minutes: int
    preparation: str = Field(
        description="Instruções de preparo que o agente DEVE comunicar antes da confirmação."
    )


class Slot(BaseModel):
    date: str = Field(description="YYYY-MM-DD")
    time: str = Field(description="HH:MM")


class AppointmentRequest(BaseModel):
    patient_id: str
    exam_id: str
    date: str = Field(description="YYYY-MM-DD")
    time: str = Field(description="HH:MM")


class Appointment(BaseModel):
    id: str
    patient_id: str
    exam_id: str
    date: str
    time: str
    status: Literal["confirmed"] = "confirmed"


# ---------------------------------------------------------------------------
# Dados em memória
# ---------------------------------------------------------------------------


PATIENTS: dict[str, Patient] = {
    "P001": Patient(id="P001", name="Ana Silva"),
    "P002": Patient(id="P002", name="Bruno Costa"),
    "P003": Patient(id="P003", name="Carla Oliveira"),
    "P042": Patient(id="P042", name="Daniel Souza"),
}


SERVICES: list[Service] = [
    Service(
        id="ressonancia_magnetica",
        name="Ressonância Magnética",
        duration_minutes=45,
        preparation=(
            "Jejum de 4 horas antes do exame. "
            "Remova objetos metálicos (joias, piercings, próteses dentárias removíveis). "
            "Avise se tiver marcapasso, implante coclear ou claustrofobia."
        ),
    ),
    Service(
        id="raio_x",
        name="Raio-X",
        duration_minutes=15,
        preparation=(
            "Nenhum preparo especial necessário. "
            "Evite usar roupas com botões metálicos ou estampas na região a ser examinada."
        ),
    ),
    Service(
        id="exame_sangue",
        name="Exame de Sangue",
        duration_minutes=10,
        preparation=(
            "Jejum de 8 a 12 horas (apenas água é permitida). "
            "Evite atividade física intensa nas 24 horas anteriores."
        ),
    ),
    Service(
        id="ultrassom_abdominal",
        name="Ultrassom Abdominal",
        duration_minutes=30,
        preparation=(
            "Jejum de 6 horas. "
            "Beba 1 litro de água até 1 hora antes do exame e não urine até a realização."
        ),
    ),
    Service(
        id="tomografia",
        name="Tomografia Computadorizada",
        duration_minutes=30,
        preparation=(
            "Jejum de 4 horas se o exame for com contraste. "
            "Informe alergias a contraste iodado ou problemas renais."
        ),
    ),
]

SERVICES_BY_ID: dict[str, Service] = {s.id: s for s in SERVICES}


# Bookings em memória — slot -> appointment.
# Chave: (exam_id, date, time)
_BOOKINGS: dict[tuple[str, str, str], Appointment] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_date(value: str) -> date_cls:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Formato de data inválido: '{value}'. Use YYYY-MM-DD.",
        ) from e


def _parse_time(value: str) -> time:
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Formato de hora inválido: '{value}'. Use HH:MM.",
        ) from e


def _deterministic_slots(exam_id: str, target: date_cls) -> list[Slot]:
    """Gera 0-4 slots determinísticos para (exam_id, date)."""
    # Fim de semana: clínica fechada.
    if target.weekday() >= 5:
        return []

    seed = hashlib.md5(f"{exam_id}|{target.isoformat()}".encode()).digest()
    candidate_times = ["08:00", "09:30", "11:00", "13:30", "15:00", "16:30"]

    # Bit-mask determinístico: cada bit decide se o slot está disponível.
    mask = seed[0]
    slots: list[Slot] = []
    for i, t in enumerate(candidate_times):
        if mask & (1 << i):
            slots.append(Slot(date=target.isoformat(), time=t))

    # Remove slots já reservados.
    return [s for s in slots if (exam_id, s.date, s.time) not in _BOOKINGS]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/patients/{patient_id}", response_model=Patient)
def get_patient(patient_id: str) -> Patient:
    """
    Retorna 200 + paciente se existir, 404 caso contrário.

    Observação: este endpoint NÃO valida o formato do ID. A validação por regex
    (deve começar com 'P' seguido de alfanuméricos) é responsabilidade do agente,
    antes de chamar a API. Veja a spec do desafio.
    """
    patient = PATIENTS.get(patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")
    return patient


@app.get("/service-catalog", response_model=list[Service])
def get_service_catalog() -> list[Service]:
    """Lista exames disponíveis e suas instruções de preparo."""
    return SERVICES


@app.get("/availability", response_model=list[Slot])
def get_availability(
    exam: str = Query(..., description="ID do exame (ver /service-catalog)."),
    date: str = Query(..., description="Data desejada no formato YYYY-MM-DD."),
) -> list[Slot]:
    """
    Retorna slots disponíveis para um exame em uma data.

    Erros possíveis (intencionais — veja docstring do módulo):
    - 400: data ou exame mal-formados.
    - 404: exame inexistente.
    - 500: data 2099-01-01 (gatilho determinístico de falha).
    - 200 vazio: data 2099-01-02, fins de semana, ou nenhum slot livre.
    """
    target = _parse_date(date)

    if exam not in SERVICES_BY_ID:
        raise HTTPException(status_code=404, detail=f"Exame '{exam}' não encontrado.")

    # Gatilhos determinísticos para a Fase 3.
    if target == date_cls(2099, 1, 1):
        raise HTTPException(status_code=500, detail="Erro interno simulado.")
    if target == date_cls(2099, 1, 2):
        return []

    return _deterministic_slots(exam, target)


@app.post("/appointments", response_model=Appointment, status_code=201)
def create_appointment(payload: AppointmentRequest) -> Appointment:
    """
    Cria um agendamento.

    Erros possíveis:
    - 400: data/hora mal-formadas.
    - 404: paciente ou exame inexistente.
    - 409: slot já reservado (ou date=2099-12-31, gatilho determinístico).
    """
    if payload.patient_id not in PATIENTS:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")
    if payload.exam_id not in SERVICES_BY_ID:
        raise HTTPException(status_code=404, detail="Exame não encontrado.")

    target_date = _parse_date(payload.date)
    _parse_time(payload.time)  # valida formato

    # Gatilho determinístico de conflito.
    if target_date == date_cls(2099, 12, 31):
        raise HTTPException(
            status_code=409,
            detail="Slot indisponível: já foi reservado por outro paciente.",
        )

    key = (payload.exam_id, payload.date, payload.time)
    if key in _BOOKINGS:
        raise HTTPException(
            status_code=409,
            detail="Slot indisponível: já foi reservado por outro paciente.",
        )

    appointment_id = f"A{len(_BOOKINGS) + 1:05d}"
    appointment = Appointment(
        id=appointment_id,
        patient_id=payload.patient_id,
        exam_id=payload.exam_id,
        date=payload.date,
        time=payload.time,
    )
    _BOOKINGS[key] = appointment
    return appointment


@app.delete("/_test/reset", include_in_schema=False)
def _reset_state() -> dict[str, str]:
    """Limpa o estado de bookings — útil para rodar testes locais. Não é parte da API pública."""
    _BOOKINGS.clear()
    return {"status": "ok"}
