import os
import re
import time

import jwt

from errors import ApiError
from users import find_public



secret = os.getenv("JWT_SECRET", "")

if not re.fullmatch(r"[0-9a-fA-F]{64}", secret):
    raise RuntimeError("JWT_SECRET은 64자리 16진수여야 합니다.")

SECRET_KEY = bytes.fromhex(secret)

TOKEN_TTL = int(os.getenv("TOKEN_TTL", "90"))


# PyJWT는 requirements.txt에 포함되어 있습니다. 아래 함수를 완성하세요.
def issue_token(user):
    #TODO BE-01: 서버 환경변수 키로 HS256 JWT 발급. sub, exp, iss, aud 필수.
    payload = {
        "sub": str(user["id"]),
        "exp": int(time.time()) + TOKEN_TTL,
        "iss": os.getenv("JWT_ISSUER", "webservice-class"),
        "aud": os.getenv("JWT_AUDIENCE", "board-api"),

    }

    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def current_user_id(request):
    # TODO BE-02: Bearer 추출 → 서명/알고리즘/만료/클레임 검증 → 실제 사용자 확인.
    # 완성 후 데모 ID 반환을 제거하세요. 토큰 없음/변조/만료는 401입니다.
    header = request.headers.get("Authorization", "")
    parts = header.split()

    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise ApiError(401, "TOKEN_REQUIRED", "Bearer 토큰이 필요합니다.")

    try:
        payload = jwt.decode(
            parts[1],
            SECRET_KEY,
            algorithms=["HS256"],
            issuer=os.getenv("JWT_ISSUER", "webservice-class"),
            audience=os.getenv("JWT_AUDIENCE", "board-api"),
            options={
                "require": ["sub", "exp", "iss", "aud"],
                "verify_exp": False,
            },
        )

        subject = payload["sub"]
        if not isinstance(subject, str) or not re.fullmatch(
            r"[1-9][0-9]*", subject
        ):
            raise ValueError("잘못된 사용자 ID")

        # 이 서비스는 만료 시각을 정수 Unix 초로 사용합니다.
        if type(payload["exp"]) is not int:
            raise ValueError("잘못된 만료 시각")

        user_id = int(subject)
        if not find_public(user_id):
            raise ValueError("없는 사용자")

    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise ApiError(
            401, "INVALID_TOKEN", "유효하지 않은 토큰입니다."
        ) from None

    if payload["exp"] <= time.time():
        raise ApiError(
            401, "TOKEN_EXPIRED", "로그인이 만료되었습니다."
        )

    return user_id


def assert_owner(user_id, author_id):   
    # TODO BE-03: 다른 작성자이면 403 FORBIDDEN. 현재는 검사하지 않습니다.
    if user_id != author_id:
        raise ApiError(
            403,
            "FORBIDDEN",
            "본인이 작성한 글만 수정하거나 삭제할 수 있습니다.",
        )
   
