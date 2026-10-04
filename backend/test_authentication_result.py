from uuid import UUID

from app.modules.identity.schemas.authentication import AuthenticationResult


def main():
    user_id = UUID("30aaaffe-58ca-4bc7-9420-453c29c19992")
    organization_id = UUID("5d3602f7-042b-4422-a030-5360569b68e5")

    result = AuthenticationResult(
        access_token="test-access-token",
        user_id=user_id,
        organization_id=organization_id,
    )

    assert result.access_token == "test-access-token"
    assert result.token_type == "bearer"
    assert result.user_id == user_id
    assert result.organization_id == organization_id

    print("PASS: AuthenticationResult fields")
    print("PASS: default token_type")
    print("PASS: UUID validation")
    print("\nAll AuthenticationResult tests passed.")


if __name__ == "__main__":
    main()