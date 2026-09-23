import asyncio
from datetime import datetime
from uuid import UUID

from app.database import AsyncSessionLocal
from app.modules.scheduling.services.availability_service import (
    SchedulingAvailabilityService,
)


ORGANIZATION_ID = UUID("5d3602f7-042b-4422-a030-5360569b68e5")
BRANCH_ID = UUID("9a8d84b8-56fa-434d-8546-73ea75b35a42")


async def run_test(
    service,
    name,
    start,
    end,
    expected,
):
    result = await service.is_branch_available(
        organization_id=ORGANIZATION_ID,
        branch_id=BRANCH_ID,
        scheduled_start=datetime.fromisoformat(start),
        scheduled_end=datetime.fromisoformat(end),
    )

    passed = result == expected

    print(
        f"{'PASS' if passed else 'FAIL'} | "
        f"{name} | "
        f"Expected={expected}, Actual={result}"
    )


async def main():
    async with AsyncSessionLocal() as session:

        service = SchedulingAvailabilityService(session)

        # 2026-09-21 is Monday
        await run_test(
            service,
            "Inside morning hours",
            "2026-09-21T10:00:00+05:30",
            "2026-09-21T11:00:00+05:30",
            True,
        )

        await run_test(
            service,
            "Inside afternoon hours",
            "2026-09-21T15:00:00+05:30",
            "2026-09-21T16:00:00+05:30",
            True,
        )

        await run_test(
            service,
            "Before opening",
            "2026-09-21T08:00:00+05:30",
            "2026-09-21T09:00:00+05:30",
            False,
        )

        await run_test(
            service,
            "After closing",
            "2026-09-21T20:00:00+05:30",
            "2026-09-21T21:00:00+05:30",
            False,
        )

        await run_test(
            service,
            "Crossing lunch break",
            "2026-09-21T12:00:00+05:30",
            "2026-09-21T15:00:00+05:30",
            False,
        )

        await run_test(
            service,
            "Exactly morning closing time",
            "2026-09-21T12:00:00+05:30",
            "2026-09-21T13:00:00+05:30",
            True,
        )

        await run_test(
            service,
            "Exactly afternoon opening time",
            "2026-09-21T14:00:00+05:30",
            "2026-09-21T15:00:00+05:30",
            True,
        )

        await run_test(
            service,
            "Saturday closed",
            "2026-09-26T10:00:00+05:30",
            "2026-09-26T11:00:00+05:30",
            False,
        )

        await run_test(
            service,
            "Sunday closed",
            "2026-09-27T10:00:00+05:30",
            "2026-09-27T11:00:00+05:30",
            False,
        )

        await run_test(
            service,
            "Invalid time range",
            "2026-09-21T11:00:00+05:30",
            "2026-09-21T10:00:00+05:30",
            False,
        )

        await run_test(
            service,
            "Crossing midnight",
            "2026-09-21T23:00:00+05:30",
            "2026-09-22T01:00:00+05:30",
            False,
        )

        await run_test(
            service,
            "Active holiday",
            "2026-09-22T10:00:00+05:30",
            "2026-09-22T11:00:00+05:30",
            False,
        )


if __name__ == "__main__":
    asyncio.run(main())