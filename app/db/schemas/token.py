from pydantic import BaseModel

### SCHEMAS FOR TOKENS ###


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str = None
    permissions: str = "user"
