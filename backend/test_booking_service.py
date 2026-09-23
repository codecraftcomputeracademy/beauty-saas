import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID

import app.model_registry  # noqa: F401

from app.database import AsyncSessionLocal
from app.modules.scheduling.services.booking_service import (
    BookingService,
    BookingValidationReason,
)


ORG_ID = UUID(
    "5d3602f7-042b-4422-a030-5360569b68e5"
)

BRANCH_ID = UUID(
    "9a8d84b8-56fa-434d-8546-73ea75b35a42"
)

EMPLOYEE_ID = UUID(
    "452afac3-6df2-4dba-ab1a-e2927f8b37a6"
)

RESOURCE_ID = UUID(
    "8b249905-312f-4629-97b3-ec8e8ea24ff7"
)

IST = timezone(timedelta(hours=5, minutes=30))

BRANCH_SERVICE_ID = UUID(
    "4cb9478b-6d00-4c28-b9c5-22111b0c4ea5"
)

def dt(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(
        tzinfo=IST
    )


async def run_test(
    service: BookingService,
    name: str,
    start: datetime,
    end: datetime,
    employee_ids: list[UUID],
    resource_ids: list[UUID],
    expected_allowed: bool,
    expected_reason: BookingValidationReason | None,
):
    result = await service.validate_booking(
        organization_id=ORG_ID,
        branch_id=BRANCH_ID,
        branch_service_id=BRANCH_SERVICE_ID,
        scheduled_start=start,
        scheduled_end=end,
        employee_ids=employee_ids,
        resource_ids=resource_ids,
    )

    passed = (
        result.allowed == expected_allowed
        and result.reason == expected_reason
    )

    status = "PASS" if passed else "FAIL"

    print(
        f"{status} | {name} | "
        f"Expected=({expected_allowed}, {expected_reason}), "
        f"Actual=({result.allowed}, {result.reason})"
    )


async def main():
    async with AsyncSessionLocal() as session:

        service = BookingService(session)

        print()
        print("BOOKING SERVICE TESTS")
        print("---------------------")

        # ---------------------------------------------------------
        # 1. Valid booking
        #
        # 2026-09-24 is Thursday.
        #
        # Employee:
        # Thursday 09:00–13:00
        #
        # Resource:
        # Thursday 09:00–13:00
        #
        # Existing appointment is 10:00–11:00, so use 11:00–12:00.
        # ---------------------------------------------------------

        await run_test(
            service,
            "Valid booking",
            dt("2026-09-24T11:00:00"),
            dt("2026-09-24T12:00:00"),
            [EMPLOYEE_ID],
            [RESOURCE_ID],
            True,
            None,
        )

        # ---------------------------------------------------------
        # 2. Branch unavailable
        #
        # Saturday is normally closed.
        # ---------------------------------------------------------

        await run_test(
            service,
            "Branch unavailable",
            dt("2026-09-26T10:00:00"),
            dt("2026-09-26T11:00:00"),
            [EMPLOYEE_ID],
            [RESOURCE_ID],
            False,
            BookingValidationReason.BRANCH_UNAVAILABLE,
        )

        # ---------------------------------------------------------
        # 3. Employee unavailable
        #
        # Wednesday 11:00–12:00 has an employee OFF exception.
        # Branch itself is available.
        # ---------------------------------------------------------

        await run_test(
            service,
            "Employee unavailable",
            dt("2026-09-23T11:00:00"),
            dt("2026-09-23T12:00:00"),
            [EMPLOYEE_ID],
            [RESOURCE_ID],
            False,
            BookingValidationReason.EMPLOYEE_UNAVAILABLE,
        )

        # ---------------------------------------------------------
        # 4. Employee conflict
        #
        # Existing appointment:
        # 10:00–11:00
        # ---------------------------------------------------------

        await run_test(
            service,
            "Employee conflict",
            dt("2026-09-24T10:30:00"),
            dt("2026-09-24T11:30:00"),
            [EMPLOYEE_ID],
            [],
            False,
            BookingValidationReason.EMPLOYEE_CONFLICT,
        )

        # ---------------------------------------------------------
        # 5. Resource unavailable
        #
        # Wednesday 11:00–12:00 has a resource OFF exception.
        # ---------------------------------------------------------

        await run_test(
            service,
            "Resource unavailable",
            dt("2026-09-23T11:00:00"),
            dt("2026-09-23T12:00:00"),
            [],
            [RESOURCE_ID],
            False,
            BookingValidationReason.RESOURCE_UNAVAILABLE,
        )

        # ---------------------------------------------------------
        # 6. Resource conflict
        #
        # Existing appointment:
        # 10:00–11:00
        # ---------------------------------------------------------

        await run_test(
            service,
            "Resource conflict",
            dt("2026-09-24T10:30:00"),
            dt("2026-09-24T11:30:00"),
            [],
            [RESOURCE_ID],
            False,
            BookingValidationReason.RESOURCE_CONFLICT,
        )

        # ---------------------------------------------------------
        # 7. Invalid time
        # ---------------------------------------------------------

        await run_test(
            service,
            "Invalid time",
            dt("2026-09-24T12:00:00"),
            dt("2026-09-24T11:00:00"),
            [],
            [],
            False,
            BookingValidationReason.INVALID_TIME,
        )

        # ---------------------------------------------------------
        # 8. Exact boundary booking
        #
        # Existing appointment ends at 11:00.
        # Back-to-back booking from 11:00 is valid.
        # ---------------------------------------------------------

        await run_test(
            service,
            "Exact back-to-back booking",
            dt("2026-09-24T11:00:00"),
            dt("2026-09-24T12:00:00"),
            [EMPLOYEE_ID],
            [RESOURCE_ID],
            True,
            None,
        )

        # --------------------------------------------------------- # 9. Invalid time # --------------------------------------------------------- 
        await run_test( 
            service,
            "Invalid time", 
            dt("2026-09-24T12:00:00"), 
            dt("2026-09-24T11:00:00"), 
            [], 
            [], 
            False, 
            BookingValidationReason.INVALID_TIME, 
        )

        await run_test( 
            service, 
            "Exact back-to-back booking", 
            dt("2026-09-24T11:00:00"), 
            dt("2026-09-24T12:00:00"), 
            [EMPLOYEE_ID], 
            [RESOURCE_ID], 
            True, 
            None, 
        )

        print()
        print("Booking service tests completed.")


if __name__ == "__main__":
    asyncio.run(main())