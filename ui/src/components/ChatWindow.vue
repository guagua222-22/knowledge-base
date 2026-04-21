<template>
  <div class="app-layout">
    <div class="sidebar">
      <div class="logo-section">
        <img src="@/assets/logo.png" alt="知识助手" width="120" height="120" />
        <span class="logo-text">知识助手</span>
      </div>
      <el-button class="new-chat-button" @click="newChat">
        <i class="fa-solid fa-plus"></i>
        &nbsp;新会话
      </el-button>
    </div>
    <div class="main-content">
      <div class="chat-header">
        <h2>万象智识库</h2>
        <span class="chat-description">基于企业知识库的智能问答系统</span>
      </div>
      <div class="chat-container">
        <div class="message-list" ref="messaggListRef">
          <div
            v-for="(message, index) in messages"
            :key="index"
            :class="
              message.isUser ? 'message user-message' : 'message bot-message'
            "
          >
            <!-- 会话图标 -->
            <div
              :class="
                message.isUser
                  ? 'fa-solid fa-user message-icon'
                  : 'fa-solid fa-database message-icon'
              "
            ></div>
            <!-- 会话内容 -->
            <div class="message-content">
              <div class="message-body">
                <span v-html="message.content"></span>
                <!-- loading -->
                <span
                  class="loading-dots"
                  v-if="message.isThinking || message.isTyping"
                >
                  <span class="dot"></span>
                  <span class="dot"></span>
                </span>
              </div>
            </div>
          </div>
        </div>
        <div class="input-container">
          <el-input
            v-model="inputMessage"
            placeholder="请输入消息"
            @keyup.enter="sendMessage"
          ></el-input>
          <el-button @click="sendMessage" :disabled="isSending" type="primary"
            >发送</el-button
          >
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import axios from 'axios'
import { v4 as uuidv4 } from 'uuid'

const messaggListRef = ref()
const isSending = ref(false)
const uuid = ref()
const inputMessage = ref('')
const messages = ref([])
const useStreamResponse = ref(true)

onMounted(() => {
  // 每次页面加载时创建新会话
  createNewSession()
  
  // 移除 setInterval，改用手动滚动
  watch(messages, () => scrollToBottom(), { deep: true })
})

const scrollToBottom = () => {
  if (messaggListRef.value) {
    messaggListRef.value.scrollTop = messaggListRef.value.scrollHeight
  }
}

const hello = () => {
  // 修改欢迎消息
  const welcomeMsg = {
    isUser: false,
    content: '你好，我是企业知识库管理系统，你可以向我提问来获取知识库中的相关信息',
    isTyping: false,
    isThinking: false,
  }
  messages.value.push(welcomeMsg)
}

const sendMessage = () => {
  if (inputMessage.value.trim()) {
    sendRequest(inputMessage.value.trim())
    inputMessage.value = ''
  }
}

const sendRequest = (message) => {
  isSending.value = true
  const userMsg = {
    isUser: true,
    content: message,
    isTyping: false,
    isThinking: false,
  }
  //第一条默认发送的用户消息"你好"不放入会话列表
  if(messages.value.length > 0){
    messages.value.push(userMsg)
  }

  // 添加机器人加载消息
  const botMsg = {
    isUser: false,
    content: '', // 增量填充
    isTyping: true, // 显示加载动画
    isThinking: false,
  }
  messages.value.push(botMsg)
  const lastMsg = messages.value[messages.value.length - 1]
  scrollToBottom()

  // 根据配置选择请求方式
  if (useStreamResponse.value) {
    sendStreamRequest(message, lastMsg)
  } else {
    sendNormalRequest(message, lastMsg)
  }
}

// 普通响应请求
const sendNormalRequest = (message, lastMsg) => {
  axios
    .post(
      'http://localhost:8000/api/chat',
      { 
        question: message,
        session_id: uuid.value
      }
    )
    .then((response) => {
      if (response && response.data && response.data.answer) {
        lastMsg.content = response.data.answer;
      }
      lastMsg.isTyping = false;
      isSending.value = false;
      scrollToBottom();
    })
    .catch((error) => {
      console.error('请求错误:', error);
      lastMsg.content = '请求失败，请重试';
      lastMsg.isTyping = false;
      isSending.value = false;
    });
}

