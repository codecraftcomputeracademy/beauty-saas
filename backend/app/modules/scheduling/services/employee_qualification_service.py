from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models.service import Service
from app.modules.catalog.models.service_skill_requirement import (
    ServiceSkillRequirement,
)
from app.modules.employee.models.employee_skill import EmployeeSkill
from app.modules.catalog.models.service import Service

class EmployeeQualificationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def is_employee_qualified(
        self,
        organization_id: UUID,
        employee_id: UUID,
        service_id: UUID,
        effective_date: date,
    ) -> bool:
        """
        Return True when the employee possesses every skill required
        by the service on the effective date.

        required_count is intentionally not evaluated here.
        It represents staffing capacity and is handled separately.
        """

        # Get all skills required by the service.
        service_stmt = select(Service.id).where(
            Service.id == service_id,
            Service.organization_id == organization_id,
        )

        service_result = await self.session.execute(service_stmt)

        if service_result.scalar_one_or_none() is None:
            return False

        # ---------------------------------------------------------
        # 2. Get skills required by this service.
        # ---------------------------------------------------------
        requirement_stmt = select(
            ServiceSkillRequirement.skill_id,
        ).where(
            ServiceSkillRequirement.organization_id == organization_id,
            ServiceSkillRequirement.service_id == service_id,
        )

        requirement_result = await self.session.execute(
            requirement_stmt
        )

        required_skill_ids = set(
            requirement_result.scalars().all()
        )

        # ---------------------------------------------------------
        # 3. No skill requirements means no skill qualification
        #    is necessary.
        # ---------------------------------------------------------
        if not required_skill_ids:
            return True

        # ---------------------------------------------------------
        # 4. Find employee skills effective on the requested date.
        # ---------------------------------------------------------
        employee_skill_stmt = select(
            EmployeeSkill.skill_id,
        ).where(
            EmployeeSkill.organization_id == organization_id,
            EmployeeSkill.employee_id == employee_id,
            EmployeeSkill.skill_id.in_(required_skill_ids),
            EmployeeSkill.status == "ACTIVE",
            EmployeeSkill.from_date <= effective_date,
            (
                EmployeeSkill.to_date.is_(None)
                | (EmployeeSkill.to_date >= effective_date)
            ),
        )

        employee_skill_result = await self.session.execute(
            employee_skill_stmt
        )

        employee_skill_ids = set(
            employee_skill_result.scalars().all()
        )

        # ---------------------------------------------------------
        # 5. Employee must possess every required skill.
        # ---------------------------------------------------------
        return required_skill_ids.issubset(employee_skill_ids)