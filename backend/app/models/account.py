from pydantic import BaseModel, ConfigDict, Field


class SignUpRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class AccountUpdateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)


class NotificationPreferences(BaseModel):
    policy_updates: bool = True
    product_updates: bool = False


class AccountResponse(BaseModel):
    id: str
    name: str
    email: str
    notifications: NotificationPreferences

    model_config = ConfigDict(extra="forbid")
