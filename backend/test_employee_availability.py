import asyncio
from datetime import datetime
from uuid import UUID

from app.database import AsyncSessionLocal
from app.modules.scheduling.services.employee_availability_service import (
    EmployeeAvailabilityService,
)


ORG_ID = UUID("5d3602f7-042b-4422-a030-5360569b68e5")
BRANCH_ID = UUID("9a8d84b8-56fa-434d-8546-73ea75b35a42")
EMPLOYEE_ID = UUID("452afac3-6df2-4dba-ab1a-e2927f8b37a6")


async def run_test(
    service,
    name,
    start,
    end,
    expected,
):
    actual = await service.is_employee_available(
        organization_id=ORG_ID,
        employee_id=EMPLOYEE_ID,
        branch_id=BRANCH_ID,
        scheduled_start=datetime.fromisoformat(start),
        scheduled_end=datetime.fromisoformat(end),
    )

    result = "PASS" if actual == expected else "FAIL"

    print(
        f"{result} | {name} | "
        f"Expected={expected}, Actual={actual}"
    )


async def main():
    async with AsyncSessionLocal() as session:
        service = EmployeeAvailabilityService(session)

        # Monday 21 September 2026
        await run_test(
            service,
            "Inside morning schedule",
            "2026-09-21T10:00:00+05:30",
            "2026-09-21T11:00:00+05:30",
            True,
        )

        await run_test(
            service,
            "Inside afternoon schedule",
            "2026-09-21T15:00:00+05:30",
            "2026-09-21T16:00:00+05:30",
            True,
        )

        await run_test(
            service,
            "Before working hours",
            "2026-09-21T08:00:00+05:30",
            "2026-09-21T09:00:00+05:30",
            False,
        )

        await run_test(
            service,
            "After working hours",
            "2026-09-21T20:00:00+05:30",
            "2026-09-21T21:00:00+05:30",
            False,
        )

        await run_test(
            service,
            "Crossing lunch break",
            "2026-09-21T12:30:00+05:30",
            "2026-09-21T14:30:00+05:30",
            False,
        )

        await run_test(
            service,
            "Exactly morning closing",
            "2026-09-21T12:00:00+05:30",
            "2026-09-21T13:00:00+05:30",
            True,
        )

        await run_test(
            service,
            "Exactly afternoon opening",
            "2026-09-21T14:00:00+05:30",
            "2026-09-21T15:00:00+05:30",
            True,
        )

        # Saturday
        await run_test(
            service,
            "Saturday",
            "2026-09-19T10:00:00+05:30",
            "2026-09-19T11:00:00+05:30",
            False,
        )

        # Invalid range
        await run_test(
            service,
            "Invalid time range",
            "2026-09-21T12:00:00+05:30",
            "2026-09-21T11:00:00+05:30",
            False,
        )

        # Crossing midnight
        await run_test(
            service,
            "Crossing midnight",
            "2026-09-21T23:00:00+05:30",
            "2026-09-22T01:00:00+05:30",
            False,
        )

                # Tuesday - full day OFF exception
        await run_test(
            service,
            "Full-day OFF exception",
            "2026-09-22T10:00:00+05:30",
            "2026-09-22T11:00:00+05:30",
            False,
        )

        # Wednesday - partial OFF exception
        await run_test(
            service,
            "Inside partial OFF exception",
            "2026-09-23T11:15:00+05:30",
            "2026-09-23T11:45:00+05:30",
            False,
        )

        await run_test(
            service,
            "Before partial OFF exception",
            "2026-09-23T10:00:00+05:30",
            "2026-09-23T10:30:00+05:30",
            True,
        )

        await run_test(
            service,
            "After partial OFF exception",
            "2026-09-23T12:30:00+05:30",
            "2026-09-23T13:00:00+05:30",
            True,
        )

        # Saturday - WORK exception
        await run_test(
            service,
            "WORK exception on normally off day",
            "2026-09-26T10:30:00+05:30",
            "2026-09-26T11:30:00+05:30",
            True,
        )

        await run_test(
            service,
            "Outside WORK exception",
            "2026-09-26T15:00:00+05:30",
            "2026-09-26T16:00:00+05:30",
            False,
        )


if __name__ == "__main__":
    asyncio.run(main())