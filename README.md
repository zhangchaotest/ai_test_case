# AI 智能测试用例生成平台

这是一个基于 FastAPI、Vue 3 和 AutoGen 的 AI 测试用例生成平台 Demo。

## 项目结构

```
ai-test-demo/
├── backend/
│   ├── main.py            # FastAPI 核心代码
│   ├── database.py        # 数据库连接与初始化
│   ├── models.py          # Pydantic 模型
│   ├── agents.py          # AutoGen Agent 定义
│   ├── tools.py           # 工具函数封装
│   ├── .env               # 环境变量 (存放 API Key)
│   └── requirements.txt   # 后端依赖
└── frontend/
    ├── src/
    │   ├── api/           # Axios 封装
    │   ├── components/    # 组件
    │   ├── App.vue        # 主页面逻辑
    │   └── main.js        # 入口文件
    ├── package.json       # 前端依赖
    └── vite.config.js     # Vite 配置
```

## 快速开始

### 1. 后端设置

1. 进入后端目录:
   ```
   cd backend
   ```

2. 创建虚拟环境并激活:
   ```
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate     # Windows
   ```

3. 安装依赖:
   ```
   pip install -r requirements.txt
   ```

4. 配置环境变量:
   编辑 `.env` 文件，填入您的 OpenAI API Key:
   ```
   OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   OPENAI_MODEL=gpt-4o
   ```

5. 启动后端服务:
   ```
   python main.py
   ```
   
   后端将在 `http://localhost:8000` 上运行。

### 2. 前端设置

1. 进入前端目录:
   ```
   cd frontend
   ```

2. 安装依赖:
   ```
   npm install
   ```

3. 启动前端开发服务器:
   ```
   npm run dev
   ```
   
   前端将在 `http://localhost:5173` 上运行。

### 3. 使用平台

1. 访问 `http://localhost:5173`
2. 在文本框中输入需求文档
3. 点击"分析需求"按钮
4. 确认识别出的功能点
5. 为功能点生成测试用例
6. 确认并保存测试用例

## 技术特点

- **后端**: 使用 FastAPI 构建高性能 API，集成 AutoGen 框架实现 AI 对话
- **前端**: 使用 Vue 3 和 Element Plus 构建现代化界面
- **AI**: 利用 AutoGen 的多 Agent 协作能力，实现需求分析和测试用例生成
- **安全**: API Key 通过环境变量管理，不在代码中硬编码
- **跨域**: 正确配置 CORS，支持前后端分离架构

## 注意事项

1. 确保您的 OpenAI API Key 有足够的权限访问所选模型
2. 数据库存储在本地 SQLite 文件中 (`test_case.db`)
3. 平台使用轮询机制获取 AI 生成的结果，请耐心等待