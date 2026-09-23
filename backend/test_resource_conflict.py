import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID

import app.model_registry  # noqa: F401

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.modules.scheduling.models.appointment import (
    Appointment,
    AppointmentStatus,
)
from app.modules.scheduling.models.appointment_service import (
    AppointmentService,
)
from app.modules.scheduling.models.appointment_service_resource import (
    AppointmentServiceResource,
)
from app.modules.scheduling.services.resource_conflict_service import (
    ResourceConflictService,
)


ORG_ID = UUID(
    "5d3602f7-042b-4422-a030-5360569b68e5"
)

BRANCH_ID = UUID(
    "9a8d84b8-56fa-434d-8546-73ea75b35a42"
)

APPOINTMENT_ID = UUID(
    "53aac011-58e9-4240-8b07-f3f9ad4a79f0"
)

RESOURCE_ID = UUID(
    "8b249905-312f-4629-97b3-ec8e8ea24ff7"
)

IST = timezone(timedelta(hours=5, minutes=30))


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=IST)


async def run_test(
    service: ResourceConflictService,
    name: str,
    start: datetime,
    end: datetime,
    expected: bool,
):
    actual = await service.has_conflict(
        organization_id=ORG_ID,
        resource_id=RESOURCE_ID,
        branch_id=BRANCH_ID,
        requested_start=start,
        requested_end=end,
    )

    result = "PASS" if actual == expected else "FAIL"

    print(
        f"{result} | {name} | "
        f"Expected={expected}, Actual={actual}"
    )


async def main():
    async with AsyncSessionLocal() as session:

        # ---------------------------------------------------------
        # 1. Find the existing appointment service dynamically
        # ---------------------------------------------------------

        result = await session.execute(
            select(AppointmentService).where(
                AppointmentService.appointment_id
                == APPOINTMENT_ID,
                AppointmentService.organization_id
                == ORG_ID,
                AppointmentService.branch_id
                == BRANCH_ID,
            )
        )

        appointment_service = result.scalar_one_or_none()

        if appointment_service is None:
            raise RuntimeError(
                "AppointmentService for the test appointment "
                "was not found."
            )

        appointment_service_id = appointment_service.id

        print(
            "Appointment Service found:"
        )
        print(
            f"  ID: {appointment_service_id}"
        )
        print(
            f"  Start: {appointment_service.scheduled_start}"
        )
        print(
            f"  End:   {appointment_service.scheduled_end}"
        )

        # ---------------------------------------------------------
        # 2. Find the appointment
        # ---------------------------------------------------------

        appointment = await session.get(
            Appointment,
            APPOINTMENT_ID,
        )

        if appointment is None:
            raise RuntimeError(
                "Test appointment was not found."
            )

        # ---------------------------------------------------------
        # 3. Ensure resource allocation exists
        # ---------------------------------------------------------

        result = await session.execute(
            select(AppointmentServiceResource).where(
                AppointmentServiceResource.organization_id
                == ORG_ID,
                AppointmentServiceResource.branch_id
                == BRANCH_ID,
                AppointmentServiceResource.appointment_service_id
                == appointment_service_id,
                AppointmentServiceResource.resource_id
                == RESOURCE_ID,
            )
        )

        allocation = result.scalar_one_or_none()

        if allocation is None:
            allocation = AppointmentServiceResource(
                organization_id=ORG_ID,
                branch_id=BRANCH_ID,
                appointment_service_id=appointment_service_id,
                resource_id=RESOURCE_ID,
            )

            session.add(allocation)

            await session.flush()

            print(
                f"Resource allocation created: {allocation.id}"
            )
        else:
            print(
                f"Resource allocation already exists: "
                f"{allocation.id}"
            )

        # ---------------------------------------------------------
        # 4. Create conflict service
        # ---------------------------------------------------------

        service = ResourceConflictService(session)

        print()
        print("RESOURCE CONFLICT TESTS")
        print("-----------------------")

        # Existing appointment:
        # 10:00–11:00 IST

        await run_test(
            service,
            "Before existing appointment",
            dt("2026-09-24T08:00:00"),
            dt("2026-09-24T09:00:00"),
            False,
        )

        await run_test(
            service,
            "After existing appointment",
            dt("2026-09-24T11:00:00"),
            dt("2026-09-24T12:00:00"),
            False,
        )

        await run_test(
            service,
            "Exact same time",
            dt("2026-09-24T10:00:00"),
            dt("2026-09-24T11:00:00"),
            True,
        )

        await run_test(
            service,
            "Overlaps existing start",
            dt("2026-09-24T09:30:00"),
            dt("2026-09-24T10:30:00"),
            True,
        )

        await run_test(
            service,
            "Overlaps existing end",
            dt("2026-09-24T10:30:00"),
            dt("2026-09-24T11:30:00"),
            True,
        )

        await run_test(
            service,
            "Existing appointment inside requested window",
            dt("2026-09-24T09:00:00"),
            dt("2026-09-24T12:00:00"),
            True,
        )

        await run_test(
            service,
            "Exact back-to-back",
            dt("2026-09-24T11:00:00"),
            dt("2026-09-24T12:00:00"),
            False,
        )

        # ---------------------------------------------------------
        # 5. Exclude current appointment service
        # ---------------------------------------------------------

        actual = await service.has_conflict(
            organization_id=ORG_ID,
            resource_id=RESOURCE_ID,
            branch_id=BRANCH_ID,
            requested_start=dt("2026-09-24T10:00:00"),
            requested_end=dt("2026-09-24T11:00:00"),
            exclude_appointment_service_id=appointment_service_id,
        )

        result = "PASS" if actual is False else "FAIL"

        print(
            f"{result} | Exclude current appointment | "
            f"Expected=False, Actual={actual}"
        )

        # ---------------------------------------------------------
        # 6. Appointment status behavior
        # ---------------------------------------------------------

        statuses = [
            (AppointmentStatus.DRAFT, "DRAFT"),
            (AppointmentStatus.COMPLETED, "COMPLETED"),
            (AppointmentStatus.CANCELLED, "CANCELLED"),
            (AppointmentStatus.NO_SHOW, "NO_SHOW"),
        ]

        for status, name in statuses:

            appointment.status = status

            await session.flush()

            await run_test(
                service,
                f"{name} appointment",
                dt("2026-09-24T10:00:00"),
                dt("2026-09-24T11:00:00"),
                False,
            )

        # ---------------------------------------------------------
        # 7. Restore appointment status
        # ---------------------------------------------------------

        appointment.status = AppointmentStatus.BOOKED

        await session.commit()

        print()
        print("Appointment status restored to BOOKED.")
        print("Resource conflict tests completed.")


if __name__ == "__main__":
    asyncio.run(main())