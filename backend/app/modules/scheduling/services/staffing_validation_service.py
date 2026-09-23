from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models.service import Service
from app.modules.catalog.models.service_skill_requirement import (
    ServiceSkillRequirement,
)
from app.modules.employee.models.employee_skill import EmployeeSkill


@dataclass(frozen=True)
class StaffingValidationResult:
    allowed: bool
    missing_skill_id: UUID | None = None
    required_count: int | None = None
    qualified_count: int | None = None


class StaffingValidationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def validate_staffing(
        self,
        organization_id: UUID,
        service_id: UUID,
        employee_ids: list[UUID],
        effective_date: date,
    ) -> StaffingValidationResult:

        # ---------------------------------------------------------
        # 1. Verify that the service belongs to this organization.
        # ---------------------------------------------------------
        service_stmt = select(Service.id).where(
            Service.id == service_id,
            Service.organization_id == organization_id,
        )

        service_result = await self.session.execute(service_stmt)

        if service_result.scalar_one_or_none() is None:
            return StaffingValidationResult(allowed=False)

        # ---------------------------------------------------------
        # 2. Get service skill requirements.
        # ---------------------------------------------------------
        requirement_stmt = select(
            ServiceSkillRequirement.skill_id,
            ServiceSkillRequirement.required_count,
        ).where(
            ServiceSkillRequirement.organization_id == organization_id,
            ServiceSkillRequirement.service_id == service_id,
        )

        requirement_result = await self.session.execute(
            requirement_stmt
        )

        requirements = requirement_result.all()

        if not requirements:
            return StaffingValidationResult(allowed=True)

        # ---------------------------------------------------------
        # 3. Remove duplicate employees.
        # ---------------------------------------------------------
        unique_employee_ids = list(dict.fromkeys(employee_ids))

        if not unique_employee_ids:
            skill_id, required_count = requirements[0]

            return StaffingValidationResult(
                allowed=False,
                missing_skill_id=skill_id,
                required_count=required_count,
                qualified_count=0,
            )

        # ---------------------------------------------------------
        # 4. Check each required skill independently.
        # ---------------------------------------------------------
        for skill_id, required_count in requirements:

            skill_stmt = select(
                EmployeeSkill.employee_id,
            ).where(
                EmployeeSkill.organization_id == organization_id,
                EmployeeSkill.employee_id.in_(unique_employee_ids),
                EmployeeSkill.skill_id == skill_id,
                EmployeeSkill.status == "ACTIVE",
                EmployeeSkill.from_date <= effective_date,
                (
                    EmployeeSkill.to_date.is_(None)
                    | (
                        EmployeeSkill.to_date
                        >= effective_date
                    )
                ),
            )

            skill_result = await self.session.execute(skill_stmt)

            qualified_employee_ids = set(
                skill_result.scalars().all()
            )

            qualified_count = len(qualified_employee_ids)

            if qualified_count < required_count:
                return StaffingValidationResult(
                    allowed=False,
                    missing_skill_id=skill_id,
                    required_count=required_count,
                    qualified_count=qualified_count,
                )

        return StaffingValidationResult(allowed=True)