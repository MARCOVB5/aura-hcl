from fastapi import APIRouter, Response

from app.deps import AuthServiceDep, CurrentUserDep
from app.schemas.Auth import CurrentUserOut, LoginRequest, TokenOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(data: LoginRequest, response: Response, service: AuthServiceDep):
    response.headers["Cache-Control"] = "no-store"
    return TokenOut(access_token=service.login(data.username, data.password))


@router.get("/me", response_model=CurrentUserOut)
def me(user: CurrentUserDep):
    practitioner = user.practitioner
    return CurrentUserOut(
        id=user.id, username=user.username, practitioner_id=practitioner.id,
        name_given=practitioner.person.name_given,
        name_family=practitioner.person.name_family, profession=practitioner.profession,
    )
