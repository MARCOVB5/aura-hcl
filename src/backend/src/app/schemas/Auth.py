from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        value = value.strip().lower()
        if not value:
            raise ValueError("Username must not be empty")
        return value


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 28800


class CurrentUserOut(BaseModel):
    id: int
    username: str
    practitioner_id: int
    name_given: str | None
    name_family: str | None
    profession: str | None
