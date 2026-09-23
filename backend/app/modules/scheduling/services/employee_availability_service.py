from datetime import date, datetime, time
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.employee.models.employee_branch_assignment import (
    EmployeeBranchAssignment,
)
from app.modules.scheduling.models.employee_schedule_exception import (
    EmployeeScheduleException,
)
from app.modules.scheduling.models.employee_work_schedule import (
    EmployeeWorkSchedule,
)


class EmployeeAvailabilityService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def is_employee_available(
        self,
        organization_id: UUID,
        employee_id: UUID,
        branch_id: UUID,
        scheduled_start: datetime,
        scheduled_end: datetime,
    ) -> bool:

        # ---------------------------------------------------------
        # 1. Basic time validation
        # ---------------------------------------------------------

        if scheduled_start >= scheduled_end:
            return False

        if scheduled_start.date() != scheduled_end.date():
            return False

        requested_date = scheduled_start.date()
        requested_start = scheduled_start.time()
        requested_end = scheduled_end.time()

        # ---------------------------------------------------------
        # 2. Employee must be assigned to the branch
        # ---------------------------------------------------------

        assignment_result = await self.session.execute(
            select(EmployeeBranchAssignment.id)
            .where(
                EmployeeBranchAssignment.organization_id
                == organization_id,
                EmployeeBranchAssignment.employee_id
                == employee_id,
                EmployeeBranchAssignment.branch_id
                == branch_id,
                EmployeeBranchAssignment.from_date <= requested_date,
                (
                    EmployeeBranchAssignment.to_date.is_(None)
                    | (
                        EmployeeBranchAssignment.to_date
                        >= requested_date
                    )
                ),
            )
            .limit(1)
        )

        assignment = assignment_result.scalar_one_or_none()

        if assignment is None:
            return False

        # ---------------------------------------------------------
        # 3. Check date-specific exceptions
        # ---------------------------------------------------------

        exception_result = await self.session.execute(
            select(EmployeeScheduleException)
            .where(
                EmployeeScheduleException.organization_id
                == organization_id,
                EmployeeScheduleException.employee_id
                == employee_id,
                EmployeeScheduleException.branch_id
                == branch_id,
                EmployeeScheduleException.exception_date
                == requested_date,
            )
        )

        exceptions = exception_result.scalars().all()

        # A full-day OFF exception blocks everything.
        for exception in exceptions:
            if (
                exception.exception_type.value == "OFF"
                and exception.starts_at is None
                and exception.ends_at is None
            ):
                return False

        # ---------------------------------------------------------
        # 4. WORK exceptions explicitly add availability
        # ---------------------------------------------------------

        for exception in exceptions:
            if (
                exception.exception_type.value == "WORK"
                and exception.starts_at is not None
                and exception.ends_at is not None
                and exception.starts_at <= requested_start
                and exception.ends_at >= requested_end
            ):
                return True

        # ---------------------------------------------------------
        # 5. OFF interval exceptions remove availability
        # ---------------------------------------------------------

        for exception in exceptions:
            if (
                exception.exception_type.value == "OFF"
                and exception.starts_at is not None
                and exception.ends_at is not None
                and exception.starts_at < requested_end
                and exception.ends_at > requested_start
            ):
                return False

        # ---------------------------------------------------------
        # 6. Check recurring employee work schedule
        # ---------------------------------------------------------

        day_of_week = requested_date.weekday()

        schedule_result = await self.session.execute(
            select(EmployeeWorkSchedule)
            .where(
                EmployeeWorkSchedule.organization_id
                == organization_id,
                EmployeeWorkSchedule.employee_id
                == employee_id,
                EmployeeWorkSchedule.branch_id
                == branch_id,
                EmployeeWorkSchedule.day_of_week
                == day_of_week,
            )
        )

        schedules = schedule_result.scalars().all()

        if not schedules:
            return False

        # Requested time must fit completely inside
        # one recurring work interval.
        for schedule in schedules:
            if (
                schedule.starts_at <= requested_start
                and schedule.ends_at >= requested_end
            ):
                return True

        return False