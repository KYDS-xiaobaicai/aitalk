import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


# 测试辅助函数
def create_test_user(username="testuser", email="test@example.com", password="testpassword"):
    """创建测试用户"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password
        }
    )
    return response


def login_test_user(username="testuser", password="testpassword"):
    """登录测试用户并返回token"""
    response = client.post(
        "/api/auth/login",
        data={
            "username": username,
            "password": password
        }
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


def get_auth_headers(token):
    """获取认证头"""
    return {"Authorization": f"Bearer {token}"}


# 基础功能测试
def test_root():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check():
    """测试健康检查"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


# 用户认证测试
def test_register_user():
    """测试用户注册"""
    response = create_test_user("newuser", "new@example.com")
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert "id" in data
    assert data["is_active"] is True


def test_register_duplicate_username():
    """测试注册重复用户名"""
    # 先注册一个用户
    create_test_user("duplicate", "first@example.com")
    
    # 尝试注册相同用户名
    response = create_test_user("duplicate", "second@example.com")
    assert response.status_code == 400
    assert "用户名已存在" in response.json()["detail"]


def test_register_duplicate_email():
    """测试注册重复邮箱"""
    # 先注册一个用户
    create_test_user("user1", "same@example.com")
    
    # 尝试注册相同邮箱
    response = create_test_user("user2", "same@example.com")
    assert response.status_code == 400
    assert "邮箱已被注册" in response.json()["detail"]


def test_register_invalid_data():
    """测试注册无效数据"""
    # 用户名太短
    response = client.post(
        "/api/auth/register",
        json={
            "username": "ab",  # 少于3个字符
            "email": "test@example.com",
            "password": "testpassword"
        }
    )
    assert response.status_code == 422
    
    # 密码太短
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "12345"  # 少于6个字符
        }
    )
    assert response.status_code == 422
    
    # 无效邮箱
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "invalid-email",
            "password": "testpassword"
        }
    )
    assert response.status_code == 422


