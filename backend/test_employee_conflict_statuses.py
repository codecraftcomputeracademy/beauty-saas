import asyncio
from datetime import datetime
from uuid import UUID

import app.model_registry  # noqa: F401

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.modules.scheduling.models.appointment import (
    Appointment,
    AppointmentStatus,
)
from app.modules.scheduling.services.employee_conflict_service import (
    EmployeeConflictService,
)


ORG_ID = UUID("5d3602f7-042b-4422-a030-5360569b68e5")
BRANCH_ID = UUID("9a8d84b8-56fa-434d-8546-73ea75b35a42")
EMPLOYEE_ID = UUID("452afac3-6df2-4dba-ab1a-e2927f8b37a6")
APPOINTMENT_ID = UUID(
    "53aac011-58e9-4240-8b07-f3f9ad4a79f0"
)


async def run_test(service, name, expected):
    actual = await service.has_conflict(
        organization_id=ORG_ID,
        employee_id=EMPLOYEE_ID,
        branch_id=BRANCH_ID,
        requested_start=datetime.fromisoformat(
            "2026-09-24T10:00:00+05:30"
        ),
        requested_end=datetime.fromisoformat(
            "2026-09-24T11:00:00+05:30"
        ),
    )

    result = "PASS" if actual == expected else "FAIL"

    print(
        f"{result} | {name} | "
        f"Expected={expected}, Actual={actual}"
    )


async def main():
    async with AsyncSessionLocal() as session:

        appointment = await session.get(
            Appointment,
            APPOINTMENT_ID,
        )

        if appointment is None:
            print("Appointment not found.")
            return

        service = EmployeeConflictService(session)

        non_blocking_statuses = [
            (
                AppointmentStatus.DRAFT,
                "DRAFT",
            ),
            (
                AppointmentStatus.COMPLETED,
                "COMPLETED",
            ),
            (
                AppointmentStatus.CANCELLED,
                "CANCELLED",
            ),
            (
                AppointmentStatus.NO_SHOW,
                "NO_SHOW",
            ),
        ]

        for status, name in non_blocking_statuses:
            appointment.status = status
            await session.flush()

            await run_test(
                service,
                f"{name} appointment",
                False,
            )

        # Restore the original test appointment state.
        appointment.status = AppointmentStatus.BOOKED
        await session.commit()

        print("Appointment status restored to BOOKED.")


if __name__ == "__main__":
    asyncio.run(main())