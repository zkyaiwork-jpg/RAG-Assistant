# 前端（Vue 3 + HTML + CSS + JavaScript）

企业 AI 知识库助手的前端。纯手写 HTML / CSS / JavaScript，只依赖 Vue 3 生态本身，没有引入任何 UI 组件库。

## 技术栈

| 技术 | 作用 |
| --- | --- |
| Vue 3 | 页面与组件（单文件组件 `.vue`） |
| HTML / CSS | 结构与样式，全部手写，不依赖 UI 框架 |
| JavaScript | 业务逻辑 |
| Vue Router | 页面路由、登录守卫、权限守卫 |
| Axios | 统一请求实例与拦截器 |
| Vite | 开发服务器与打包 |

## 目录结构

```text
frontend/
├── index.html              # 唯一入口，挂载 #app
├── vite.config.js          # 开发服务器 + /api 代理
├── src/
│   ├── main.js             # 创建应用、注册路由、配置 401 处理
│   ├── App.vue             # 根组件（<router-view> + 全局提示）
│   ├── router/index.js     # 路由表与守卫
│   ├── stores/             # auth（登录态/权限）、toast（全局提示）
│   ├── api/                # http 实例 + 各业务接口
│   ├── utils/              # token、格式化、极简 Markdown 渲染
│   ├── components/         # 布局、侧边栏、顶栏、弹窗、空状态等公共组件
│   ├── views/              # 10 个页面
│   └── styles/main.css     # 全局样式（CSS 变量 + 手写样式）
├── Dockerfile              # 多阶段构建：Node 构建 → nginx 托管
└── nginx.conf              # 静态托管 + /api 反向代理
```

## 页面

| 路由 | 页面 | 需要的权限点 |
| --- | --- | --- |
| `/login` | 登录 | 无（公开） |
| `/welcome` | 桌面版首次启动的称呼设置（浏览器里自动回首页） | 无（公开） |
| `/` | 工作台（统计、最近入库） | 登录 |
| `/documents` | 知识库文档（上传/编辑/删除/文件夹） | `file_view` |
| `/chat` | AI 问答（会话列表、来源引用） | `file_view` |
| `/search` | 智能检索 | `file_view` |
| `/users` | 用户管理 | `user_manage` |
| `/departments` | 部门管理 | `user_manage` |
| `/teams` | 团队管理 | `user_manage` |
| `/audit` | 审计日志 | `audit_view` |
| `/settings` | 模型设置 | `model_manage` |

## 本地开发

```bash
# 1. 先启动后端（项目根目录）
python -m uvicorn app.main:app --reload

# 2. 启动前端
cd frontend
npm install
npm run dev
```

访问 http://127.0.0.1:5173 。开发环境下 Vite 会把 `/api/*` 代理到 `http://127.0.0.1:8000/*`（并去掉 `/api` 前缀），因此不需要处理跨域。

## 生产构建

```bash
npm run build     # 产物在 dist/
```

`dist/` 可以直接交给 nginx 托管，也可以用 Docker：

```bash
docker compose up --build frontend
```

## 几个实现说明

1. **登录态**：JWT 存在 `localStorage`，Axios 请求拦截器自动加 `Authorization: Bearer`；任何接口返回 401 都会清掉凭证并跳回登录页，同时记住原地址。
2. **权限控制**：路由上写 `meta.permission`，`router.beforeEach` 里判断；侧边栏按权限过滤菜单，页面内的按钮也按权限显示。**前端只负责"少让人看见"，真正的校验在后端。**
3. **Markdown 渲染**：AI 回答是 Markdown，用 `src/utils/markdown.js` 里约 90 行的渲染器处理，先转义 HTML 再替换语法，避免 XSS，也不引入额外依赖。
4. **会话 id**：提问返回的 `conversation_id` 会立刻记下来，下一轮带回去，才能接着同一个会话聊。
5. **上传**：用 `FormData` 提交，支持文件夹归档和四种可见范围；可见范围下拉会按当前账号的发布权限过滤。