def test_login_user():
    """测试用户登录"""
    # 先注册用户
    create_test_user("logintest", "login@example.com")
    
    # 登录
    response = client.post(
        "/api/auth/login",
        data={
            "username": "logintest",
            "password": "testpassword"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials():
    """测试无效登录凭据"""
    # 先注册用户
    create_test_user("validuser", "valid@example.com")
    
    # 错误密码
    response = client.post(
        "/api/auth/login",
        data={
            "username": "validuser",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert "用户名或密码错误" in response.json()["detail"]
    
    # 不存在的用户
    response = client.post(
        "/api/auth/login",
        data={
            "username": "nonexistent",
            "password": "testpassword"
        }
    )
    assert response.status_code == 401
    assert "用户名或密码错误" in response.json()["detail"]


# 对话管理测试
def test_create_conversation():
    """测试创建对话"""
    # 创建用户并登录
    create_test_user("convuser", "conv@example.com")
    token = login_test_user("convuser")
    headers = get_auth_headers(token)
    
    # 创建对话
    response = client.post(
        "/api/conversations",
        json={"title": "测试对话"},
        headers=headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "测试对话"
    assert "id" in data
    assert "created_at" in data


def test_create_conversation_default_title():
    """测试创建对话使用默认标题"""
    # 创建用户并登录
    create_test_user("defaultuser", "default@example.com")
    token = login_test_user("defaultuser")
    headers = get_auth_headers(token)
    
    # 创建对话（不指定标题）
    response = client.post(
        "/api/conversations",
        json={},
        headers=headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "新对话"


def test_get_conversations():
    """测试获取对话列表"""
    # 创建用户并登录
    create_test_user("listuser", "list@example.com")
    token = login_test_user("listuser")
    headers = get_auth_headers(token)
    
    # 创建几个对话
    client.post("/api/conversations", json={"title": "对话1"}, headers=headers)
    client.post("/api/conversations", json={"title": "对话2"}, headers=headers)
    
    # 获取对话列表
    response = client.get("/api/conversations", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] in ["对话1", "对话2"]


def test_get_conversation_by_id():
    """测试根据ID获取对话"""
    # 创建用户并登录
    create_test_user("getuser", "get@example.com")
    token = login_test_user("getuser")
    headers = get_auth_headers(token)
    
    # 创建对话
    create_response = client.post(
        "/api/conversations",
        json={"title": "特定对话"},
        headers=headers
    )
    conversation_id = create_response.json()["id"]
    
    # 获取特定对话
    response = client.get(f"/api/conversations/{conversation_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "特定对话"
    assert data["id"] == conversation_id


def test_update_conversation():
    """测试更新对话标题"""
    # 创建用户并登录
    create_test_user("updateuser", "update@example.com")
    token = login_test_user("updateuser")
    headers = get_auth_headers(token)
    
    # 创建对话
    create_response = client.post(
        "/api/conversations",
        json={"title": "原标题"},
        headers=headers
    )
    conversation_id = create_response.json()["id"]
    
    # 更新对话标题
    response = client.put(
        f"/api/conversations/{conversation_id}",
        json={"title": "新标题"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "新标题"


def test_delete_conversation():
    """测试删除对话"""
    # 创建用户并登录
    create_test_user("deleteuser", "delete@example.com")
    token = login_test_user("deleteuser")
    headers = get_auth_headers(token)
    
    # 创建对话
    create_response = client.post(
        "/api/conversations",
        json={"title": "待删除对话"},
        headers=headers
    )
    conversation_id = create_response.json()["id"]
    
    # 删除对话
    response = client.delete(f"/api/conversations/{conversation_id}", headers=headers)
    assert response.status_code == 204
    
    # 验证对话已删除
    response = client.get(f"/api/conversations/{conversation_id}", headers=headers)
    assert response.status_code == 404


def test_conversation_access_control():
    """测试对话访问控制"""
    # 创建两个用户
    create_test_user("user1", "user1@example.com")
    create_test_user("user2", "user2@example.com")
    
    token1 = login_test_user("user1")
    token2 = login_test_user("user2")
    
    headers1 = get_auth_headers(token1)
    headers2 = get_auth_headers(token2)
    
    # 用户1创建对话
    create_response = client.post(
        "/api/conversations",
        json={"title": "用户1的对话"},
        headers=headers1
    )
    conversation_id = create_response.json()["id"]
    
    # 用户2尝试访问用户1的对话
    response = client.get(f"/api/conversations/{conversation_id}", headers=headers2)
    assert response.status_code == 404  # 应该返回404，因为用户2无权访问


# 消息交互测试
def test_send_message():
    """测试发送消息"""
    # 创建用户并登录
    create_test_user("msguser", "msg@example.com")
    token = login_test_user("msguser")
    headers = get_auth_headers(token)
    
    # 创建对话
    create_response = client.post(
        "/api/conversations",
        json={"title": "消息测试对话"},
        headers=headers
    )
    conversation_id = create_response.json()["id"]
    
    # 发送消息
    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"content": "你好，这是测试消息"},
        headers=headers
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 2  # 用户消息 + AI回复
    assert data[0]["role"] == "user"
    assert data[0]["content"] == "你好，这是测试消息"
    assert data[1]["role"] == "assistant"


def test_get_messages():
    """测试获取消息列表"""
    # 创建用户并登录
    create_test_user("getmsguser", "getmsg@example.com")
    token = login_test_user("getmsguser")
    headers = get_auth_headers(token)
    
    # 创建对话
    create_response = client.post(
        "/api/conversations",
        json={"title": "获取消息测试"},
        headers=headers
    )
    conversation_id = create_response.json()["id"]
    
    # 发送消息
    client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"content": "第一条消息"},
        headers=headers
    )
    
    # 获取消息列表
    response = client.get(f"/api/conversations/{conversation_id}/messages", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # 至少有用户消息和AI回复


def test_message_access_control():
    """测试消息访问控制"""
    # 创建两个用户
    create_test_user("msguser1", "msguser1@example.com")
    create_test_user("msguser2", "msguser2@example.com")
    
    token1 = login_test_user("msguser1")
    token2 = login_test_user("msguser2")
    
    headers1 = get_auth_headers(token1)
    headers2 = get_auth_headers(token2)
    
    # 用户1创建对话并发送消息
    create_response = client.post(
        "/api/conversations",
        json={"title": "用户1的对话"},
        headers=headers1
    )
    conversation_id = create_response.json()["id"]
    
    client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"content": "私密消息"},
        headers=headers1
    )
    
    # 用户2尝试访问用户1的消息
    response = client.get(f"/api/conversations/{conversation_id}/messages", headers=headers2)
    assert response.status_code == 404  # 应该返回404，因为用户2无权访问


def test_conversation_title_auto_update():
    """测试对话标题自动更新"""
    # 创建用户并登录
    create_test_user("titleuser", "title@example.com")
    token = login_test_user("titleuser")
    headers = get_auth_headers(token)
    
    # 创建对话（使用默认标题）
    create_response = client.post(
        "/api/conversations",
        json={},
        headers=headers
    )
    conversation_id = create_response.json()["id"]
    
    # 发送第一条消息
    long_message = "这是一条很长的消息，用来测试对话标题是否会自动更新为消息的前50个字符"
    client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"content": long_message},
        headers=headers
    )
    
    # 检查对话标题是否更新
    response = client.get(f"/api/conversations/{conversation_id}", headers=headers)
    data = response.json()
    assert data["title"] == long_message[:50] + "..."


def test_invalid_message_content():
    """测试无效消息内容"""
    # 创建用户并登录
    create_test_user("invaliduser", "invalid@example.com")
    token = login_test_user("invaliduser")
    headers = get_auth_headers(token)
    
    # 创建对话
    create_response = client.post(
        "/api/conversations",
        json={"title": "无效消息测试"},
        headers=headers
    )
    conversation_id = create_response.json()["id"]
    
    # 发送空消息
    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"content": ""},
        headers=headers
    )
    assert response.status_code == 422  # 验证失败


def test_unauthorized_access():
    """测试未授权访问"""
    # 不提供认证头
    response = client.get("/api/conversations")
    assert response.status_code == 401
    
    response = client.post("/api/conversations", json={"title": "测试"})
    assert response.status_code == 401
    
    # 无效token
    invalid_headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/conversations", headers=invalid_headers)
    assert response.status_code == 401


def test_pagination():
    """测试分页功能"""
    # 创建用户并登录
    create_test_user("pageuser", "page@example.com")
    token = login_test_user("pageuser")
    headers = get_auth_headers(token)
    
    # 创建多个对话
    for i in range(5):
        client.post(
            "/api/conversations",
            json={"title": f"对话{i}"},
            headers=headers
        )
    
    # 测试分页
    response = client.get("/api/conversations?skip=0&limit=3", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    
    response = client.get("/api/conversations?skip=3&limit=3", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # 剩余2个


if __name__ == "__main__":
    pytest.main([__file__]) 