// 流式响应请求
const sendStreamRequest = (message, lastMsg) => {
  // 创建请求URL和参数
  const url = `http://localhost:8000/api/chat/stream?question=${encodeURIComponent(message)}&session_id=${uuid.value}`;
  
  console.log('发送流式请求:', {
    url,
    session_id: uuid.value,
    question: message
  });
  
  // 创建 EventSource 连接 (使用GET方法)
  const eventSource = new EventSource(url);
  
  // 处理消息事件
  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      
      if (data.type === 'metadata') {
        console.log('收到元数据:', data.data);
      } 
      else if (data.type === 'content') {
        lastMsg.content += data.data;
        scrollToBottom();
      } 
      else if (data.type === 'end') {
        lastMsg.isTyping = false;
        isSending.value = false;
        eventSource.close();
      }
      else if (data.type === 'error') {
        console.error('流式响应错误:', data.data);
        lastMsg.content = '请求出错: ' + (data.data.message || '未知错误');
        lastMsg.isTyping = false;
        isSending.value = false;
        eventSource.close();
      }
    } catch (error) {
      console.error('解析事件数据失败:', error, event.data);
      // 如果不是JSON格式，可能是直接返回的文本
      if (event.data.trim()) {
        lastMsg.content += event.data;
        scrollToBottom();
      }
    }
  };
  
  // 处理连接错误
  eventSource.onerror = (error) => {
    console.error('EventSource 错误:', error);
    lastMsg.content = '正在思考中，请稍候...';
    lastMsg.isTyping = false;
    isSending.value = false;
    eventSource.close();
    
    // 如果流式请求失败，尝试回退到普通请求
    console.log('流式请求失败，尝试普通请求');
    sendNormalRequest(message, lastMsg);
  };
}

// 初始化 UUID
const initUUID = () => {
  let storedUUID = localStorage.getItem('user_uuid')
  if (!storedUUID) {
    storedUUID = uuidToNumber(uuidv4())
    localStorage.setItem('user_uuid', storedUUID)
  }
  uuid.value = storedUUID
}

const uuidToNumber = (uuid) => {
  let number = 0
  for (let i = 0; i < uuid.length && i < 6; i++) {
    const hexValue = uuid[i]
    number = number * 16 + (parseInt(hexValue, 16) || 0)
  }
  return number % 1000000
}

// 转换特殊字符
const convertStreamOutput = (output) => {
  return output
    .replace(/\n/g, '<br>')
    .replace(/\t/g, '&nbsp;&nbsp;&nbsp;&nbsp;')
    .replace(/&/g, '&amp;') // 新增转义，避免 HTML 注入
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

const newChat = () => {
  console.log('开始新会话');
  
  // 如果有已存在的会话ID，先清除其记忆
  if (uuid.value) {
    axios.post('http://localhost:8000/api/memory/clear', {
      session_id: uuid.value
    }).catch(error => {
      console.error('清除记忆失败:', error);
    });
  }
  
  // 生成新的会话ID
  const newUUID = uuidToNumber(uuidv4());
  localStorage.setItem('user_uuid', newUUID);
  uuid.value = newUUID;
  
  // 清空消息列表
  messages.value = [];
  
  // 重新发送欢迎消息
  hello();
}

// 创建新会话
const createNewSession = () => {
  // 生成新的会话ID
  const newUUID = uuidToNumber(uuidv4())
  localStorage.setItem('user_uuid', newUUID)
  uuid.value = newUUID
  
  // 清空消息列表
  messages.value = []
  
  // 发送欢迎消息
  hello()
}

</script>
<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 180px;
  background-color: #1E2030; /* 更深的蓝灰色，更接近截图 */
  padding: 20px 15px;
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #E0E0E0;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
  transition: width 0.3s ease;
}

.logo-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 30px; /* 增加间距 */
}

