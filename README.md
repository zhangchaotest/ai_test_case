# AI 智能测试用例生成平台

这是一个基于 FastAPI、Vue 3 和 AutoGen 的 AI 测试用例生成平台，支持需求分析、测试用例生成、提示词管理等功能。

## 项目结构

```
ai_test_case/
├── backend/                # 后端代码
│   ├── agents/             # AI 代理相关代码
│   │   ├── case_agent.py       # 测试用例生成代理
│   │   ├── context_manager.py  # 上下文管理
│   │   ├── knowledge_manager.py # 知识库管理
│   │   ├── llm_factory.py      # LLM 客户端工厂
│   │   ├── prompt_manager.py   # 提示词管理
│   │   ├── requirement_agent.py # 需求分析代理
│   │   └── test_dimension.py   # 测试维度管理
│   ├── api/                # API 接口
│   │   ├── analysis.py         # 需求分析接口
│   │   ├── cases.py            # 测试用例接口
│   │   ├── export.py           # 导出接口
│   │   ├── projects.py         # 项目管理接口
│   │   ├── prompts.py          # 提示词管理接口
│   │   └── requirements.py     # 需求管理接口
│   ├── database/           # 数据库相关
│   │   ├── case_db.py          # 测试用例数据库操作
│   │   ├── db_base.py          # 数据库基础类
│   │   ├── init_db.py          # 数据库初始化
│   │   ├── project_db.py       # 项目数据库操作
│   │   ├── prompt_db.py         # 提示词数据库操作
│   │   └── requirement_db.py    # 需求数据库操作
│   ├── requirement/         # 需求文档
│   ├── services/           # 服务层
│   │   ├── case_service.py     # 测试用例服务
│   │   ├── project_service.py   # 项目服务
│   │   └── requirement_service.py # 需求服务
│   ├── utils/              # 工具函数
│   ├── .env                 # 环境变量配置
│   ├── config.py            # 配置文件
│   ├── main.py             # 后端入口
│   └── requirements.txt    # 后端依赖
├── frontend/               # 前端代码
│   ├── src/                # 源代码
│   │   ├── api/            # API 调用
│   │   ├── components/     # 组件
│   │   ├── layout/          # 布局
│   │   ├── router/          # 路由
│   │   ├── views/           # 页面
│   │   │   ├── BreakdownList.vue      # 需求解构中心
│   │   │   ├── FeatureConfig.vue      # 功能控制面板
│   │   │   ├── PromptManagement.vue  # 提示词实验室
│   │   │   ├── RequirementAnalysis.vue # 需求智能解析
│   │   │   ├── RequirementList.vue    # 功能模块管理
│   │   │   ├── TestCaseList.vue       # 用例矩阵
│   │   │   └── TestExecution.vue      # 执行引擎
│   │   ├── App.vue          # 主应用
│   │   └── main.js          # 入口文件
│   ├── package.json        # 前端依赖
│   └── vite.config.js      # Vite 配置
├── tests/                   # 测试脚本
├── .gitignore              # Git 忽略文件
├── CHANGELOG.md             # 更新记录
├── README.md               # 项目说明
└── start_services.ps1      # 一键启动脚本
```

## 快速开始

### 1. 环境要求

- Python 3.8+
- Node.js 14+
- npm 6+

### 2. 后端设置

1. 进入后端目录:
   ```
   cd backend
   ```

2. 创建虚拟环境并激活:
   ```
   python -m venv venv_backend
   venv_backend\Scripts\activate     # Windows
   ```

3. 安装依赖:
   ```
   pip install -r requirements.txt
   ```

4. 配置环境变量:
   编辑 `backend/.env` 文件，配置您的 LLM 服务和 Dify 知识库信息。
   ```
   # LLM 配置
   GEMINI_API_KEY=your_gemini_api_key

   # Dify 知识库配置
   DIFY_API_KEY=your_dify_api_key
   DIFY_ENDPOINT=https://dify-test.lbxdrugs.com
   DIFY_RETRIEVE_LIMIT=3
   ```

### 3. 前端设置

1. 进入前端目录:
   ```
   cd frontend
   ```

2. 安装依赖:
   ```
   npm install
   ```

### 4. 一键启动服务

使用 PowerShell 运行启动脚本:

```
.start_services.ps1
```

