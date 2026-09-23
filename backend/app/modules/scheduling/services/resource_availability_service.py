from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.scheduling.models.resource_schedule_exception import (
    ResourceScheduleException,
)
from app.modules.scheduling.models.resource_work_schedule import (
    ResourceWorkSchedule,
)


class ResourceAvailabilityService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def is_resource_available(
        self,
        organization_id: UUID,
        resource_id: UUID,
        branch_id: UUID,
        scheduled_start: datetime,
        scheduled_end: datetime,
    ) -> bool:

        # 1. Invalid range
        if scheduled_start >= scheduled_end:
            return False

        # 2. Cross-midnight requests are not supported
        if scheduled_start.date() != scheduled_end.date():
            return False

        requested_date = scheduled_start.date()
        weekday = scheduled_start.weekday()

        # 3. Resource must have a schedule exception or recurring
        # schedule belonging to the requested organization/branch.
        exception_stmt = (
            select(ResourceScheduleException)
            .where(
                ResourceScheduleException.organization_id
                == organization_id,
                ResourceScheduleException.resource_id
                == resource_id,
                ResourceScheduleException.branch_id
                == branch_id,
                ResourceScheduleException.exception_date
                == requested_date,
            )
        )

        result = await self.session.execute(exception_stmt)
        exceptions = result.scalars().all()

        # 4. Process exceptions first.
        for exception in exceptions:

            exception_type = exception.exception_type.value

            # Full-day OFF
            if (
                exception_type == "OFF"
                and exception.starts_at is None
                and exception.ends_at is None
            ):
                return False

        # 5. WORK exceptions can override the recurring schedule.
        for exception in exceptions:

            exception_type = exception.exception_type.value

            if (
                exception_type == "WORK"
                and exception.starts_at is not None
                and exception.ends_at is not None
            ):
                if (
                    exception.starts_at <= scheduled_start.time()
                    and exception.ends_at >= scheduled_end.time()
                ):
                    return True

        # 6. Partial OFF exception blocks overlapping requests.
        for exception in exceptions:

            exception_type = exception.exception_type.value

            if (
                exception_type == "OFF"
                and exception.starts_at is not None
                and exception.ends_at is not None
            ):
                if (
                    exception.starts_at < scheduled_end.time()
                    and exception.ends_at > scheduled_start.time()
                ):
                    return False

        # 7. Check recurring resource schedule.
        schedule_stmt = (
            select(ResourceWorkSchedule)
            .where(
                ResourceWorkSchedule.organization_id
                == organization_id,
                ResourceWorkSchedule.resource_id
                == resource_id,
                ResourceWorkSchedule.branch_id
                == branch_id,
                ResourceWorkSchedule.day_of_week
                == weekday,
            )
        )

        result = await self.session.execute(schedule_stmt)
        schedules = result.scalars().all()

        # 8. Requested interval must be fully contained
        # within at least one recurring schedule interval.
        for schedule in schedules:
            if (
                schedule.starts_at <= scheduled_start.time()
                and schedule.ends_at >= scheduled_end.time()
            ):
                return True

        # 9. No matching schedule.
        return False