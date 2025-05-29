<template>
  <div class="chat-container">
    <!-- 侧边栏 -->
    <div class="sidebar">
      <div class="sidebar-header">
        <el-button type="primary" @click="createNewConversation" class="new-chat-btn">
          <el-icon><Plus /></el-icon>
          新建对话
        </el-button>
        <el-dropdown @command="handleUserMenu">
          <span class="user-info">
            <el-icon><User /></el-icon>
            {{ currentUser?.username }}
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
      
      <div class="conversation-list">
        <div
          v-for="conversation in conversations"
          :key="conversation.id"
          :class="['conversation-item', { active: currentConversationId === conversation.id }]"
        >
          <div class="conversation-content" @click="selectConversation(conversation.id)">
            <div class="conversation-title">{{ conversation.title }}</div>
            <div class="conversation-time">{{ formatTime(conversation.updated_at) }}</div>
          </div>
          <div class="conversation-actions">
            <el-dropdown 
              @command="(command) => handleConversationMenu(command, conversation)"
              trigger="click"
              placement="bottom-end"
            >
              <div class="conversation-menu-btn">
                <el-icon><MoreFilled /></el-icon>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="rename">
                    <el-icon><Edit /></el-icon>
                    重命名
                  </el-dropdown-item>
                  <el-dropdown-item command="delete" divided>
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 主聊天区域 -->
    <div class="chat-main">
      <div v-if="!currentConversationId" class="welcome-screen">
        <h2>欢迎使用 AI Talk</h2>
        <p>选择一个对话开始聊天，或创建新的对话</p>
      </div>
      
      <div v-else class="chat-content">
        <!-- 消息列表 -->
        <div ref="messagesContainer" class="messages-container">
          <div
            v-for="message in messages"
            :key="message.id"
            :class="['message', message.role]"
          >
            <div class="message-avatar">
              <el-icon v-if="message.role === 'user'"><User /></el-icon>
              <el-icon v-else><ChatDotRound /></el-icon>
            </div>
            <div class="message-content">
              <div class="message-text">
                {{ message.content }}
                <span v-if="message.isStreaming" class="streaming-cursor">|</span>
              </div>
              <div class="message-time">{{ formatTime(message.created_at) }}</div>
            </div>
          </div>
          
          <!-- 加载中的消息 -->
          <div v-if="isLoading" class="message assistant">
            <div class="message-avatar">
              <el-icon><ChatDotRound /></el-icon>
            </div>
            <div class="message-content">
              <div class="message-text">
                <el-icon class="loading-icon"><Loading /></el-icon>
                AI 正在思考中...
              </div>
            </div>
          </div>
        </div>
        
        <!-- 输入区域 -->
        <div class="input-area">
          <div class="input-container">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="3"
              placeholder="输入您的消息..."
              @keydown.enter.exact.prevent="sendMessage"
              @keydown.enter.shift.exact="inputMessage += '\n'"
              :disabled="isLoading"
            />
            <el-button
              type="primary"
              @click="sendMessage"
              :loading="isLoading"
              :disabled="!inputMessage.trim()"
              class="send-btn"
            >
              发送
            </el-button>
          </div>
          <div class="input-tip">
            按 Enter 发送，Shift + Enter 换行
          </div>
        </div>
      </div>
    </div>
    
    <!-- 重命名对话对话框 -->
    <el-dialog v-model="renameDialogVisible" title="重命名对话" width="400px">
      <el-input v-model="newConversationTitle" placeholder="请输入新的对话标题" />
      <template #footer>
        <el-button @click="renameDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmRename">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, 
  User, 
  ArrowDown, 
  MoreFilled, 
  ChatDotRound, 
  Loading,
  Edit,
  Delete
} from '@element-plus/icons-vue'
import { conversationAPI } from '../api'

