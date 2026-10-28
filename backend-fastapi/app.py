from dotenv import load_dotenv

load_dotenv()
import os, re, json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from errors import ApiError
from users import find_public, verify_credentials
from auth import issue_token, current_user_id, assert_owner
import store

app = FastAPI(title="JWT 게시판 시작 코드")


@app.exception_handler(ApiError)
async def handle_error(request, exc):
    return JSONResponse(
        status_code=exc.status,
        content=dict(code=exc.code, message=exc.message),
        headers={"WWW-Authenticate": "Bearer"} if exc.status == 401 else None,
    )


async def fields(request, limits):
    try:
        body = await request.json()
    except (ValueError, UnicodeError):
        raise ApiError(400, "BAD_INPUT", "올바른 JSON을 보내세요.")
    if not isinstance(body, dict) or set(body) - set(limits):
        raise ApiError(400, "BAD_INPUT", "허용된 JSON 필드만 보내세요.")
    result = {}
    for key, limit in limits.items():
        value = body.get(key)
        if (
            not isinstance(value, str)
            or not value.strip()
            or len(value.strip()) > limit
        ):
            raise ApiError(400, "BAD_INPUT", f"{key} 입력을 확인하세요.")
        result[key] = value if key == "password" else value.strip()
    return result


def post_id(value):
    if not re.fullmatch(r"[1-9][0-9]*", value) or int(value) > 9007199254740991:
        raise ApiError(400, "BAD_INPUT", "ID는 양의 정수여야 합니다.")
    return int(value)


def existing(value):
    post = store.get_post(value)
    if not post:
        raise ApiError(404, "NOT_FOUND", "게시글이 없습니다.")
    return post


@app.get("/api/health")
def health():
    return dict(status="ok", stack="fastapi")


@app.post("/api/auth/login")
async def login(request: Request):
    data = await fields(request, dict(email=254, password=128))
    user = verify_credentials(**data)
    if not user:
        raise ApiError(401, "INVALID_CREDENTIALS", "이메일 또는 비밀번호를 확인하세요.")
    return dict(
        accessToken=issue_token(user),
        expiresIn=int(os.getenv("TOKEN_TTL", "90")),
        user=user,
    )


@app.get("/api/me")
def me(request: Request):
    user = find_public(current_user_id(request))
    if not user:
        raise ApiError(401, "INVALID_TOKEN", "사용자를 확인할 수 없습니다.")
    return user


@app.get("/api/posts")
def list_posts():
    return store.list_posts()


@app.get("/api/posts/{id}")
def get_post(id: str):
    return existing(post_id(id))


@app.post("/api/posts", status_code=201)
async def create(request: Request):
    user_id = current_user_id(request)
    data = await fields(request, dict(title=100, content=5000))
    post = store.create_post(data, user_id)
    return JSONResponse(
        status_code=201, content=post, headers={"Location": f"/api/posts/{post['id']}"}
    )


@app.put("/api/posts/{id}")
async def update(id: str, request: Request):
    user_id = current_user_id(request)
    pid = post_id(id)
    post = existing(pid)
    assert_owner(user_id, post["authorId"])
    return store.update_post(pid, await fields(request, dict(title=100, content=5000)))


@app.delete("/api/posts/{id}", status_code=204)
def delete(id: str, request: Request):
    user_id = current_user_id(request)
    pid = post_id(id)
    post = existing(pid)
    assert_owner(user_id, post["authorId"])
    store.delete_post(pid)
    return Response(status_code=204)
