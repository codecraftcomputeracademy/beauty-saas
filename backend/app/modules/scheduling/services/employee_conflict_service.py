from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.scheduling.models.appointment import Appointment
from app.modules.scheduling.models.appointment_service import AppointmentService
from app.modules.scheduling.models.appointment_service_employee import (
    AppointmentServiceEmployee,
)
from app.modules.scheduling.models.appointment import (
    Appointment,
    AppointmentStatus,
)


ACTIVE_STATUSES = (
    AppointmentStatus.BOOKED,
    AppointmentStatus.CONFIRMED,
    AppointmentStatus.IN_PROGRESS,
)


class EmployeeConflictService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def has_conflict(
        self,
        organization_id: UUID,
        employee_id: UUID,
        branch_id: UUID,
        requested_start: datetime,
        requested_end: datetime,
        exclude_appointment_service_id: UUID | None = None,
    ) -> bool:

        if requested_start >= requested_end:
            return False

        stmt = (
            select(AppointmentService.id)
            .join(
                AppointmentServiceEmployee,
                AppointmentServiceEmployee.appointment_service_id
                == AppointmentService.id,
            )
            .join(
                Appointment,
                Appointment.id == AppointmentService.appointment_id,
            )
            .where(
                AppointmentService.organization_id == organization_id,
                AppointmentService.branch_id == branch_id,
                AppointmentServiceEmployee.organization_id == organization_id,
                AppointmentServiceEmployee.branch_id == branch_id,
                AppointmentServiceEmployee.employee_id == employee_id,
                Appointment.branch_id == branch_id,
                Appointment.status.in_(ACTIVE_STATUSES),

                AppointmentService.scheduled_start < requested_end,
                AppointmentService.scheduled_end > requested_start,
            )
        )

        if exclude_appointment_service_id is not None:
            stmt = stmt.where(
                AppointmentService.id
                != exclude_appointment_service_id
            )

        stmt = stmt.limit(1)

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none() is not None