import axios from 'axios'
import { ElMessage } from 'element-plus'

// 清理不必要的Cookie函数
const cleanupCookies = () => {
  // 获取所有cookie
  const cookies = document.cookie.split(';')
  
  // 只保留必要的cookie（例如认证相关的）
  const necessaryCookies = ['token'] // 只保留需要的cookie名称
  
  // 删除不必要的cookie
  cookies.forEach(cookie => {
    const cookieName = cookie.split('=')[0].trim()
    if (!necessaryCookies.includes(cookieName) && 
        cookieName.startsWith('http_')) { // 删除所有http_开头的cookie
      document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`
    }
  })
}

// 执行一次cookie清理
cleanupCookies()

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  maxContentLength: 10000000, // 增加内容长度限制
  maxBodyLength: 10000000 // 增加请求体长度限制
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      // 避免token过长导致的问题
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // 避免发送过大的Cookie
    config.withCredentials = false // 如果不需要跨域携带Cookie，可以关闭
    
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    } else {
      ElMessage.error(error.response?.data?.detail || '请求失败')
    }
    return Promise.reject(error)
  }
)

// 认证相关 API
export const authAPI = {
  // 用户注册
  register(data) {
    return api.post('/auth/register', data)
  },
  
  // 用户登录
  login(data) {
    return api.post('/auth/login', data)
  },
  
  // 获取当前用户信息
  getCurrentUser() {
    return api.get('/auth/me')
  }
}

// 对话相关 API
export const conversationAPI = {
  // 获取对话列表
  getConversations(page = 1, size = 20) {
    const skip = (page - 1) * size
    return api.get('/conversations', { params: { skip, limit: size } })
  },
  
  // 创建新对话
  createConversation(data) {
    return api.post('/conversations', data)
  },
  
  // 获取对话详情
  getConversation(id) {
    return api.get(`/conversations/${id}`)
  },
  
  // 更新对话标题
  updateConversation(id, data) {
    return api.put(`/conversations/${id}`, data)
  },
  
  // 删除对话
  deleteConversation(id) {
    return api.delete(`/conversations/${id}`)
  },
  
  // 获取对话消息
  getMessages(conversationId, page = 1, size = 50) {
    const skip = (page - 1) * size
    return api.get(`/conversations/${conversationId}/messages`, { 
      params: { skip, limit: size } 
    })
  },
  
  // 发送消息
  sendMessage(conversationId, data) {
    return api.post(`/conversations/${conversationId}/messages`, data)
  },
  
  // 发送流式消息
  sendMessageStream(conversationId, data, onMessage) {
    return new Promise((resolve, reject) => {
      const eventSource = new EventSource(`/api/conversations/${conversationId}/messages/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(data)
      })
      
      // 注意：EventSource 不支持 POST 请求，我们需要使用 fetch 和 ReadableStream
      fetch(`/api/conversations/${conversationId}/messages/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(data)
      }).then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        
        function readStream() {
          return reader.read().then(({ done, value }) => {
            if (done) {
              resolve()
              return
            }
            
            const chunk = decoder.decode(value)
            const lines = chunk.split('\n')
            
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6))
                  onMessage(data)
                } catch (e) {
                  console.error('解析SSE数据失败:', e)
                }
              }
            }
            
            return readStream()
          })
        }
        
        return readStream()
      }).catch(reject)
    })
  }
}

export default api 