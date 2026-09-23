import asyncio
from datetime import datetime, timezone, timedelta
from uuid import UUID

from app.database import AsyncSessionLocal
from app.modules.scheduling.services.resource_availability_service import (
    ResourceAvailabilityService,
)

ORG_ID = UUID("5d3602f7-042b-4422-a030-5360569b68e5")
BRANCH_ID = UUID("9a8d84b8-56fa-434d-8546-73ea75b35a42")
RESOURCE_ID = UUID("8b249905-312f-4629-97b3-ec8e8ea24ff7")

IST = timezone(timedelta(hours=5, minutes=30))


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=IST)


async def run_test(
    service,
    name: str,
    start: datetime,
    end: datetime,
    expected: bool,
):
    actual = await service.is_resource_available(
        organization_id=ORG_ID,
        resource_id=RESOURCE_ID,
        branch_id=BRANCH_ID,
        scheduled_start=start,
        scheduled_end=end,
    )

    result = "PASS" if actual == expected else "FAIL"

    print(
        f"{result} | {name} | "
        f"Expected={expected}, Actual={actual}"
    )


async def main():
    async with AsyncSessionLocal() as session:

        service = ResourceAvailabilityService(session)

        # ---------------------------------------------------------
        # 1. Normal weekday availability
        # ---------------------------------------------------------

        await run_test(
            service,
            "Morning inside schedule",
            dt("2026-09-21T10:00:00"),
            dt("2026-09-21T11:00:00"),
            True,
        )

        await run_test(
            service,
            "Afternoon inside schedule",
            dt("2026-09-21T15:00:00"),
            dt("2026-09-21T16:00:00"),
            True,
        )

        # ---------------------------------------------------------
        # 2. Outside schedule
        # ---------------------------------------------------------

        await run_test(
            service,
            "Before opening",
            dt("2026-09-21T08:00:00"),
            dt("2026-09-21T09:00:00"),
            False,
        )

        await run_test(
            service,
            "After closing",
            dt("2026-09-21T20:00:00"),
            dt("2026-09-21T21:00:00"),
            False,
        )

        # ---------------------------------------------------------
        # 3. Lunch break
        # ---------------------------------------------------------

        await run_test(
            service,
            "Crossing lunch break",
            dt("2026-09-21T12:30:00"),
            dt("2026-09-21T14:30:00"),
            False,
        )

        # ---------------------------------------------------------
        # 4. Exact boundaries
        # ---------------------------------------------------------

        await run_test(
            service,
            "Exact morning boundaries",
            dt("2026-09-21T09:00:00"),
            dt("2026-09-21T13:00:00"),
            True,
        )

        await run_test(
            service,
            "Exact afternoon boundaries",
            dt("2026-09-21T14:00:00"),
            dt("2026-09-21T20:00:00"),
            True,
        )

        # ---------------------------------------------------------
        # 5. Weekend
        # ---------------------------------------------------------

        await run_test(
            service,
            "Saturday normally unavailable",
            dt("2026-09-26T09:00:00"),
            dt("2026-09-26T10:00:00"),
            False,
        )

        # ---------------------------------------------------------
        # 6. Invalid / cross-midnight
        # ---------------------------------------------------------

        await run_test(
            service,
            "Invalid range",
            dt("2026-09-21T12:00:00"),
            dt("2026-09-21T11:00:00"),
            False,
        )

        await run_test(
            service,
            "Cross midnight",
            dt("2026-09-21T23:00:00"),
            dt("2026-09-22T01:00:00"),
            False,
        )

        # ---------------------------------------------------------
        # 7. Full-day OFF exception
        # ---------------------------------------------------------

        await run_test(
            service,
            "Full-day OFF exception",
            dt("2026-09-22T10:00:00"),
            dt("2026-09-22T11:00:00"),
            False,
        )

        # ---------------------------------------------------------
        # 8. Partial OFF exception
        # ---------------------------------------------------------

        await run_test(
            service,
            "Partial OFF - inside exception",
            dt("2026-09-23T11:15:00"),
            dt("2026-09-23T11:45:00"),
            False,
        )

        await run_test(
            service,
            "Partial OFF - before exception",
            dt("2026-09-23T09:00:00"),
            dt("2026-09-23T10:00:00"),
            True,
        )

        await run_test(
            service,
            "Partial OFF - after exception",
            dt("2026-09-23T12:00:00"),
            dt("2026-09-23T13:00:00"),
            True,
        )

        # ---------------------------------------------------------
        # 9. WORK exception on normally unavailable Saturday
        # ---------------------------------------------------------

        await run_test(
            service,
            "WORK exception inside special availability",
            dt("2026-09-26T10:00:00"),
            dt("2026-09-26T12:00:00"),
            True,
        )

        await run_test(
            service,
            "Outside WORK exception",
            dt("2026-09-26T14:00:00"),
            dt("2026-09-26T15:00:00"),
            False,
        )

        print()
        print("Resource availability tests completed.")


if __name__ == "__main__":
    asyncio.run(main())