.logo-text {
  font-size: 20px;
  font-weight: bold;
  margin-top: 15px;
  color: #ffffff;
  text-align: center;
}

.new-chat-button {
  width: 100%;
  margin-top: auto;
  background-color: #23C89F; /* 更准确的绿色 */
  border: none;
  color: white;
  height: 44px;
  font-size: 16px;
}

.new-chat-button:hover {
  background-color: #20B592; /* 悬停颜色 */
  border: none;
}

.main-content {
  flex: 1;
  padding: 0;
  overflow-y: hidden; /* 防止两个滚动条 */
  background-color: #f5f7fa;
  display: flex;
  flex-direction: column;
}

.chat-header {
  padding: 15px 25px; /* 增加内边距 */
  background-color: #ffffff;
  border-bottom: 1px solid #e6e6e6;
}

.chat-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #303133;
}
.chat-description {
  color: #909399;
  font-size: 0.9rem;
}
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* 重要：使内部滚动 */
}

.message-list {
  flex: 1;
  padding: 20px 25px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: #ccc #f1f1f1;
}

.message {
  display: flex;
  margin-bottom: 20px;
  max-width: 85%;
  align-items: flex-start;
}
.message-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  margin-right: 15px;
}
.message-content {
  display: flex;
  flex-direction: column;
}

.message-body {
  padding: 12px 18px;
  border-radius: 8px;
  line-height: 1.6;
  font-size: 15px;
  position: relative;
}
/* 用户消息 */
.user-message {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.user-message .message-icon {
  margin-right: 0;
  margin-left: 15px;
  background-color: #E8F4FF; /* 更浅的蓝色 */
  color: #409EFF;
}
.user-message .message-body {
  background-color: #EBF5FF; /* 更浅的蓝色 */
  color: #333;
  border: 1px solid #C8E1FF; /* 更浅的边框 */
}

/* 机器人消息 */
.bot-message {
  align-self: flex-start;
}
.bot-message .message-icon {
  background-color: #F5F7FA; /* 更浅的灰色 */
  color: #606266;
}
.bot-message .message-body {
  background-color: #FFFFFF;
  border: 1px solid #EBEEF5; /* 更浅的边框 */
}
.loading-dots {
  display: inline-block;
  margin-left: 5px;
}
.loading-dots .dot {
  display: inline-block;
  width: 5px;
  height: 5px;
  background-color: #999;
  border-radius: 50%;
  animation: loading-blink 1.4s infinite both;
}
.loading-dots .dot:nth-child(2) {
  animation-delay: 0.2s;
}
.loading-dots .dot:nth-child(3) {
  animation-delay: 0.4s;
}
@keyframes loading-blink {
  0%, 80%, 100% {
    opacity: 0;
  }
  40% {
    opacity: 1;
  }
}


.input-container {
  padding: 15px 25px;
  background-color: #ffffff;
  border-top: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
}

.input-container .el-input {
  flex: 1;
  margin-right: 15px;
}
.input-container .el-input .el-input__inner {
  height: 44px;
  line-height: 44px;
}

.input-container .el-button {
  height: 44px;
  font-size: 16px;
  background-color: #409EFF; /* 蓝色发送按钮 */
}

.input-container .el-button:hover {
  background-color: #66B1FF; /* 悬停颜色 */
}

/* 媒体查询，当设备宽度小于等于 768px 时应用以下样式 */
@media (max-width: 768px) {
  .main-content {
    padding: 10px 0 10px 0;
  }
  .app-layout {
    flex-direction: column;
  }

  .sidebar {
    /* display: none; */
    width: 100%;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    padding: 10px;
  }

  .logo-section {
    flex-direction: row;
    align-items: center;
  }

  .logo-text {
    font-size: 20px;
  }

  .logo-section img {
    width: 40px;
    height: 40px;
  }

  .new-chat-button {
    margin-right: 30px;
    width: auto;
    margin-top: 5px;
  }
}

/* 媒体查询，当设备宽度大于 768px 时应用原来的样式 */
@media (min-width: 769px) {
  .main-content {
    padding: 0;
  }
}
</style>