export default {
  name: 'Chat',
  components: {
    Plus,
    User,
    ArrowDown,
    MoreFilled,
    ChatDotRound,
    Loading,
    Edit,
    Delete
  },
  setup() {
    const router = useRouter()
    const conversations = ref([])
    const currentConversationId = ref(null)
    const messages = ref([])
    const inputMessage = ref('')
    const isLoading = ref(false)
    const messagesContainer = ref()
    
    // 重命名对话
    const renameDialogVisible = ref(false)
    const newConversationTitle = ref('')
    const renamingConversation = ref(null)
    
    // 当前用户
    const currentUser = computed(() => {
      const user = localStorage.getItem('user')
      return user ? JSON.parse(user) : null
    })
    
    // 加载对话列表
    const loadConversations = async () => {
      try {
        const response = await conversationAPI.getConversations()
        conversations.value = response || []
      } catch (error) {
        console.error('加载对话列表失败:', error)
      }
    }
    
    // 创建新对话
    const createNewConversation = async () => {
      try {
        const response = await conversationAPI.createConversation({
          title: '新对话'
        })
        conversations.value.unshift(response)
        selectConversation(response.id)
        ElMessage.success('创建新对话成功')
      } catch (error) {
        console.error('创建对话失败:', error)
      }
    }
    
    // 选择对话
    const selectConversation = async (conversationId) => {
      currentConversationId.value = conversationId
      await loadMessages(conversationId)
    }
    
    // 加载消息
    const loadMessages = async (conversationId) => {
      try {
        const response = await conversationAPI.getMessages(conversationId)
        messages.value = response || []
        await nextTick()
        scrollToBottom()
      } catch (error) {
        console.error('加载消息失败:', error)
      }
    }
    
    // 发送消息
    const sendMessage = async () => {
      if (!inputMessage.value.trim() || !currentConversationId.value || isLoading.value) {
        return
      }
      
      const messageContent = inputMessage.value.trim()
      inputMessage.value = ''
      
      // 添加用户消息到界面
      const userMessage = {
        id: Date.now(),
        role: 'user',
        content: messageContent,
        created_at: new Date().toISOString()
      }
      messages.value.push(userMessage)
      
      // 添加AI消息占位符
      const aiMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: '',
        created_at: new Date().toISOString(),
        isStreaming: true
      }
      messages.value.push(aiMessage)
      
      await nextTick()
      scrollToBottom()
      
      try {
        isLoading.value = true
        
        await conversationAPI.sendMessageStream(
          currentConversationId.value,
          { content: messageContent },
          (data) => {
            switch (data.type) {
              case 'user_message':
                // 更新用户消息ID
                const userMsgIndex = messages.value.findIndex(msg => msg.id === userMessage.id)
                if (userMsgIndex !== -1) {
                  messages.value[userMsgIndex] = {
                    ...data.message,
                    created_at: new Date().toISOString()
                  }
                }
                break
                
              case 'ai_start':
                // AI开始回复
                break
                
              case 'ai_chunk':
                // 追加AI回复内容
                const aiMsgIndex = messages.value.findIndex(msg => msg.id === aiMessage.id)
                if (aiMsgIndex !== -1) {
                  messages.value[aiMsgIndex].content += data.content
                  nextTick(() => scrollToBottom())
                }
                break
                
              case 'ai_complete':
                // AI回复完成，更新消息
                const completeMsgIndex = messages.value.findIndex(msg => msg.id === aiMessage.id)
                if (completeMsgIndex !== -1) {
                  messages.value[completeMsgIndex] = {
                    ...data.message,
                    created_at: new Date().toISOString(),
                    isStreaming: false
                  }
                }
                break
                
              case 'done':
                // 流式传输完成
                isLoading.value = false
                break
            }
          }
        )
        
        // 更新对话标题（如果是第一条消息）
        if (messages.value.filter(m => m.role === 'user').length === 1) {
          const conversation = conversations.value.find(c => c.id === currentConversationId.value)
          if (conversation && conversation.title === '新对话') {
            conversation.title = messageContent.slice(0, 20) + (messageContent.length > 20 ? '...' : '')
          }
        }
        
      } catch (error) {
        console.error('发送消息失败:', error)
        // 移除失败的消息
        messages.value = messages.value.filter(msg => 
          msg.id !== userMessage.id && msg.id !== aiMessage.id
        )
        ElMessage.error('发送消息失败，请检查网络或联系管理员')
      } finally {
        isLoading.value = false
      }
    }
    
    // 滚动到底部
    const scrollToBottom = () => {
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
    }
    
    // 格式化时间
    const formatTime = (timeStr) => {
      const time = new Date(timeStr)
      const now = new Date()
      const diff = now - time
      
      if (diff < 60000) { // 1分钟内
        return '刚刚'
      } else if (diff < 3600000) { // 1小时内
        return `${Math.floor(diff / 60000)}分钟前`
      } else if (diff < 86400000) { // 1天内
        return `${Math.floor(diff / 3600000)}小时前`
      } else {
        return time.toLocaleDateString()
      }
    }
    
    // 处理用户菜单
    const handleUserMenu = (command) => {
      if (command === 'logout') {
        ElMessageBox.confirm('确定要退出登录吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          router.push('/login')
        })
      }
    }
    
    // 处理对话菜单
    const handleConversationMenu = (command, conversation) => {
      if (command === 'rename') {
        renamingConversation.value = conversation
        newConversationTitle.value = conversation.title
        renameDialogVisible.value = true
      } else if (command === 'delete') {
        ElMessageBox.confirm('确定要删除这个对话吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(async () => {
          try {
            await conversationAPI.deleteConversation(conversation.id)
            conversations.value = conversations.value.filter(c => c.id !== conversation.id)
            if (currentConversationId.value === conversation.id) {
              currentConversationId.value = null
              messages.value = []
            }
            ElMessage.success('删除成功')
          } catch (error) {
            console.error('删除对话失败:', error)
          }
        })
      }
    }
    
    // 确认重命名
    const confirmRename = async () => {
      if (!newConversationTitle.value.trim()) {
        ElMessage.warning('请输入对话标题')
        return
      }
      
      try {
        await conversationAPI.updateConversation(renamingConversation.value.id, {
          title: newConversationTitle.value.trim()
        })
        
        renamingConversation.value.title = newConversationTitle.value.trim()
        renameDialogVisible.value = false
        ElMessage.success('重命名成功')
      } catch (error) {
        console.error('重命名失败:', error)
      }
    }
    
    onMounted(() => {
      // 调试：检查token
      console.log('Token in localStorage:', localStorage.getItem('token'))
      console.log('User in localStorage:', localStorage.getItem('user'))
      
      loadConversations()
    })
    
    return {
      conversations,
      currentConversationId,
      messages,
      inputMessage,
      isLoading,
      messagesContainer,
      renameDialogVisible,
      newConversationTitle,
      currentUser,
      createNewConversation,
      selectConversation,
      sendMessage,
      formatTime,
      handleUserMenu,
      handleConversationMenu,
      confirmRename
    }
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 300px;
  background: #f8f9fa;
  border-right: 1px solid #e9ecef;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.new-chat-btn {
  flex: 1;
  margin-right: 10px;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: #666;
  font-size: 14px;
}

