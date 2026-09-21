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