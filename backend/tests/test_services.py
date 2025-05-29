import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from app.database import Base
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.schemas.user import UserCreate
from app.schemas.conversation import ConversationCreate, ConversationUpdate
from app.schemas.message import MessageCreate
from app.services.auth import AuthService
from app.services.conversation import ConversationService
from app.utils.security import verify_password

# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_services.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


@pytest.fixture
def db_session():
    """创建数据库会话"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpassword"
    )
    user = AuthService.register_user(db_session, user_data)
    return user


@pytest.fixture
def test_conversation(db_session, test_user):
    """创建测试对话"""
    conversation_data = ConversationCreate(title="测试对话")
    conversation = ConversationService.create_conversation(
        db_session, test_user, conversation_data
    )
    return conversation


class TestAuthService:
    """认证服务测试"""
    
    def test_register_user_success(self, db_session):
        """测试成功注册用户"""
        user_data = UserCreate(
            username="newuser",
            email="new@example.com",
            password="password123"
        )
        
        user = AuthService.register_user(db_session, user_data)
        
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.is_active is True
        assert verify_password("password123", user.hashed_password)
    
    def test_register_duplicate_username(self, db_session):
        """测试注册重复用户名"""
        user_data1 = UserCreate(
            username="duplicate",
            email="first@example.com",
            password="password123"
        )
        user_data2 = UserCreate(
            username="duplicate",
            email="second@example.com",
            password="password123"
        )
        
        AuthService.register_user(db_session, user_data1)
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.register_user(db_session, user_data2)
        
        assert exc_info.value.status_code == 400
        assert "用户名已存在" in str(exc_info.value.detail)
    
    def test_register_duplicate_email(self, db_session):
        """测试注册重复邮箱"""
        user_data1 = UserCreate(
            username="user1",
            email="same@example.com",
            password="password123"
        )
        user_data2 = UserCreate(
            username="user2",
            email="same@example.com",
            password="password123"
        )
        
        AuthService.register_user(db_session, user_data1)
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.register_user(db_session, user_data2)
        
        assert exc_info.value.status_code == 400
        assert "邮箱已被注册" in str(exc_info.value.detail)
    
    def test_authenticate_user_success(self, db_session):
        """测试成功认证用户"""
        user_data = UserCreate(
            username="authuser",
            email="auth@example.com",
            password="password123"
        )
        AuthService.register_user(db_session, user_data)
        
        user = AuthService.authenticate_user(db_session, "authuser", "password123")
        
        assert user.username == "authuser"
        assert user.email == "auth@example.com"
    
    def test_authenticate_user_wrong_password(self, db_session):
        """测试错误密码认证"""
        user_data = UserCreate(
            username="authuser2",
            email="auth2@example.com",
            password="password123"
        )
        AuthService.register_user(db_session, user_data)
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.authenticate_user(db_session, "authuser2", "wrongpassword")
        
        assert exc_info.value.status_code == 401
        assert "用户名或密码错误" in str(exc_info.value.detail)
    
    def test_authenticate_nonexistent_user(self, db_session):
        """测试认证不存在的用户"""
        with pytest.raises(HTTPException) as exc_info:
            AuthService.authenticate_user(db_session, "nonexistent", "password123")
        
        assert exc_info.value.status_code == 401
        assert "用户名或密码错误" in str(exc_info.value.detail)
    
    def test_create_token(self, test_user):
        """测试创建访问令牌"""
        token = AuthService.create_token(test_user)
        
        assert isinstance(token, str)
        assert len(token) > 0


class TestConversationService:
    """对话服务测试"""
    
    def test_create_conversation(self, db_session, test_user):
        """测试创建对话"""
        conversation_data = ConversationCreate(title="新对话")
        conversation = ConversationService.create_conversation(
            db_session, test_user, conversation_data
        )
        
        assert conversation.title == "新对话"
        assert conversation.user_id == test_user.id
        assert conversation.id is not None
    
    def test_create_conversation_default_title(self, db_session, test_user):
        """测试创建对话使用默认标题"""
        conversation_data = ConversationCreate()
        conversation = ConversationService.create_conversation(
            db_session, test_user, conversation_data
        )
        
        assert conversation.title == "新对话"
        assert conversation.user_id == test_user.id
    
    def test_get_user_conversations(self, db_session, test_user):
        """测试获取用户对话列表"""
        # 创建多个对话
        for i in range(3):
            conversation_data = ConversationCreate(title=f"对话{i}")
            ConversationService.create_conversation(
                db_session, test_user, conversation_data
            )
        
        conversations = ConversationService.get_user_conversations(
            db_session, test_user
        )
        
        assert len(conversations) == 3
        assert all(conv.user_id == test_user.id for conv in conversations)
    
    def test_get_user_conversations_pagination(self, db_session, test_user):
        """测试对话列表分页"""
        # 创建5个对话
        for i in range(5):
            conversation_data = ConversationCreate(title=f"对话{i}")
            ConversationService.create_conversation(
                db_session, test_user, conversation_data
            )
        
        # 测试分页
        conversations_page1 = ConversationService.get_user_conversations(
            db_session, test_user, skip=0, limit=3
        )
        conversations_page2 = ConversationService.get_user_conversations(
            db_session, test_user, skip=3, limit=3
        )
        
        assert len(conversations_page1) == 3
        assert len(conversations_page2) == 2
    
    def test_get_conversation_success(self, db_session, test_user, test_conversation):
        """测试成功获取对话"""
        conversation = ConversationService.get_conversation(
            db_session, test_user, test_conversation.id
        )
        
        assert conversation.id == test_conversation.id
        assert conversation.title == test_conversation.title
    
    def test_get_conversation_not_found(self, db_session, test_user):
        """测试获取不存在的对话"""
        with pytest.raises(HTTPException) as exc_info:
            ConversationService.get_conversation(db_session, test_user, 999)
        
        assert exc_info.value.status_code == 404
        assert "对话不存在" in str(exc_info.value.detail)
    
    def test_get_conversation_access_denied(self, db_session, test_conversation):
        """测试访问其他用户的对话"""
        # 创建另一个用户
        other_user_data = UserCreate(
            username="otheruser",
            email="other@example.com",
            password="password123"
        )
        other_user = AuthService.register_user(db_session, other_user_data)
        
        with pytest.raises(HTTPException) as exc_info:
            ConversationService.get_conversation(
                db_session, other_user, test_conversation.id
            )
        
        assert exc_info.value.status_code == 404
    
    def test_update_conversation(self, db_session, test_user, test_conversation):
        """测试更新对话标题"""
        update_data = ConversationUpdate(title="更新后的标题")
        updated_conversation = ConversationService.update_conversation(
            db_session, test_user, test_conversation.id, update_data
        )
        
        assert updated_conversation.title == "更新后的标题"
        assert updated_conversation.id == test_conversation.id
    
    def test_delete_conversation(self, db_session, test_user, test_conversation):
        """测试删除对话"""
        conversation_id = test_conversation.id
        
        ConversationService.delete_conversation(
            db_session, test_user, conversation_id
        )
        
        # 验证对话已删除
        with pytest.raises(HTTPException):
            ConversationService.get_conversation(
                db_session, test_user, conversation_id
            )
    
    def test_send_message(self, db_session, test_user, test_conversation):
        """测试发送消息"""
        message_data = MessageCreate(content="测试消息")
        
        # 使用异步函数需要特殊处理
        import asyncio
        
        async def test_async():
            user_message, ai_message = await ConversationService.send_message(
                db_session, test_user, test_conversation.id, message_data
            )
            
            assert user_message.content == "测试消息"
            assert user_message.role == MessageRole.USER
            assert user_message.conversation_id == test_conversation.id
            
            assert ai_message.role == MessageRole.ASSISTANT
            assert ai_message.conversation_id == test_conversation.id
            assert len(ai_message.content) > 0
            
            return user_message, ai_message
        
        # 运行异步测试
        user_message, ai_message = asyncio.run(test_async())
        
        # 验证消息已保存到数据库
        messages = db_session.query(Message).filter(
            Message.conversation_id == test_conversation.id
        ).all()
        assert len(messages) == 2
    
    def test_get_conversation_messages(self, db_session, test_user, test_conversation):
        """测试获取对话消息"""
        # 先添加一些消息
        message1 = Message(
            conversation_id=test_conversation.id,
            role=MessageRole.USER,
            content="第一条消息"
        )
        message2 = Message(
            conversation_id=test_conversation.id,
            role=MessageRole.ASSISTANT,
            content="AI回复"
        )
        
        db_session.add(message1)
        db_session.add(message2)
        db_session.commit()
        
        messages = ConversationService.get_conversation_messages(
            db_session, test_user, test_conversation.id
        )
        
        assert len(messages) == 2
        assert messages[0].content == "第一条消息"
        assert messages[1].content == "AI回复"
    
    def test_get_conversation_messages_pagination(self, db_session, test_user, test_conversation):
        """测试消息列表分页"""
        # 添加多条消息
        for i in range(5):
            message = Message(
                conversation_id=test_conversation.id,
                role=MessageRole.USER,
                content=f"消息{i}"
            )
            db_session.add(message)
        db_session.commit()
        
        # 测试分页
        messages_page1 = ConversationService.get_conversation_messages(
            db_session, test_user, test_conversation.id, skip=0, limit=3
        )
        messages_page2 = ConversationService.get_conversation_messages(
            db_session, test_user, test_conversation.id, skip=3, limit=3
        )
        
        assert len(messages_page1) == 3
        assert len(messages_page2) == 2
    
    def test_conversation_title_auto_update(self, db_session, test_user):
        """测试对话标题自动更新"""
        # 创建默认标题的对话
        conversation_data = ConversationCreate()
        conversation = ConversationService.create_conversation(
            db_session, test_user, conversation_data
        )
        
        assert conversation.title == "新对话"
        
        # 发送第一条消息
        long_message = "这是一条很长的消息，用来测试对话标题是否会自动更新为消息的前50个字符，超出部分应该被截断"
        message_data = MessageCreate(content=long_message)
        
        import asyncio
        
        async def test_async():
            await ConversationService.send_message(
                db_session, test_user, conversation.id, message_data
            )
        
        asyncio.run(test_async())
        
        # 刷新对话对象
        db_session.refresh(conversation)
        
        # 检查标题是否更新
        expected_title = long_message[:50] + "..."
        assert conversation.title == expected_title


class TestDataIntegrity:
    """数据完整性测试"""
    
    def test_cascade_delete_conversation(self, db_session, test_user):
        """测试级联删除对话和消息"""
        # 创建对话
        conversation_data = ConversationCreate(title="待删除对话")
        conversation = ConversationService.create_conversation(
            db_session, test_user, conversation_data
        )
        
        # 添加消息
        message = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content="测试消息"
        )
        db_session.add(message)
        db_session.commit()
        
        # 删除对话
        ConversationService.delete_conversation(
            db_session, test_user, conversation.id
        )
        
        # 验证消息也被删除
        messages = db_session.query(Message).filter(
            Message.conversation_id == conversation.id
        ).all()
        assert len(messages) == 0
    
    def test_cascade_delete_user(self, db_session):
        """测试级联删除用户、对话和消息"""
        # 创建用户
        user_data = UserCreate(
            username="deleteuser",
            email="delete@example.com",
            password="password123"
        )
        user = AuthService.register_user(db_session, user_data)
        
        # 创建对话
        conversation_data = ConversationCreate(title="用户对话")
        conversation = ConversationService.create_conversation(
            db_session, user, conversation_data
        )
        
        # 添加消息
        message = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content="用户消息"
        )
        db_session.add(message)
        db_session.commit()
        
        user_id = user.id
        conversation_id = conversation.id
        
        # 删除用户
        db_session.delete(user)
        db_session.commit()
        
        # 验证对话和消息也被删除
        conversations = db_session.query(Conversation).filter(
            Conversation.user_id == user_id
        ).all()
        messages = db_session.query(Message).filter(
            Message.conversation_id == conversation_id
        ).all()
        
        assert len(conversations) == 0
        assert len(messages) == 0


if __name__ == "__main__":
    pytest.main([__file__]) 