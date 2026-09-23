from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import select

from app.database import AsyncSessionLocal
import app.model_registry  # noqa: F401

from app.modules.catalog.models.service import Service
from app.modules.catalog.models.service_category import ServiceCategory
from app.modules.catalog.models.service_skill_requirement import (
    ServiceSkillRequirement,
)
from app.modules.catalog.models.skill import Skill
from app.modules.employee.models.employee_skill import EmployeeSkill
from app.modules.scheduling.services.employee_qualification_service import (
    EmployeeQualificationService,
)



# ORGANIZATION_ID = uuid4("5d3602f7-042b-4422-a030-5360569b68e5")
# EMPLOYEE_ID = uuid4("452afac3-6df2-4dba-ab1a-e2927f8b37a6")

ORGANIZATION_ID = UUID("5d3602f7-042b-4422-a030-5360569b68e5")
EMPLOYEE_ID = UUID("452afac3-6df2-4dba-ab1a-e2927f8b37a6")

EFFECTIVE_DATE = date(2026, 9, 22)


async def main():
    async with AsyncSessionLocal() as session:
        try:
            # ---------------------------------------------------------
            # Verify existing employee belongs to the test organization
            # ---------------------------------------------------------
            from app.modules.employee.models.employee import Employee

            employee_result = await session.execute(
                select(Employee).where(
                    Employee.id == EMPLOYEE_ID,
                    Employee.organization_id == ORGANIZATION_ID,
                )
            )

            employee = employee_result.scalar_one()

            print(
                f"Using employee: "
                f"{employee.id} | {employee.display_name}"
            )

            # ---------------------------------------------------------
            # Create test category
            # ---------------------------------------------------------
            category = ServiceCategory(
                organization_id=ORGANIZATION_ID,
                code=f"QUAL-CAT-{uuid4().hex[:8]}",
                name=f"Qualification Test Category {uuid4().hex[:8]}",
            )

            session.add(category)
            await session.flush()

            # ---------------------------------------------------------
            # Create test skills
            # ---------------------------------------------------------
            skill_1 = Skill(
                organization_id=ORGANIZATION_ID,
                code=f"QUAL-SKILL-1-{uuid4().hex[:8]}",
                name=f"Qualification Skill 1 {uuid4().hex[:8]}",
            )

            skill_2 = Skill(
                organization_id=ORGANIZATION_ID,
                code=f"QUAL-SKILL-2-{uuid4().hex[:8]}",
                name=f"Qualification Skill 2 {uuid4().hex[:8]}",
            )

            skill_3 = Skill(
                organization_id=ORGANIZATION_ID,
                code=f"QUAL-SKILL-3-{uuid4().hex[:8]}",
                name=f"Qualification Skill 3 {uuid4().hex[:8]}",
            )

            session.add_all([skill_1, skill_2, skill_3])
            await session.flush()

            # ---------------------------------------------------------
            # Create service requiring skill 1 + skill 2
            # ---------------------------------------------------------
            service = Service(
                organization_id=ORGANIZATION_ID,
                category_id=category.id,
                code=f"QUAL-SERVICE-{uuid4().hex[:8]}",
                name=f"Qualification Test Service {uuid4().hex[:8]}",
                duration_minutes=60,
            )

            session.add(service)
            await session.flush()

            requirement_1 = ServiceSkillRequirement(
                organization_id=ORGANIZATION_ID,
                service_id=service.id,
                skill_id=skill_1.id,
                required_count=1,
            )

            requirement_2 = ServiceSkillRequirement(
                organization_id=ORGANIZATION_ID,
                service_id=service.id,
                skill_id=skill_2.id,
                required_count=1,
            )

            session.add_all([requirement_1, requirement_2])
            await session.flush()

            # ---------------------------------------------------------
            # Employee has both required skills
            # ---------------------------------------------------------
            employee_skill_1 = EmployeeSkill(
                organization_id=ORGANIZATION_ID,
                employee_id=EMPLOYEE_ID,
                skill_id=skill_1.id,
                from_date=date(2026, 1, 1),
                status="ACTIVE",
            )

            employee_skill_2 = EmployeeSkill(
                organization_id=ORGANIZATION_ID,
                employee_id=EMPLOYEE_ID,
                skill_id=skill_2.id,
                from_date=date(2026, 1, 1),
                status="ACTIVE",
            )

            session.add_all([employee_skill_1, employee_skill_2])
            await session.flush()

            qualification_service = EmployeeQualificationService(session)

            # ---------------------------------------------------------
            # 1. All required skills
            # ---------------------------------------------------------
            result = await qualification_service.is_employee_qualified(
                organization_id=ORGANIZATION_ID,
                employee_id=EMPLOYEE_ID,
                service_id=service.id,
                effective_date=EFFECTIVE_DATE,
            )

            print(
                f"1. All required skills | "
                f"Expected=True, Actual={result}"
            )
            assert result is True

            # ---------------------------------------------------------
            # 2. Missing one required skill
            # ---------------------------------------------------------
            await session.delete(employee_skill_2)
            await session.flush()

            result = await qualification_service.is_employee_qualified(
                organization_id=ORGANIZATION_ID,
                employee_id=EMPLOYEE_ID,
                service_id=service.id,
                effective_date=EFFECTIVE_DATE,
            )

            print(
                f"2. Missing required skill | "
                f"Expected=False, Actual={result}"
            )
            assert result is False

            # Restore skill 2
            employee_skill_2 = EmployeeSkill(
                organization_id=ORGANIZATION_ID,
                employee_id=EMPLOYEE_ID,
                skill_id=skill_2.id,
                from_date=date(2026, 1, 1),
                status="ACTIVE",
            )

            session.add(employee_skill_2)
            await session.flush()

            # ---------------------------------------------------------
            # 3. Expired skill
            #
            # Replace requirement 2 with skill 3.
            # Employee has skill 3 but it expired before effective date.
            # ---------------------------------------------------------
            await session.delete(requirement_2)
            await session.flush()

            requirement_3 = ServiceSkillRequirement(
                organization_id=ORGANIZATION_ID,
                service_id=service.id,
                skill_id=skill_3.id,
                required_count=1,
            )

            session.add(requirement_3)

            expired_skill = EmployeeSkill(
                organization_id=ORGANIZATION_ID,
                employee_id=EMPLOYEE_ID,
                skill_id=skill_3.id,
                from_date=date(2026, 1, 1),
                to_date=date(2026, 9, 21),
                status="ACTIVE",
            )

            session.add(expired_skill)
            await session.flush()

            result = await qualification_service.is_employee_qualified(
                organization_id=ORGANIZATION_ID,
                employee_id=EMPLOYEE_ID,
                service_id=service.id,
                effective_date=EFFECTIVE_DATE,
            )

            print(
                f"3. Expired skill | "
                f"Expected=False, Actual={result}"
            )
            assert result is False

            # ---------------------------------------------------------
            # 4. Skill starts in future
            # ---------------------------------------------------------
            expired_skill.to_date = None
            expired_skill.from_date = date(2026, 9, 23)
            await session.flush()

            result = await qualification_service.is_employee_qualified(
                organization_id=ORGANIZATION_ID,
                employee_id=EMPLOYEE_ID,
                service_id=service.id,
                effective_date=EFFECTIVE_DATE,
            )

            print(
                f"4. Future skill | "
                f"Expected=False, Actual={result}"
            )
            assert result is False

            # ---------------------------------------------------------
            # 5. Inactive skill
            # ---------------------------------------------------------
            expired_skill.from_date = date(2026, 1, 1)
            expired_skill.status = "INACTIVE"
            await session.flush()

            result = await qualification_service.is_employee_qualified(
                organization_id=ORGANIZATION_ID,
                employee_id=EMPLOYEE_ID,
                service_id=service.id,
                effective_date=EFFECTIVE_DATE,
            )

            print(
                f"5. Inactive skill | "
                f"Expected=False, Actual={result}"
            )
            assert result is False

            # ---------------------------------------------------------
            # 6. Service with no skill requirements
            # ---------------------------------------------------------
            empty_service = Service(
                organization_id=ORGANIZATION_ID,
                category_id=category.id,
                code=f"QUAL-EMPTY-{uuid4().hex[:8]}",
                name=f"No Skill Service {uuid4().hex[:8]}",
                duration_minutes=30,
            )

            session.add(empty_service)
            await session.flush()

            result = await qualification_service.is_employee_qualified(
                organization_id=ORGANIZATION_ID,
                employee_id=EMPLOYEE_ID,
                service_id=empty_service.id,
                effective_date=EFFECTIVE_DATE,
            )

            print(
                f"6. No skill requirements | "
                f"Expected=True, Actual={result}"
            )
            assert result is True

            # ---------------------------------------------------------
            # 7. Different organization
            # ---------------------------------------------------------
            different_organization_id = uuid4()

            result = await qualification_service.is_employee_qualified(
                organization_id=different_organization_id,
                employee_id=EMPLOYEE_ID,
                service_id=service.id,
                effective_date=EFFECTIVE_DATE,
            )

            print(
                f"7. Different organization | "
                f"Expected=False, Actual={result}"
            )
            assert result is False

            # ---------------------------------------------------------
            # Rollback all test data
            # ---------------------------------------------------------
            await session.rollback()

            print("\nALL EMPLOYEE QUALIFICATION TESTS PASSED")

        except Exception:
            await session.rollback()
            raise


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())