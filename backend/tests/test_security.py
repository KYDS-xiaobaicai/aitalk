import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.utils.security import get_password_hash, verify_password, create_access_token, decode_access_token
from datetime import timedelta

# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_security.db"
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


class TestPasswordSecurity:
    """密码安全测试"""
    
    def test_password_hashing(self):
        """测试密码哈希"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # 哈希值不应该等于原密码
        assert hashed != password
        
        # 哈希值应该是字符串
        assert isinstance(hashed, str)
        
        # 哈希值长度应该合理（bcrypt通常是60个字符）
        assert len(hashed) > 50
    
    def test_password_verification(self):
        """测试密码验证"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # 正确密码应该验证成功
        assert verify_password(password, hashed) is True
        
        # 错误密码应该验证失败
        assert verify_password("wrongpassword", hashed) is False
        assert verify_password("", hashed) is False
    
    def test_different_passwords_different_hashes(self):
        """测试不同密码产生不同哈希值"""
        password1 = "password123"
        password2 = "password456"
        
        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)
        
        assert hash1 != hash2
    
    def test_same_password_different_hashes(self):
        """测试相同密码产生不同哈希值（盐值不同）"""
        password = "samepassword"
        
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # bcrypt每次都会生成不同的值，所以哈希值应该不同
        assert hash1 != hash2
        
        # 但都应该能验证成功
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTSecurity:
    """JWT安全测试"""
    
    def test_create_access_token(self):
        """测试创建访问令牌"""
        data = {"sub": 123, "username": "testuser"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert "." in token  # JWT应该包含点分隔符
    
    def test_decode_access_token(self):
        """测试解码访问令牌"""
        data = {"sub": 123, "username": "testuser"}
        token = create_access_token(data)
        
        decoded = decode_access_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == 123
        assert decoded["username"] == "testuser"
        assert "exp" in decoded  # 应该包含过期时间
    
    def test_decode_invalid_token(self):
        """测试解码无效令牌"""
        invalid_tokens = [
            "invalid.token.here",
            "not.a.jwt",
            "",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
        ]
        
        for token in invalid_tokens:
            decoded = decode_access_token(token)
            assert decoded is None
    
    def test_token_expiration(self):
        """测试令牌过期"""
        data = {"sub": 123, "username": "testuser"}
        
        # 创建一个立即过期的令牌
        expired_token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        
        # 解码应该失败
        decoded = decode_access_token(expired_token)
        assert decoded is None
    
    def test_token_with_custom_expiration(self):
        """测试自定义过期时间的令牌"""
        data = {"sub": 123, "username": "testuser"}
        
        # 创建一个1小时后过期的令牌
        token = create_access_token(data, expires_delta=timedelta(hours=1))
        
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == 123


class TestInputValidation:
    """输入验证测试"""
    
    def test_register_input_validation(self):
        """测试注册输入验证"""
        # 测试各种无效输入
        invalid_inputs = [
            # 用户名太短
            {
                "username": "ab",
                "email": "test@example.com",
                "password": "password123"
            },
            # 用户名太长
            {
                "username": "a" * 51,
                "email": "test@example.com",
                "password": "password123"
            },
            # 密码太短
            {
                "username": "testuser",
                "email": "test@example.com",
                "password": "12345"
            },
            # 无效邮箱
            {
                "username": "testuser",
                "email": "invalid-email",
                "password": "password123"
            },
            # 缺少字段
            {
                "username": "testuser",
                "password": "password123"
            },
            # 空字符串
            {
                "username": "",
                "email": "test@example.com",
                "password": "password123"
            }
        ]
        
        for invalid_input in invalid_inputs:
            response = client.post("/api/auth/register", json=invalid_input)
            assert response.status_code == 422  # 验证错误
    
    def test_conversation_title_validation(self):
        """测试对话标题验证"""
        # 先注册并登录用户
        client.post("/api/auth/register", json={
            "username": "titleuser",
            "email": "title@example.com",
            "password": "password123"
        })
        
        login_response = client.post("/api/auth/login", data={
            "username": "titleuser",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 测试标题太长
        long_title = "a" * 201  # 超过200字符限制
        response = client.post("/api/conversations", json={
            "title": long_title
        }, headers=headers)
        assert response.status_code == 422
    
    def test_message_content_validation(self):
        """测试消息内容验证"""
        # 先注册并登录用户
        client.post("/api/auth/register", json={
            "username": "msguser",
            "email": "msg@example.com",
            "password": "password123"
        })
        
        login_response = client.post("/api/auth/login", data={
            "username": "msguser",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 创建对话
        conv_response = client.post("/api/conversations", json={
            "title": "测试对话"
        }, headers=headers)
        conversation_id = conv_response.json()["id"]
        
        # 测试空消息
        response = client.post(f"/api/conversations/{conversation_id}/messages", json={
            "content": ""
        }, headers=headers)
        assert response.status_code == 422


class TestAccessControl:
    """访问控制测试"""
    
    def test_unauthorized_access(self):
        """测试未授权访问"""
        # 不提供认证头的请求应该被拒绝
        endpoints = [
            ("GET", "/api/conversations"),
            ("POST", "/api/conversations"),
            ("GET", "/api/conversations/1"),
            ("PUT", "/api/conversations/1"),
            ("DELETE", "/api/conversations/1"),
            ("GET", "/api/conversations/1/messages"),
            ("POST", "/api/conversations/1/messages")
        ]
        
        for method, endpoint in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            elif method == "PUT":
                response = client.put(endpoint, json={})
            elif method == "DELETE":
                response = client.delete(endpoint)
            
            assert response.status_code == 401
    
    def test_invalid_token_access(self):
        """测试无效令牌访问"""
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get("/api/conversations", headers=invalid_headers)
        assert response.status_code == 401
    
    def test_cross_user_access_prevention(self):
        """测试跨用户访问防护"""
        # 创建两个用户
        client.post("/api/auth/register", json={
            "username": "user1",
            "email": "user1@example.com",
            "password": "password123"
        })
        
        client.post("/api/auth/register", json={
            "username": "user2",
            "email": "user2@example.com",
            "password": "password123"
        })
        
        # 用户1登录并创建对话
        login1 = client.post("/api/auth/login", data={
            "username": "user1",
            "password": "password123"
        })
        token1 = login1.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}
        
        conv_response = client.post("/api/conversations", json={
            "title": "用户1的对话"
        }, headers=headers1)
        conversation_id = conv_response.json()["id"]
        
        # 用户2登录并尝试访问用户1的对话
        login2 = client.post("/api/auth/login", data={
            "username": "user2",
            "password": "password123"
        })
        token2 = login2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # 用户2不应该能访问用户1的对话
        response = client.get(f"/api/conversations/{conversation_id}", headers=headers2)
        assert response.status_code == 404  # 返回404而不是403，避免信息泄露
        
        # 用户2不应该能修改用户1的对话
        response = client.put(f"/api/conversations/{conversation_id}", json={
            "title": "恶意修改"
        }, headers=headers2)
        assert response.status_code == 404
        
        # 用户2不应该能删除用户1的对话
        response = client.delete(f"/api/conversations/{conversation_id}", headers=headers2)
        assert response.status_code == 404


class TestSQLInjectionPrevention:
    """SQL注入防护测试"""
    
    def test_sql_injection_in_login(self):
        """测试登录中的SQL注入防护"""
        # 先注册一个正常用户
        client.post("/api/auth/register", json={
            "username": "normaluser",
            "email": "normal@example.com",
            "password": "password123"
        })
        
        # 尝试SQL注入攻击
        sql_injection_attempts = [
            "normaluser'; DROP TABLE users; --",
            "normaluser' OR '1'='1",
            "normaluser' UNION SELECT * FROM users --",
            "'; DELETE FROM users WHERE '1'='1",
        ]
        
        for malicious_username in sql_injection_attempts:
            response = client.post("/api/auth/login", data={
                "username": malicious_username,
                "password": "password123"
            })
            # 应该返回401而不是500（服务器错误）
            assert response.status_code == 401
    
    def test_sql_injection_in_conversation_search(self):
        """测试对话搜索中的SQL注入防护"""
        # 注册并登录用户
        client.post("/api/auth/register", json={
            "username": "searchuser",
            "email": "search@example.com",
            "password": "password123"
        })
        
        login_response = client.post("/api/auth/login", data={
            "username": "searchuser",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 尝试通过对话ID进行SQL注入
        malicious_ids = [
            "1; DROP TABLE conversations; --",
            "1 OR 1=1",
            "1 UNION SELECT * FROM users",
        ]
        
        for malicious_id in malicious_ids:
            response = client.get(f"/api/conversations/{malicious_id}", headers=headers)
            # 应该返回404或422，而不是500
            assert response.status_code in [404, 422]


class TestXSSPrevention:
    """XSS防护测试"""
    
    def test_xss_in_conversation_title(self):
        """测试对话标题中的XSS防护"""
        # 注册并登录用户
        client.post("/api/auth/register", json={
            "username": "xssuser",
            "email": "xss@example.com",
            "password": "password123"
        })
        
        login_response = client.post("/api/auth/login", data={
            "username": "xssuser",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 尝试XSS攻击
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert('XSS');//",
        ]
        
        for payload in xss_payloads:
            response = client.post("/api/conversations", json={
                "title": payload
            }, headers=headers)
            
            if response.status_code == 201:
                # 检查返回的数据是否包含原始payload
                data = response.json()
                # 由于我们使用JSON API，XSS payload应该被原样存储和返回
                # 前端负责适当的转义
                assert data["title"] == payload
    
    def test_xss_in_message_content(self):
        """测试消息内容中的XSS防护"""
        # 注册并登录用户
        client.post("/api/auth/register", json={
            "username": "msgxssuser",
            "email": "msgxss@example.com",
            "password": "password123"
        })
        
        login_response = client.post("/api/auth/login", data={
            "username": "msgxssuser",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 创建对话
        conv_response = client.post("/api/conversations", json={
            "title": "XSS测试对话"
        }, headers=headers)
        conversation_id = conv_response.json()["id"]
        
        # 尝试在消息中进行XSS攻击
        xss_payload = "<script>alert('XSS in message')</script>"
        
        response = client.post(f"/api/conversations/{conversation_id}/messages", json={
            "content": xss_payload
        }, headers=headers)
        
        if response.status_code == 201:
            data = response.json()
            # 用户消息应该包含原始payload
            user_message = data[0]
            assert user_message["content"] == xss_payload


class TestRateLimiting:
    """速率限制测试（概念性测试）"""
    
    def test_multiple_login_attempts(self):
        """测试多次登录尝试"""
        # 注册用户
        client.post("/api/auth/register", json={
            "username": "ratelimituser",
            "email": "ratelimit@example.com",
            "password": "password123"
        })
        
        # 多次错误登录尝试
        failed_attempts = 0
        for i in range(10):
            response = client.post("/api/auth/login", data={
                "username": "ratelimituser",
                "password": "wrongpassword"
            })
            if response.status_code == 401:
                failed_attempts += 1
        
        # 所有尝试都应该失败
        assert failed_attempts == 10
        
        # 正确密码应该仍然能登录（因为我们没有实现真正的速率限制）
        response = client.post("/api/auth/login", data={
            "username": "ratelimituser",
            "password": "password123"
        })
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__]) 