.user-info .el-icon {
  margin: 0 4px;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.conversation-item {
  display: flex;
  align-items: center;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  position: relative;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.conversation-item:hover {
  background: #e9ecef;
  border-color: #dee2e6;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.conversation-item.active {
  background: #007bff;
  color: white;
  border-color: #0056b3;
  box-shadow: 0 2px 8px rgba(0,123,255,0.3);
}

.conversation-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  cursor: pointer;
  min-width: 0; /* 允许文本截断 */
}

.conversation-title {
  font-weight: 500;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.conversation-time {
  font-size: 12px;
  opacity: 0.7;
}

.conversation-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-left: 8px;
  flex-shrink: 0;
}

.conversation-menu-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s ease;
  color: #6c757d;
  opacity: 0.7;
}

.conversation-menu-btn:hover {
  background: rgba(108, 117, 125, 0.1);
  opacity: 1;
  transform: scale(1.1);
}

.conversation-item.active .conversation-menu-btn {
  color: rgba(255, 255, 255, 0.8);
}

.conversation-item.active .conversation-menu-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.welcome-screen {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #666;
}

.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.message {
  display: flex;
  margin-bottom: 20px;
}

.message.user {
  justify-content: flex-end;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 10px;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background: #007bff;
  color: white;
  order: 2;
}

.message.assistant .message-avatar {
  background: #6c757d;
  color: white;
}

.message-content {
  max-width: 70%;
  display: flex;
  flex-direction: column;
}

.message.user .message-content {
  align-items: flex-end;
  order: 1;
}

.message-text {
  background: #f8f9fa;
  padding: 12px 16px;
  border-radius: 18px;
  word-wrap: break-word;
  white-space: pre-wrap;
}

.message.user .message-text {
  background: #007bff;
  color: white;
}

.message-time {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
  padding: 0 16px;
}

.loading-icon {
  animation: spin 1s linear infinite;
  margin-right: 8px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.streaming-cursor {
  animation: blink 1s infinite;
  color: #007bff;
  font-weight: bold;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.input-area {
  padding: 20px;
  border-top: 1px solid #e9ecef;
  background: white;
}

.input-container {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.input-container .el-textarea {
  flex: 1;
}

.send-btn {
  height: 40px;
  padding: 0 20px;
}

.input-tip {
  font-size: 12px;
  color: #666;
  margin-top: 8px;
  text-align: center;
}

:deep(.el-textarea__inner) {
  resize: none;
  border-radius: 20px;
  padding: 12px 16px;
}

/* 下拉菜单样式优化 */
:deep(.el-dropdown-menu) {
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border: 1px solid #e9ecef;
  padding: 4px 0;
}

:deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  font-size: 14px;
  transition: all 0.2s ease;
}

:deep(.el-dropdown-menu__item .el-icon) {
  margin-right: 8px;
  font-size: 16px;
}

:deep(.el-dropdown-menu__item:hover) {
  background: #f8f9fa;
  color: #007bff;
}

:deep(.el-dropdown-menu__item[command="delete"]:hover) {
  background: #fff5f5;
  color: #dc3545;
}
</style> 