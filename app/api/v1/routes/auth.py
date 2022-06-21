from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException, status
from starlette.responses import JSONResponse
from datetime import timedelta

from db.crud.users import blacklist_token
from db.session import get_db
from utils.logger import logger, myself

from core import security
from core.auth import authenticate_user, get_current_active_user, sign_up_new_user

auth_router = r = APIRouter()

# from starlette.responses import HTMLResponse
# @r.get("/form", response_class=HTMLResponse)
# def form_get():
#     return '''<html<head></head><body><form method="post" action="/api/token">
#     <input type="text" name="username" value="hello"/><br>
#     <input type="password" name="password" value="world"/><br>
#     <input type="submit"/>
#     </form></body></html>'''


@r.post("/token")
def login(
    db=Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(
            minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        if user.is_superuser:
            permissions = "admin"
        else:
            permissions = "user"
        access_token = security.create_access_token(
            data={"sub": user.email, "permissions": permissions},
            expires_delta=access_token_expires,
        )

        return {"access_token": access_token, "token_type": "bearer", "permissions": permissions}

    # fastapi recommendation
    except HTTPException as e:
        logger.error(f'ERR:{myself()}: Invalid token {e}')
        raise HTTPException(status_code=400, detail="Invalid login.")

    except Exception as e:
        logger.error(f'ERR:{myself()}: {e}')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Invalid token request.')


@r.post("/signup")
def signup(
    db=Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    try:
        user = sign_up_new_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Account already exists",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(
            minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        if user.is_superuser:
            permissions = "admin"
        else:
            permissions = "user"
        access_token = security.create_access_token(
            data={"sub": user.email, "permissions": permissions},
            expires_delta=access_token_expires,
        )

        return {"access_token": access_token, "token_type": "bearer"}

    # fastapi recommendation
    except HTTPException as e:
        logger.error(f'ERR:{myself()}: Invalid signup {e}')
        raise HTTPException(status_code=400, detail="Invalid signup.")

    except Exception as e:
        logger.error(f'ERR:{myself()}: {e}')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Invalid to signup.')


@r.post("/logout")
async def logout(db=Depends(get_db), token: str = Depends(security.oauth2_scheme), current_user=Depends(get_current_active_user)):
    try:
        return blacklist_token(db, token)

    except Exception as e:
        logger.error(f'ERR:{myself()}: {e}')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Invalid token request.')

