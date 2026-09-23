from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.scheduling.models.branch_business_hours import (
    BranchBusinessHours,
)
from app.modules.scheduling.models.branch_holiday import (
    BranchHoliday,
)


class SchedulingAvailabilityService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def is_branch_available(
        self,
        organization_id: UUID,
        branch_id: UUID,
        scheduled_start: datetime,
        scheduled_end: datetime,
    ) -> bool:
        """
        Check whether a branch is open and available for the
        requested time range.

        This checks:
        1. Date/time validity
        2. Branch holiday
        3. Business hours
        """

        if scheduled_start >= scheduled_end:
            return False

        if scheduled_start.date() != scheduled_end.date():
            return False

        # ---------------------------------------------------------
        # 1. Check branch holiday
        # ---------------------------------------------------------

        holiday_result = await self.session.execute(
            select(BranchHoliday.id)
            .where(
                BranchHoliday.organization_id == organization_id,
                BranchHoliday.branch_id == branch_id,
                BranchHoliday.holiday_date == scheduled_start.date(),
                BranchHoliday.status.is_(True),
            )
            .limit(1)
        )

        if holiday_result.scalar_one_or_none() is not None:
            return False

        # ---------------------------------------------------------
        # 2. Check business hours
        # ---------------------------------------------------------

        day_of_week = scheduled_start.weekday()

        result = await self.session.execute(
            select(BranchBusinessHours)
            .where(
                BranchBusinessHours.organization_id == organization_id,
                BranchBusinessHours.branch_id == branch_id,
                BranchBusinessHours.day_of_week == day_of_week,
            )
        )

        business_hours = result.scalars().all()

        if not business_hours:
            return False

        requested_start = scheduled_start.time()
        requested_end = scheduled_end.time()

        for interval in business_hours:

            if interval.is_closed:
                continue

            if (
                interval.opens_at is not None
                and interval.closes_at is not None
                and interval.opens_at <= requested_start
                and interval.closes_at >= requested_end
            ):
                return True

        return False