// TODO FE-01~04: 공통 API 명세와 구현 체크리스트를 보고 완성하세요.
let session = { accessToken: "", user: null };
export const getSession = () => session;
export function clearSession() {
  session = { accessToken: "", user: null };
}
function authorizationHeaders() {
  // TODO FE-02: 메모리에 보관한 토큰을 Bearer 헤더로 보내세요.
  if (!session.accessToken) {
    return {};
  }

  return {
    Authorization: `Bearer ${session.accessToken}`,
  };
}
export async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authorizationHeaders(),
      ...options.headers,
    },
  });
  const data = response.status === 204 ? null : await response.json();
  if (!response.ok) {
    // TODO FE-03: 401이면 메모리의 로그인 상태도 해제하세요.
    if (response.status === 401) {
    clearSession();
  }
    const error = new Error(
      data.message || data.code || `HTTP ${response.status}`,
    );
    error.status = response.status;
    error.code = data.code;
    throw error;
  }
  return data;
}
export async function login(email, password) {
  // TODO FE-01: POST /auth/login → 응답의 토큰과 사용자 정보를 session에 저장.
  // request()를 이용할 수 있습니다. 성공하면 user를 반환하세요.
  const data = await request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

  session = {
    accessToken: data.accessToken,
    user: data.user,
  };

  return session.user;
}
export function canEdit(post) {
  // TODO FE-04: 로그인 사용자와 작성자를 비교하세요. 서버 검사도 반드시 필요합니다.
  return session.user !== null && session.user.id === post.authorId; // 시작 코드에서는 CRUD를 체험할 수 있도록 모두 표시합니다.
}
export const api = {
  list: () => request("/posts"),
  detail: (id) => request(`/posts/${id}`),
  create: (input) =>
    request("/posts", { method: "POST", body: JSON.stringify(input) }),
  update: (id, input) =>
    request(`/posts/${id}`, { method: "PUT", body: JSON.stringify(input) }),
  remove: (id) => request(`/posts/${id}`, { method: "DELETE" }),
  me: () => request("/me"),
};
