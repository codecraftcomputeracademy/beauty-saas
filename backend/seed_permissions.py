import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal
import app.model_registry  # noqa: F401

from app.modules.authorization.models.permission import Permission


PERMISSIONS = [
    {
        "code": "CUSTOMER_VIEW",
        "name": "View Customers",
        "description": "Allows viewing customer records",
        "module": "CUSTOMER",
    },
    {
        "code": "CUSTOMER_CREATE",
        "name": "Create Customers",
        "description": "Allows creating customer records",
        "module": "CUSTOMER",
    },
    {
        "code": "CUSTOMER_UPDATE",
        "name": "Update Customers",
        "description": "Allows updating customer records",
        "module": "CUSTOMER",
    },
    {
        "code": "CUSTOMER_DELETE",
        "name": "Delete Customers",
        "description": "Allows deleting customer records",
        "module": "CUSTOMER",
    },
    {
        "code": "APPOINTMENT_VIEW",
        "name": "View Appointments",
        "description": "Allows viewing appointments",
        "module": "APPOINTMENT",
    },
    {
        "code": "APPOINTMENT_CREATE",
        "name": "Create Appointments",
        "description": "Allows creating appointments",
        "module": "APPOINTMENT",
    },
    {
        "code": "APPOINTMENT_UPDATE",
        "name": "Update Appointments",
        "description": "Allows updating appointments",
        "module": "APPOINTMENT",
    },
    {
        "code": "APPOINTMENT_CANCEL",
        "name": "Cancel Appointments",
        "description": "Allows cancelling appointments",
        "module": "APPOINTMENT",
    },
    {
        "code": "EMPLOYEE_VIEW",
        "name": "View Employees",
        "description": "Allows viewing employee records",
        "module": "EMPLOYEE",
    },
    {
        "code": "EMPLOYEE_CREATE",
        "name": "Create Employees",
        "description": "Allows creating employee records",
        "module": "EMPLOYEE",
    },
    {
        "code": "EMPLOYEE_UPDATE",
        "name": "Update Employees",
        "description": "Allows updating employee records",
        "module": "EMPLOYEE",
    },
    {
        "code": "INVOICE_VIEW",
        "name": "View Invoices",
        "description": "Allows viewing invoices",
        "module": "INVOICE",
    },
    {
        "code": "INVOICE_CREATE",
        "name": "Create Invoices",
        "description": "Allows creating invoices",
        "module": "INVOICE",
    },
    {
        "code": "INVOICE_REFUND",
        "name": "Refund Invoices",
        "description": "Allows refunding invoices",
        "module": "INVOICE",
    },
    {
        "code": "INVENTORY_VIEW",
        "name": "View Inventory",
        "description": "Allows viewing inventory",
        "module": "INVENTORY",
    },
    {
        "code": "INVENTORY_ADJUST",
        "name": "Adjust Inventory",
        "description": "Allows adjusting inventory quantities",
        "module": "INVENTORY",
    },
    {
        "code": "INVENTORY_TRANSFER",
        "name": "Transfer Inventory",
        "description": "Allows transferring inventory between locations",
        "module": "INVENTORY",
    },
]


async def seed_permissions():
    async with AsyncSessionLocal() as session:
        created = 0
        existing = 0

        for data in PERMISSIONS:
            result = await session.execute(
                select(Permission).where(
                    Permission.code == data["code"]
                )
            )

            permission = result.scalar_one_or_none()

            if permission:
                existing += 1
                print(f"EXISTS: {permission.code}")
                continue

            permission = Permission(
                code=data["code"],
                name=data["name"],
                description=data["description"],
                module=data["module"],
                status="ACTIVE",
            )

            session.add(permission)
            await session.flush()

            created += 1
            print(f"CREATED: {permission.code}")

        await session.commit()

        print()
        print(f"Permissions created: {created}")
        print(f"Permissions already existed: {existing}")
        print(f"Total permissions: {created + existing}")


if __name__ == "__main__":
    asyncio.run(seed_permissions())

    