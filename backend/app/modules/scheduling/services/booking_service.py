from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models.branch_service import BranchService
from app.modules.scheduling.services.availability_service import (
    SchedulingAvailabilityService,
)
from app.modules.scheduling.services.employee_availability_service import (
    EmployeeAvailabilityService,
)
from app.modules.scheduling.services.employee_conflict_service import (
    EmployeeConflictService,
)
from app.modules.scheduling.services.resource_availability_service import (
    ResourceAvailabilityService,
)
from app.modules.scheduling.services.resource_conflict_service import (
    ResourceConflictService,
)
from app.modules.scheduling.services.resource_requirement_validation_service import (
    ResourceRequirementValidationService,
)
from app.modules.scheduling.services.staffing_validation_service import (
    StaffingValidationService,
)


class BookingValidationReason(str, Enum):
    INVALID_TIME = "INVALID_TIME"
    INVALID_BRANCH_SERVICE = "INVALID_BRANCH_SERVICE"

    BRANCH_UNAVAILABLE = "BRANCH_UNAVAILABLE"

    EMPLOYEE_UNAVAILABLE = "EMPLOYEE_UNAVAILABLE"
    EMPLOYEE_CONFLICT = "EMPLOYEE_CONFLICT"
    EMPLOYEE_STAFFING_INSUFFICIENT = (
        "EMPLOYEE_STAFFING_INSUFFICIENT"
    )

    RESOURCE_UNAVAILABLE = "RESOURCE_UNAVAILABLE"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    RESOURCE_REQUIREMENT_NOT_MET = (
        "RESOURCE_REQUIREMENT_NOT_MET"
    )


@dataclass(frozen=True)
class BookingValidationResult:
    allowed: bool
    reason: BookingValidationReason | None = None
    employee_id: UUID | None = None
    resource_id: UUID | None = None


