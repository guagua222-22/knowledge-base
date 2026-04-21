# 前端适配说明

## 修改内容

我们对前端代码进行了以下修改，以适配新的后端API：

1. **API端点更新**：
   - 将原有的 `/api/xiaozhi/chat` 端点更改为 `http://localhost:8000/api/chat`
   - 添加了对 `http://localhost:8000/api/chat/stream` 流式API的支持

2. **请求参数调整**：
   - 将 `{ memoryId, message }` 格式修改为 `{ session_id, question }`
   - 保留了原有的UUID生成和管理逻辑

3. **响应处理优化**：
   - 添加了对普通JSON响应和流式响应(SSE)的双重支持
   - 实现了流式响应失败时自动回退到普通响应的机制
   - 添加了错误处理和超时机制

4. **UI更新**：
   - 将应用名称从"硅谷小智（医疗版）"更改为"万象知识库"
   - 更新了欢迎消息，使其与知识库系统相符

5. **新会话功能增强**：
   - 实现了通过API清除会话记忆的功能
   - 优化了新会话创建流程，无需刷新页面

## 使用方法

1. **启动后端服务**：
   ```bash
   python api/run_server.py
   ```

2. **启动前端开发服务器**：
   ```bash
   cd ui/xiaozhi-ui
   npm install
   npm run dev
   ```

3. **构建前端**：
   ```bash
   cd ui/xiaozhi-ui
   npm run build
   ```

## 配置选项

在 `ChatWindow.vue` 中，可以通过修改以下变量来调整行为：

- `useStreamResponse`：是否使用流式响应（默认为true）
- 可以根据需要调整API的基础URL，以适应不同的部署环境

## 注意事项

- 确保后端API服务已启动并且CORS配置正确
- 如果在生产环境部署，请更新API端点为实际的生产环境URL
- 流式响应需要后端支持Server-Sent Events (SSE)
