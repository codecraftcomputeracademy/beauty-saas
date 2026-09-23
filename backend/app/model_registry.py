# Organization
from app.modules.organization.models.organization import Organization
from app.modules.organization.models.branch import Branch

# Identity
from app.modules.identity.models.user import User

# Authorization

from app.modules.authorization.models.permission import Permission
from app.modules.authorization.models.role import Role
from app.modules.authorization.models.role_assignment import RoleAssignment
from app.modules.authorization.models.role_permission import RolePermission

from app.modules.employee.models.employee import Employee
from app.modules.employee.models.designation import Designation
from app.modules.employee.models.employee_designation import EmployeeDesignation
from app.modules.employee.models.employee_branch_assignment import (
    EmployeeBranchAssignment,
)

# Catalog
from app.modules.catalog.models.skill import Skill
from app.modules.employee.models.employee_skill import EmployeeSkill
from app.modules.catalog.models.service_category import ServiceCategory
from app.modules.catalog.models.service import Service

from app.modules.catalog.models.service_skill_requirement import (
    ServiceSkillRequirement,
)
from app.modules.catalog.models.branch_service import BranchService

# Customer
from app.modules.customer.models.customer import Customer
from app.modules.customer.models.contact_point import ContactPoint
from app.modules.customer.models.customer_contact_point import (
    CustomerContactPoint,
)

from app.modules.customer.models.customer_relationship_type import (
    CustomerRelationshipType,
)

from app.modules.customer.models.customer_relationship import CustomerRelationship


from app.modules.scheduling.models.branch_business_hours import (
    BranchBusinessHours,
)
from app.modules.scheduling.models.branch_holiday import BranchHoliday
from app.modules.scheduling.models.employee_work_schedule import (
    EmployeeWorkSchedule,
)

from app.modules.scheduling.models.employee_schedule_exception import (
    EmployeeScheduleException,
)

from app.modules.scheduling.models.resource import Resource
from app.modules.scheduling.models.resource_work_schedule import (
    ResourceWorkSchedule,
)

from app.modules.scheduling.models.resource_schedule_exception import (
    ResourceScheduleException,
)

from app.modules.scheduling.models.appointment import Appointment
from app.modules.scheduling.models.appointment_service import AppointmentService

from app.modules.scheduling.models.appointment_service_employee import (
    AppointmentServiceEmployee,
)

from app.modules.scheduling.models.appointment_service_resource import (
    AppointmentServiceResource,
)

from app.modules.scheduling.models.appointment_event import AppointmentEvent