class BookingService:
    def __init__(self, session: AsyncSession):
        self.session = session

        self.branch_availability = SchedulingAvailabilityService(
            session
        )

        self.employee_availability = EmployeeAvailabilityService(
            session
        )

        self.employee_conflict = EmployeeConflictService(
            session
        )

        self.resource_availability = ResourceAvailabilityService(
            session
        )

        self.resource_conflict = ResourceConflictService(
            session
        )

        self.staffing_validation = StaffingValidationService(
            session
        )

        self.resource_requirement_validation = (
            ResourceRequirementValidationService(session)
        )

    async def validate_booking(
        self,
        organization_id: UUID,
        branch_id: UUID,
        branch_service_id: UUID,
        scheduled_start: datetime,
        scheduled_end: datetime,
        employee_ids: list[UUID],
        resource_ids: list[UUID],
    ) -> BookingValidationResult:

        # ---------------------------------------------------------
        # 1. Basic time validation
        # ---------------------------------------------------------

        if scheduled_start >= scheduled_end:
            return BookingValidationResult(
                allowed=False,
                reason=BookingValidationReason.INVALID_TIME,
            )

        # ---------------------------------------------------------
        # 2. Validate Branch Service
        # ---------------------------------------------------------
        #
        # The service must actually be configured for this branch.
        # This also guarantees that the branch_service belongs to
        # the current organization and branch.
        # ---------------------------------------------------------

        branch_service_stmt = select(BranchService).where(
            BranchService.id == branch_service_id,
            BranchService.organization_id == organization_id,
            BranchService.branch_id == branch_id,
        )

        branch_service_result = await self.session.execute(
            branch_service_stmt
        )

        branch_service = branch_service_result.scalar_one_or_none()

        if branch_service is None:
            return BookingValidationResult(
                allowed=False,
                reason=BookingValidationReason.INVALID_BRANCH_SERVICE,
            )

        # ---------------------------------------------------------
        # 3. Branch availability
        # ---------------------------------------------------------

        branch_available = (
            await self.branch_availability.is_branch_available(
                organization_id=organization_id,
                branch_id=branch_id,
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_end,
            )
        )

        if not branch_available:
            return BookingValidationResult(
                allowed=False,
                reason=BookingValidationReason.BRANCH_UNAVAILABLE,
            )

        # ---------------------------------------------------------
        # 4. Employee staffing requirement
        # ---------------------------------------------------------
        #
        # Validate that the supplied employees satisfy the
        # staffing requirements of this BranchService.
        #
        # This is separate from individual employee availability
        # and conflict checking below.
        # ---------------------------------------------------------

        # staffing_result = (
        #     await self.staffing_validation.validate_staffing(
        #         organization_id=organization_id,
        #         branch_id=branch_id,
        #         # branch_service_id=branch_service_id,
        #         branch_service_id=branch_service.service_id,
        #         employee_ids=employee_ids,
        #         effective_date=scheduled_start.date(),
        #     )
        # )

        staffing_result = (
            await self.staffing_validation.validate_staffing(
                organization_id=organization_id,
                service_id=branch_service.service_id,
                employee_ids=employee_ids,
                effective_date=scheduled_start.date(),
                )
            )
        
        if not staffing_result.allowed:
            return BookingValidationResult(
                allowed=False,
                reason=(
                    BookingValidationReason
                    .EMPLOYEE_STAFFING_INSUFFICIENT
                ),
            )

        # ---------------------------------------------------------
        # 5. Employee availability + conflict
        # ---------------------------------------------------------

        for employee_id in employee_ids:

            employee_available = (
                await self.employee_availability.is_employee_available(
                    organization_id=organization_id,
                    employee_id=employee_id,
                    branch_id=branch_id,
                    scheduled_start=scheduled_start,
                    scheduled_end=scheduled_end,
                )
            )

            if not employee_available:
                return BookingValidationResult(
                    allowed=False,
                    reason=BookingValidationReason.EMPLOYEE_UNAVAILABLE,
                    employee_id=employee_id,
                )

            employee_has_conflict = (
                await self.employee_conflict.has_conflict(
                    organization_id=organization_id,
                    employee_id=employee_id,
                    branch_id=branch_id,
                    requested_start=scheduled_start,
                    requested_end=scheduled_end,
                )
            )

            if employee_has_conflict:
                return BookingValidationResult(
                    allowed=False,
                    reason=BookingValidationReason.EMPLOYEE_CONFLICT,
                    employee_id=employee_id,
                )

        # ---------------------------------------------------------
        # 6. Resource requirement validation
        # ---------------------------------------------------------
        #
        # Validate that the supplied resources satisfy the
        # BranchService resource requirements.
        # ---------------------------------------------------------

        resource_requirement_result = (
            await self.resource_requirement_validation.validate_resources(
                organization_id=organization_id,
                branch_id=branch_id,
                branch_service_id=branch_service_id,
                resource_ids=resource_ids,
            )
        )

        if not resource_requirement_result.allowed:
            return BookingValidationResult(
                allowed=False,
                reason=(
                    BookingValidationReason
                    .RESOURCE_REQUIREMENT_NOT_MET
                ),
            )

        # ---------------------------------------------------------
        # 7. Resource availability + conflict
        # ---------------------------------------------------------

        for resource_id in resource_ids:

            resource_available = (
                await self.resource_availability.is_resource_available(
                    organization_id=organization_id,
                    resource_id=resource_id,
                    branch_id=branch_id,
                    scheduled_start=scheduled_start,
                    scheduled_end=scheduled_end,
                )
            )

            if not resource_available:
                return BookingValidationResult(
                    allowed=False,
                    reason=BookingValidationReason.RESOURCE_UNAVAILABLE,
                    resource_id=resource_id,
                )

            resource_has_conflict = (
                await self.resource_conflict.has_conflict(
                    organization_id=organization_id,
                    resource_id=resource_id,
                    branch_id=branch_id,
                    requested_start=scheduled_start,
                    requested_end=scheduled_end,
                )
            )

            if resource_has_conflict:
                return BookingValidationResult(
                    allowed=False,
                    reason=BookingValidationReason.RESOURCE_CONFLICT,
                    resource_id=resource_id,
                )

        # ---------------------------------------------------------
        # 8. All validation checks passed
        # ---------------------------------------------------------

        return BookingValidationResult(
            allowed=True,
        )