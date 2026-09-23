from uuid import UUID, uuid4

from sqlalchemy import select

from app.database import AsyncSessionLocal
import app.model_registry  # noqa: F401

from app.modules.catalog.models.branch_service import BranchService
from app.modules.catalog.models.branch_service_resource_requirement import (
    BranchServiceResourceRequirement,
)
from app.modules.catalog.models.service import Service
from app.modules.catalog.models.service_category import ServiceCategory
from app.modules.scheduling.models.resource import Resource
from app.modules.scheduling.services.resource_requirement_validation_service import (
    ResourceRequirementValidationService,
)
from app.modules.organization.models.branch import Branch


ORGANIZATION_ID = UUID(
    "5d3602f7-042b-4422-a030-5360569b68e5"
)

BRANCH_ID = UUID(
    "9a8d84b8-56fa-434d-8546-73ea75b35a42"
)


async def main():
    async with AsyncSessionLocal() as session:
        try:
            # ---------------------------------------------------------
            # Verify existing branch
            # ---------------------------------------------------------
            branch_result = await session.execute(
                select(Branch).where(
                    Branch.id == BRANCH_ID,
                    Branch.organization_id == ORGANIZATION_ID,
                )
            )

            branch = branch_result.scalar_one()

            print(
                f"Using branch: "
                f"{branch.id} | {branch.name}"
            )

            # ---------------------------------------------------------
            # Create category
            # ---------------------------------------------------------
            category = ServiceCategory(
                organization_id=ORGANIZATION_ID,
                code=f"RES-CAT-{uuid4().hex[:8]}",
                name=f"Resource Test Category {uuid4().hex[:8]}",
            )

            session.add(category)
            await session.flush()

            # ---------------------------------------------------------
            # Create service
            # ---------------------------------------------------------
            service = Service(
                organization_id=ORGANIZATION_ID,
                category_id=category.id,
                code=f"RES-SERVICE-{uuid4().hex[:8]}",
                name=f"Resource Requirement Service {uuid4().hex[:8]}",
                duration_minutes=60,
            )

            session.add(service)
            await session.flush()

            # ---------------------------------------------------------
            # Create BranchService
            # ---------------------------------------------------------
            branch_service = BranchService(
                organization_id=ORGANIZATION_ID,
                branch_id=BRANCH_ID,
                service_id=service.id,
                price=1000,
                status=True,
            )

            session.add(branch_service)
            await session.flush()

            # ---------------------------------------------------------
            # Create resources
            # ---------------------------------------------------------
            resource_1 = Resource(
                organization_id=ORGANIZATION_ID,
                branch_id=BRANCH_ID,
                code=f"RES-01-{uuid4().hex[:8]}",
                name="Test Chair 01",
                resource_type="CHAIR",
                status="ACTIVE",
            )

            resource_2 = Resource(
                organization_id=ORGANIZATION_ID,
                branch_id=BRANCH_ID,
                code=f"RES-02-{uuid4().hex[:8]}",
                name="Test Chair 02",
                resource_type="CHAIR",
                status="ACTIVE",
            )

            resource_3 = Resource(
                organization_id=ORGANIZATION_ID,
                branch_id=BRANCH_ID,
                code=f"RES-03-{uuid4().hex[:8]}",
                name="Test Room 01",
                resource_type="ROOM",
                status="ACTIVE",
            )

            session.add_all(
                [
                    resource_1,
                    resource_2,
                    resource_3,
                ]
            )

            await session.flush()

            # ---------------------------------------------------------
            # Requirements:
            #
            # Chair 01 → 1
            # Chair 02 → 1
            # Room 01  → 1
            # ---------------------------------------------------------
            requirement_1 = BranchServiceResourceRequirement(
                organization_id=ORGANIZATION_ID,
                branch_id=BRANCH_ID,
                branch_service_id=branch_service.id,
                resource_id=resource_1.id,
                required_count=1,
            )

            requirement_2 = BranchServiceResourceRequirement(
                organization_id=ORGANIZATION_ID,
                branch_id=BRANCH_ID,
                branch_service_id=branch_service.id,
                resource_id=resource_2.id,
                required_count=1,
            )

            requirement_3 = BranchServiceResourceRequirement(
                organization_id=ORGANIZATION_ID,
                branch_id=BRANCH_ID,
                branch_service_id=branch_service.id,
                resource_id=resource_3.id,
                required_count=1,
            )

            session.add_all(
                [
                    requirement_1,
                    requirement_2,
                    requirement_3,
                ]
            )

            await session.flush()

            validation_service = (
                ResourceRequirementValidationService(session)
            )

            # ---------------------------------------------------------
            # 1. All required resources assigned
            # ---------------------------------------------------------
            result = await validation_service.validate_resources(
                organization_id=ORGANIZATION_ID,
                branch_id=BRANCH_ID,
                branch_service_id=branch_service.id,
                resource_ids=[
                    resource_1.id,
                    resource_2.id,
                    resource_3.id,
                ],
            )

            print(
                f"1. All required resources | "
                f"Expected=True, Actual={result.allowed}"
            )

            assert result.allowed is True

            # ---------------------------------------------------------
            # 2. One required resource missing
            # ---------------------------------------------------------
            result = await validation_service.validate_resources(
                organization_id=ORGANIZATION_ID,
                branch_id=BRANCH_ID,
                branch_service_id=branch_service.id,
                resource_ids=[
                    resource_1.id,
                    resource_2.id,
                ],
            )

            print(
                f"2. Missing required resource | "
                f"Expected=False, Actual={result.allowed}"
            )

            assert result.allowed is False
            assert result.missing_resource_id == resource_3.id
            assert result.required_count == 1
            assert result.assigned_count == 0

            # ---------------------------------------------------------
            # 3. Extra resource is allowed
            # ---------------------------------------------------------
            result = await validation_service.validate_resources(
                organization_id=ORGANIZATION_ID,
                branch_id=BRANCH_ID,
                branch_service_id=branch_service.id,
                resource_ids=[
                    resource_1.id,
                    resource_2.id,
                    resource_3.id,
                    uuid4(),
                ],
            )

            print(
                f"3. Extra resource | "
                f"Expected=True, Actual={result.allowed}"
            )

            assert result.allowed is True

            # ---------------------------------------------------------
            # 4. Duplicate resource cannot count twice
            #
            # Change requirement temporarily to 2.
            # ---------------------------------------------------------
            requirement_1.required_count = 2
            await session.flush()

            result = await validation_service.validate_resources(
                organization_id=ORGANIZATION_ID,
                branch_id=BRANCH_ID,
                branch_service_id=branch_service.id,
                resource_ids=[
                    resource_1.id,
                    resource_1.id,
                    resource_2.id,
                    resource_3.id,
                ],
            )

            print(
                f"4. Duplicate resource cannot count twice | "
                f"Expected=False, Actual={result.allowed}"
            )

            assert result.allowed is False
            assert result.missing_resource_id == resource_1.id
            assert result.required_count == 2
            assert result.assigned_count == 1

            # Restore requirement.
            requirement_1.required_count = 1
            await session.flush()

            # ---------------------------------------------------------
            # 5. No resource requirements
            # ---------------------------------------------------------
            no_requirement_service = Service(
                organization_id=ORGANIZATION_ID,
                category_id=category.id,
                code=f"RES-NONE-{uuid4().hex[:8]}",
                name=f"No Resource Service {uuid4().hex[:8]}",
                duration_minutes=30,
            )

            session.add(no_requirement_service)
            await session.flush()

            no_requirement_branch_service = BranchService(
                organization_id=ORGANIZATION_ID,
                branch_id=BRANCH_ID,
                service_id=no_requirement_service.id,
                price=500,
                status=True,
            )

            session.add(no_requirement_branch_service)
            await session.flush()

            result = await validation_service.validate_resources(
                organization_id=ORGANIZATION_ID,
                branch_id=BRANCH_ID,
                branch_service_id=no_requirement_branch_service.id,
                resource_ids=[],
            )

            print(
                f"5. No resource requirements | "
                f"Expected=True, Actual={result.allowed}"
            )

            assert result.allowed is True

            # ---------------------------------------------------------
            # 6. Different branch
            # ---------------------------------------------------------
            different_branch_id = uuid4()

            result = await validation_service.validate_resources(
                organization_id=ORGANIZATION_ID,
                branch_id=different_branch_id,
                branch_service_id=branch_service.id,
                resource_ids=[
                    resource_1.id,
                    resource_2.id,
                    resource_3.id,
                ],
            )

            print(
                f"6. Different branch | "
                f"Expected=True, Actual={result.allowed}"
            )

            # Currently this returns True because the query finds
            # no requirements for the supplied branch.
            #
            # This is a diagnostic test for branch ownership.
            assert result.allowed is True

            # ---------------------------------------------------------
            # 7. Different organization
            # ---------------------------------------------------------
            result = await validation_service.validate_resources(
                organization_id=uuid4(),
                branch_id=BRANCH_ID,
                branch_service_id=branch_service.id,
                resource_ids=[
                    resource_1.id,
                    resource_2.id,
                    resource_3.id,
                ],
            )

            print(
                f"7. Different organization | "
                f"Expected=True, Actual={result.allowed}"
            )

            # Same diagnostic situation as branch isolation.
            assert result.allowed is True

            await session.rollback()

            print(
                "\nALL RESOURCE REQUIREMENT VALIDATION "
                "TESTS PASSED"
            )

        except Exception:
            await session.rollback()
            raise


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())