import asyncio
from datetime import datetime
from uuid import UUID

from app.database import AsyncSessionLocal
from app.modules.scheduling.services.employee_conflict_service import (
    EmployeeConflictService,
)


ORG_ID = UUID("5d3602f7-042b-4422-a030-5360569b68e5")
BRANCH_ID = UUID("9a8d84b8-56fa-434d-8546-73ea75b35a42")
EMPLOYEE_ID = UUID("452afac3-6df2-4dba-ab1a-e2927f8b37a6")

APPOINTMENT_SERVICE_ID = UUID(
    "77d2710d-f0bc-4d53-83bf-ec56d9d490e2"
)


async def run_test(
    service,
    name,
    start,
    end,
    expected,
    exclude_id=None,
):
    actual = await service.has_conflict(
        organization_id=ORG_ID,
        employee_id=EMPLOYEE_ID,
        branch_id=BRANCH_ID,
        requested_start=datetime.fromisoformat(start),
        requested_end=datetime.fromisoformat(end),
        exclude_appointment_service_id=exclude_id,
    )

    result = "PASS" if actual == expected else "FAIL"

    print(
        f"{result} | {name} | "
        f"Expected={expected}, Actual={actual}"
    )


async def main():
    async with AsyncSessionLocal() as session:
        service = EmployeeConflictService(session)

        # Existing appointment:
        # 10:00 - 11:00

        await run_test(
            service,
            "Before existing appointment",
            "2026-09-24T08:00:00+05:30",
            "2026-09-24T09:00:00+05:30",
            False,
        )

        await run_test(
            service,
            "After existing appointment",
            "2026-09-24T11:00:00+05:30",
            "2026-09-24T12:00:00+05:30",
            False,
        )

        await run_test(
            service,
            "Exact same time",
            "2026-09-24T10:00:00+05:30",
            "2026-09-24T11:00:00+05:30",
            True,
        )

        await run_test(
            service,
            "Overlaps existing start",
            "2026-09-24T09:30:00+05:30",
            "2026-09-24T10:30:00+05:30",
            True,
        )

        await run_test(
            service,
            "Overlaps existing end",
            "2026-09-24T10:30:00+05:30",
            "2026-09-24T11:30:00+05:30",
            True,
        )

        await run_test(
            service,
            "Existing appointment inside request",
            "2026-09-24T09:00:00+05:30",
            "2026-09-24T12:00:00+05:30",
            True,
        )

        await run_test(
            service,
            "Exact back-to-back",
            "2026-09-24T11:00:00+05:30",
            "2026-09-24T12:00:00+05:30",
            False,
        )

        await run_test(
            service,
            "Exclude current appointment",
            "2026-09-24T10:00:00+05:30",
            "2026-09-24T11:00:00+05:30",
            False,
            exclude_id=APPOINTMENT_SERVICE_ID,
        )


if __name__ == "__main__":
    asyncio.run(main())