该脚本会自动：
- 检查并关闭占用端口的进程
- 启动后端服务 (http://localhost:8888)
- 启动前端服务 (http://localhost:5173)

### 5. 手动启动（可选）

#### 后端启动

```
cd backend
venv_backend\Scripts\activate
python main.py
```

后端将在 `http://localhost:8888` 上运行。

#### 前端启动

```
cd frontend
npm run dev
```

前端将在 `http://localhost:5173` 上运行。

## 功能特点

### 1. 需求智能解析（原需求分析）
- 支持文本需求文档的智能分析
- 自动识别功能点和验收标准
- 提供可视化的需求拆解结果

### 2. 用例矩阵（原测试用例生成与管理）
- 基于 AI 的智能测试用例生成
- 支持不同测试领域（基础测试、Web应用测试、API测试）
- 支持增量生成和全量生成模式
- 实时流式输出生成过程
- 集成 Dify 知识库，自动检索相关知识并融入生成过程
- 支持测试用例的查看、筛选、批量更新和导出
- 重复用例检测和防止功能

### 3. 提示词实验室（原提示词管理）
- 支持提示词的增删改查
- 支持按领域和类型分类管理
- 确保生成器提示词包含目标数量信息
- 详细的提示词选择和使用日志

### 4. 功能控制面板（原功能开关配置）
- 可视化管理系统功能开关
- 动态配置 Dify 知识库、LLM 模型、测试维度分析等功能
- 支持配置的持久化存储

### 5. 执行引擎（原用例执行）
- 支持测试用例的执行状态跟踪
- 提供执行结果的记录和统计

### 6. 项目管理
- 支持项目的创建和管理
- 支持按项目筛选功能点和测试用例

### 7. 日志系统
- 详细的知识库调用日志
- 提示词选择和使用日志
- 用例生成流程日志
- 便于问题排查和系统监控

### 8. 前端交互
- 生成用例配置弹窗，提供灵活的参数设置
- 优化的提示词管理页面
- 清晰的操作状态反馈
- **智能工坊**与**配置中心**二级菜单结构，操作更便捷

## 技术特点

- **后端**: 使用 FastAPI 构建高性能 API，集成 AutoGen 框架实现 AI 对话
- **前端**: 使用 Vue 3、Element Plus 和 Vite 构建现代化界面
- **AI**: 利用 AutoGen 的多 Agent 协作能力，实现需求分析和测试用例生成
- **数据库**: 使用 SQLite 本地数据库，简化部署和维护
- **流式响应**: 实现 SSE (Server-Sent Events) 流式响应，提供实时反馈
- **提示词管理**: 支持自定义提示词，优化 AI 生成质量
- **测试维度**: 实现测试维度管理，提高测试用例覆盖度
- **知识库集成**: 集成 Dify 知识库，实现知识检索和上下文融入
- **日志系统**: 详细的系统日志，便于问题排查和系统监控
- **配置管理**: 集中化配置管理，便于环境切换和参数调整

## 注意事项

1. 确保您的 LLM 服务配置正确且可用
2. 数据库存储在本地 SQLite 文件中 (`backend/database/test_cases.db`)
3. 平台使用 SSE 流式响应获取 AI 生成的结果，请耐心等待
4. 首次运行时，系统会自动初始化数据库表结构和默认数据
5. 提示词管理功能确保即使用户编辑提示词，也会包含目标数量信息
6. Dify 知识库配置：需要在 `backend/.env` 文件中配置 Dify API Key 和端点
7. 知识库集成功能需要确保 Dify 服务可用且 API Key 有效
8. 系统会自动记录详细的操作日志，便于问题排查和系统监控

## 扩展建议

1. **添加更多测试领域**: 可以根据业务需求添加更多测试领域，如移动端测试、性能测试等
2. **集成更多 LLM 模型**: 可以扩展 `llm_factory.py` 支持更多 LLM 模型
3. **添加测试执行功能**: 可以实现测试用例的执行和结果记录
4. **添加报告生成功能**: 可以生成测试覆盖率和质量报告
5. **添加团队协作功能**: 可以支持多用户协作和权限管理

## 故障排除

### 端口被占用
- 运行 `start_services.ps1` 脚本会自动检查并关闭占用端口的进程
- 手动启动时，可以使用 `netstat -ano | findstr :8888` 查看占用端口的进程，然后使用 `taskkill /PID <进程ID> /F` 关闭进程

### LLM 连接失败
- 检查 `backend/agents/llm_factory.py` 中的 LLM 配置
- 确保网络连接正常
- 确保 LLM 服务可用且有足够的配额

### 数据库初始化失败
- 检查 `backend/database/init_db.py` 中的数据库路径配置
- 确保有写入权限
- 尝试删除 `backend/database/test_cases.db` 文件，重新运行服务

## 许可证

MIT
