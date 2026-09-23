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
from app.modules.employee.models.employee import Employee
from app.modules.employee.models.employee_skill import EmployeeSkill
from app.modules.scheduling.services.staffing_validation_service import (
    StaffingValidationService,
)


ORGANIZATION_ID = UUID(
    "5d3602f7-042b-4422-a030-5360569b68e5"
)

EMPLOYEE_A_ID = UUID(
    "452afac3-6df2-4dba-ab1a-e2927f8b37a6"
)

EFFECTIVE_DATE = date(2026, 9, 22)


async def main():
    async with AsyncSessionLocal() as session:
        try:
            # ---------------------------------------------------------
            # Verify existing employee
            # ---------------------------------------------------------
            employee_result = await session.execute(
                select(Employee).where(
                    Employee.id == EMPLOYEE_A_ID,
                    Employee.organization_id == ORGANIZATION_ID,
                )
            )

            employee_a = employee_result.scalar_one()

            print(
                f"Using existing employee: "
                f"{employee_a.id} | {employee_a.display_name}"
            )

            # ---------------------------------------------------------
            # Create second employee
            # ---------------------------------------------------------
            employee_b = Employee(
                organization_id=ORGANIZATION_ID,
                employee_code=f"TEST-STAFF-{uuid4().hex[:8]}",
                first_name="Staffing",
                last_name="Employee B",
                display_name="Staffing Employee B",
                status="ACTIVE",
            )

            session.add(employee_b)
            await session.flush()

            # ---------------------------------------------------------
            # Create category
            # ---------------------------------------------------------
            category = ServiceCategory(
                organization_id=ORGANIZATION_ID,
                code=f"STAFF-CAT-{uuid4().hex[:8]}",
                name=f"Staffing Test Category {uuid4().hex[:8]}",
            )

            session.add(category)
            await session.flush()

            # ---------------------------------------------------------
            # Create skills
            # ---------------------------------------------------------
            skill_1 = Skill(
                organization_id=ORGANIZATION_ID,
                code=f"STAFF-SKILL-1-{uuid4().hex[:8]}",
                name=f"Staffing Skill 1 {uuid4().hex[:8]}",
            )

            skill_2 = Skill(
                organization_id=ORGANIZATION_ID,
                code=f"STAFF-SKILL-2-{uuid4().hex[:8]}",
                name=f"Staffing Skill 2 {uuid4().hex[:8]}",
            )

            skill_3 = Skill(
                organization_id=ORGANIZATION_ID,
                code=f"STAFF-SKILL-3-{uuid4().hex[:8]}",
                name=f"Staffing Skill 3 {uuid4().hex[:8]}",
            )

            session.add_all([skill_1, skill_2, skill_3])
            await session.flush()

            # ---------------------------------------------------------
            # Create service
            # ---------------------------------------------------------
            service = Service(
                organization_id=ORGANIZATION_ID,
                category_id=category.id,
                code=f"STAFF-SERVICE-{uuid4().hex[:8]}",
                name=f"Staffing Test Service {uuid4().hex[:8]}",
                duration_minutes=60,
            )

            session.add(service)
            await session.flush()

            # ---------------------------------------------------------
            # Service requirements
            #
            # Skill 1 requires TWO qualified employees.
            # Skill 2 requires ONE qualified employee.
            # ---------------------------------------------------------
            requirement_1 = ServiceSkillRequirement(
                organization_id=ORGANIZATION_ID,
                service_id=service.id,
                skill_id=skill_1.id,
                required_count=2,
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
            # Employee A has both skills.
            # ---------------------------------------------------------
            employee_a_skill_1 = EmployeeSkill(
                organization_id=ORGANIZATION_ID,
                employee_id=EMPLOYEE_A_ID,
                skill_id=skill_1.id,
                from_date=date(2026, 1, 1),
                status="ACTIVE",
            )

            employee_a_skill_2 = EmployeeSkill(
                organization_id=ORGANIZATION_ID,
                employee_id=EMPLOYEE_A_ID,
                skill_id=skill_2.id,
                from_date=date(2026, 1, 1),
                status="ACTIVE",
            )

            # ---------------------------------------------------------
            # Employee B initially has only skill 1.
            # ---------------------------------------------------------
            employee_b_skill_1 = EmployeeSkill(
                organization_id=ORGANIZATION_ID,
                employee_id=employee_b.id,
                skill_id=skill_1.id,
                from_date=date(2026, 1, 1),
                status="ACTIVE",
            )

            session.add_all(
                [
                    employee_a_skill_1,
                    employee_a_skill_2,
                    employee_b_skill_1,
                ]
            )

            await session.flush()

            staffing_service = StaffingValidationService(session)

            # ---------------------------------------------------------
            # 1. Two employees satisfy required_count = 2
            # ---------------------------------------------------------
            result = await staffing_service.validate_staffing(
                organization_id=ORGANIZATION_ID,
                service_id=service.id,
                employee_ids=[
                    EMPLOYEE_A_ID,
                    employee_b.id,
                ],
                effective_date=EFFECTIVE_DATE,
            )

            print(
                f"1. Two qualified employees | "
                f"Expected=True, Actual={result.allowed}"
            )

            assert result.allowed is True

            # ---------------------------------------------------------
            # 2. Only one employee — insufficient for skill 1
            # ---------------------------------------------------------
            result = await staffing_service.validate_staffing(
                organization_id=ORGANIZATION_ID,
                service_id=service.id,
                employee_ids=[
                    EMPLOYEE_A_ID,
                ],
                effective_date=EFFECTIVE_DATE,
            )

            print(
                f"2. One employee for required_count=2 | "
                f"Expected=False, Actual={result.allowed}"
            )

            assert result.allowed is False
            assert result.missing_skill_id == skill_1.id
            assert result.required_count == 2
            assert result.qualified_count == 1

            # ---------------------------------------------------------
            # 3. Duplicate employee must count only once
            # ---------------------------------------------------------
            result = await staffing_service.validate_staffing(
                organization_id=ORGANIZATION_ID,
                service_id=service.id,
                employee_ids=[
                    EMPLOYEE_A_ID,
                    EMPLOYEE_A_ID,
                ],
                effective_date=EFFECTIVE_DATE,
            )

            print(
                f"3. Duplicate employee | "
                f"Expected=False, Actual={result.allowed}"
            )

            assert result.allowed is False
            assert result.qualified_count == 1

            # ---------------------------------------------------------
            # 4. Employee without all required skills does not count
            #
            # Employee B has skill 1 but not skill 2.
            # Therefore Employee B is not qualified for the service.
            # ---------------------------------------------------------
            await session.delete(employee_a_skill_2)
            await session.flush()

            result = await staffing_service.validate_staffing(
                organization_id=ORGANIZATION_ID,
                service_id=service.id,
                employee_ids=[
                    EMPLOYEE_A_ID,
                    employee_b.id,
                ],
                effective_date=EFFECTIVE_DATE,
            )

            print(
                f"4. Employees missing required skill | "
                f"Expected=False, Actual={result.allowed}"
            )

            assert result.allowed is False

            # ---------------------------------------------------------
            # Restore Employee A skill 2.
            # ---------------------------------------------------------
            employee_a_skill_2 = EmployeeSkill(
                organization_id=ORGANIZATION_ID,
                employee_id=EMPLOYEE_A_ID,
                skill_id=skill_2.id,
                from_date=date(2026, 1, 1),
                status="ACTIVE",
            )

            session.add(employee_a_skill_2)
            await session.flush()

            # ---------------------------------------------------------
            # 5. Expired skill means employee no longer counts.
            # ---------------------------------------------------------
            employee_b_skill_1.to_date = date(2026, 9, 21)
            await session.flush()

            result = await staffing_service.validate_staffing(
                organization_id=ORGANIZATION_ID,
                service_id=service.id,
                employee_ids=[
                    EMPLOYEE_A_ID,
                    employee_b.id,
                ],
                effective_date=EFFECTIVE_DATE,
            )

            print(
                f"5. Expired employee skill | "
                f"Expected=False, Actual={result.allowed}"
            )

            assert result.allowed is False
            assert result.qualified_count == 1

            # ---------------------------------------------------------
            # 6. Service with no requirements
            # ---------------------------------------------------------
            empty_service = Service(
                organization_id=ORGANIZATION_ID,
                category_id=category.id,
                code=f"STAFF-EMPTY-{uuid4().hex[:8]}",
                name=f"No Staffing Requirement {uuid4().hex[:8]}",
                duration_minutes=30,
            )

            session.add(empty_service)
            await session.flush()

            result = await staffing_service.validate_staffing(
                organization_id=ORGANIZATION_ID,
                service_id=empty_service.id,
                employee_ids=[],
                effective_date=EFFECTIVE_DATE,
            )

            print(
                f"6. No skill requirements | "
                f"Expected=True, Actual={result.allowed}"
            )

            assert result.allowed is True

            # ---------------------------------------------------------
            # 7. Cross-organization request
            # ---------------------------------------------------------
            result = await staffing_service.validate_staffing(
                        organization_id=uuid4(),
                        service_id=service.id,
                        employee_ids=[
                        EMPLOYEE_A_ID,
                        employee_b.id,
                        ],
                        effective_date=EFFECTIVE_DATE,
                    )

            print(
                    f"7. Different organization | "
                    f"Expected=False, Actual={result.allowed}"
                )

            assert result.allowed is False

            # result = await staffing_service.validate_staffing(
            #     organization_id=uuid4(),
            #     service_id=service.id,
            #     employee_ids=[
            #         EMPLOYEE_A_ID,
            #         employee_b.id,
            #     ],
            #     effective_date=EFFECTIVE_DATE,
            # )

            # print(
            #     f"7. Different organization | "
            #     f"Expected=True, Actual={result.allowed}"
            # )

            # No requirements are visible in another organization,
            # so this currently exposes an important distinction:
            # StaffingValidationService must verify service ownership.
            #
            # We deliberately assert the current expected behavior
            # only after seeing this case.
            # assert result.allowed is True

            await session.rollback()

            print("\nALL STAFFING VALIDATION TESTS PASSED")

        except Exception:
            await session.rollback()
            raise


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())