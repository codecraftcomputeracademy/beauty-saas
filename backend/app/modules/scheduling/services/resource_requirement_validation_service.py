from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models.branch_service_resource_requirement import (
    BranchServiceResourceRequirement,
)


@dataclass(frozen=True)
class ResourceRequirementValidationResult:
    allowed: bool
    missing_resource_id: UUID | None = None
    required_count: int | None = None
    assigned_count: int | None = None


class ResourceRequirementValidationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def validate_resources(
        self,
        organization_id: UUID,
        branch_id: UUID,
        branch_service_id: UUID,
        resource_ids: list[UUID],
    ) -> ResourceRequirementValidationResult:

        # ---------------------------------------------------------
        # 1. Get resource requirements for this branch service.
        # ---------------------------------------------------------
        requirement_stmt = select(
            BranchServiceResourceRequirement.resource_id,
            BranchServiceResourceRequirement.required_count,
        ).where(
            BranchServiceResourceRequirement.organization_id
            == organization_id,
            BranchServiceResourceRequirement.branch_id
            == branch_id,
            BranchServiceResourceRequirement.branch_service_id
            == branch_service_id,
        )

        result = await self.session.execute(requirement_stmt)
        requirements = result.all()

        # No resource requirements means no resource assignment
        # is required by the service.
        if not requirements:
            return ResourceRequirementValidationResult(
                allowed=True,
            )

        # ---------------------------------------------------------
        # 2. Remove duplicate resource IDs.
        #
        # One physical resource must never count twice.
        # ---------------------------------------------------------
        unique_resource_ids = set(resource_ids)

        # ---------------------------------------------------------
        # 3. Check every resource requirement.
        #
        # Each requirement represents a physical resource type/
        # resource record and its required quantity.
        # ---------------------------------------------------------
        for resource_id, required_count in requirements:

            assigned_count = (
                1
                if resource_id in unique_resource_ids
                else 0
            )

            if assigned_count < required_count:
                return ResourceRequirementValidationResult(
                    allowed=False,
                    missing_resource_id=resource_id,
                    required_count=required_count,
                    assigned_count=assigned_count,
                )

        return ResourceRequirementValidationResult(
            allowed=True,
        )