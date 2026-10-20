# 企业 AI 知识库助手

> 面向企业内部知识问答场景的 RAG 知识库系统，支持企业组织架构、RBAC 权限控制、文档级可见性、会话隔离、审计日志与 RAG 检索效果评测。

基于 FastAPI + React + Chroma + BGE + DeepSeek 构建。

系统将企业内部文档进行解析、分块和向量化存储，在用户提问时通过语义检索召回相关知识片段，并结合 DeepSeek 生成带来源引用的回答。

相比普通 RAG Demo，本项目重点解决企业知识库中的两个实际问题：

1. 回答是否能检索到正确知识
2. 用户是否有权限检索这些知识

---

# 项目背景

企业内部通常存在大量规章制度、业务规范和内部资料。

员工遇到问题时，传统方式往往需要：

* 人工查找文档
* 在多个文件中搜索关键词
* 询问其他员工
* 联系管理人员确认制度

而通用大模型本身并不了解企业内部知识。

例如：

> 公司事假应该怎么申请？

DeepSeek 无法直接知道某家企业内部的请假制度。

因此，本项目通过 RAG（Retrieval-Augmented Generation） 将企业内部知识库与大语言模型结合：

```text
企业文档
   ↓
文档解析
   ↓
文本分块
   ↓
Embedding 向量化
   ↓
Chroma 向量数据库
   ↓
用户问题
   ↓
语义检索
   ↓
相关知识片段
   ↓
DeepSeek
   ↓
生成企业知识回答
```

同时，企业知识并不是所有员工都可以访问，因此项目进一步加入组织架构、RBAC 和文档可见性控制，使知识检索遵循企业权限边界。

---

# 核心亮点

## 1. 企业级 RAG 知识问答

实现完整 RAG 链路：

```text
文档上传
  ↓
DOCX 解析
  ↓
Chunk 文本分块
  ↓
BGE Embedding
  ↓
Chroma 向量存储
  ↓
语义检索
  ↓
TopK 候选知识
  ↓
Distance Threshold 过滤
  ↓
构建 Context
  ↓
DeepSeek
  ↓
回答 + Sources
```

回答不仅返回生成内容，同时返回对应知识来源，方便用户确认回答依据。

---

## 2. 企业 RBAC 权限体系

系统实现基于角色的权限控制，不同用户拥有不同的数据访问范围。

主要角色包括：

| 角色       | 主要权限范围   |
| -------- | ----------   | 
| admin    | 企业级管理权限    |
| manager  | 部门级管理与访问权限 |
| leader   | 团队级权限     |
| employee | 普通员工权限   |

接口访问通过 JWT 身份认证与 RBAC 权限进行控制。

---

## 3. 文档级可见性控制

企业文档支持不同可见范围：

| Visibility | 含义           |
| ---------- | ------------ |
| private    | 仅指定用户/上传者可访问 |
| team       | 团队内部可访问      |
| department | 部门内部可访问      |
| company    | 企业内部可访问      |

系统不会简单地将所有知识检索后交给大模型判断权限，而是在进入 LLM 之前完成权限过滤。

---

## 4. RAG 检索前权限过滤

项目将权限控制放在知识检索链路中，而不是仅依赖 Prompt 约束模型。

核心流程：

```text
用户问题
   ↓
JWT 身份认证
   ↓
file_view 权限检查
   ↓
SQL 查询当前用户可访问文档
   ↓
生成文档白名单
   ↓
Embedding
   ↓
Chroma 在允许范围内检索
   ↓
返回结果二次权限校验
   ↓
Distance Threshold
   ↓
构建 Context
   ↓
DeepSeek
```

如果用户没有任何可访问文档：

```text
Allowed Documents = []
        ↓
直接返回空检索结果
        ↓
不会继续检索企业知识
```

采用 Fail-Closed 思路：权限无法确认时默认拒绝访问，而不是默认放行。

这样可以降低无权限文档进入 LLM Context 的风险。

---

## 5. 企业组织架构

系统建立：

```text
Company
   ↓
Department
   ↓
Team
   ↓
User
```

Department 与 Team 建立组织关系，用户可以归属于对应部门和团队。

组织架构不仅用于用户管理，同时参与文档权限计算。

---

## 6. 会话隔离

系统建立 Conversation 与 ChatMessage 数据模型。

不同用户之间的 AI 对话相互隔离，用户只能访问自己的会话记录，避免不同账号之间出现会话数据串用。

---

## 7. 审计日志

系统记录关键管理操作和访问行为，为企业内部系统提供操作追踪能力。

管理员可以通过审计接口查看相关记录。

---

## 8. 数据库迁移

项目使用 Alembic 管理数据库 Schema 变化。

数据库结构升级通过 Migration 管理，而不是依赖手动修改数据库表结构。

---

# 系统架构

```text
┌─────────────────────────────┐
│       React + TypeScript    │
│           Frontend          │
└──────────────┬──────────────┘
               │ HTTP API
               ↓
┌─────────────────────────────┐
│           FastAPI           │
│                             │
│ Authentication / JWT        │
│ RBAC Permission             │
│ Document Permission         │
│ Conversation Isolation      │
│ Audit Log                   │
└──────────────┬──────────────┘
               │
               ↓
┌─────────────────────────────┐
│          RAG Service        │
│                             │
│ SQL Document Whitelist      │
│ Embedding                   │
│ Vector Search               │
│ Permission Recheck          │
│ Distance Filter             │
└─────────┬───────────┬───────┘
          │           │
          ↓           ↓
┌──────────────┐  ┌──────────────┐
│    Chroma    │  │   DeepSeek   │
│ Vector Store │  │     LLM      │
└──────────────┘  └──────────────┘
```

---

# RAG 检索链路

当前核心检索流程：

```text
POST /chat
    ↓
JWT 校验（含 token_version，改密后旧 token 立即失效）
    ↓
file_view Permission（RBAC 功能权限）
    ↓
SQL 查询可访问 Documents（角色 + 部门 + 小组 + 可见性）
    ↓
Document Whitelist
    ↓
Question Embedding
    ↓
Chroma 召回候选池 Top10（where document_id ∈ 白名单）
    ↓
Permission Recheck（逐条回验，防 metadata 漂移）
    ↓
硬拒答：池内最近距离 ≥ 0.85 → 直接返回「没有找到相关资料」
    ↓
bge-reranker-base 对 10 条候选重排（失败回落 Chroma 顺序）
    ↓
模糊带判定：0.65 ≤ 最近距离 < 0.85 → 模型判断片段能否支撑回答
    ↓
取重排后前 3 条 → Build Context
    ↓
DeepSeek
    ↓
Answer + Sources（文档 / 文件夹 / 分块号）
```

当前主要检索参数：

```text
Embedding Model:
BAAI/bge-small-zh-v1.5

Vector Database:
Chroma（本地持久化）

Chunk Size:
100（由 100/200/300/400 四组切片对照实验确定）

Chunk Overlap:
0

候选池:
10（重排的输入宽度）

TopK:
3（重排后进入上下文的数量）

拒答策略:
三段式 —— 最近距离 <0.65 直接回答；0.65~0.85 由模型判定片段能否支撑回答；≥0.85 直接拒答

Rerank:
BAAI/bge-reranker-base（CrossEncoder，CPU，启动时预热，失败自动回落）
```

---

# RAG 检索评测

评测目标：不靠主观体验判断检索质量，而是把"有没有找对条款""没有答案时会不会乱答"变成可复现、可对照的指标。

## 评测集

| 集合 | 规模 | 说明 |
| --- | ---: | --- |
| 正向题 | **308** | 每题标注「金标文档 + 条款号 + 答案片段」，覆盖全部 29 篇文档 |
| 负向题 | **200** | near 80（主题相邻但制度未规定）/ mid 60 / far 60（业务类无关问题） |

题目以 CSV 管理：`evals/questions_v2_positive.csv`、`evals/questions_v2_negative.csv`。
构建脚本会用「答案关键词必须出现在声明的条款里」逐条断言，防止题号与金标错位（`evals/build_question_set.py`）。

## 判定口径

```text
片段级 Top1/Top3：召回的分块里是否包含【金标条款】
负向拒答率      ：知识库确实没有答案时，是否返回空结果
```

之所以用片段级而不是文档级：文档只有 29 篇时，文档级命中的随机基线就有约 3%；更早只有 3 篇文档时，100 与 200 两种切片的文档级 Top1 都显示 93.5%，指标已经饱和，根本无法区分优劣。

## 当前线上结果

| 指标 | 结果 |
| --- | ---: |
| 片段 Top1 | **94.5%**（291/308） |
| 片段 Top3 | **99.0%**（305/308） |
| 文档 Top1 / Top3 | 96.1% / 99.4% |
| 负向拒答 | **95.0%**（190/200） |
| └ near / mid / far | 75/80 · 57/60 · 58/60 |

## 关键对照实验

### 1. 切片大小（100 / 200 / 300 / 400）

| chunk | 分块数 | 平均长度 | 片段Top1 | 片段Top3 | 负向拒答 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| **100** | 346 | 79 字 | **89.9%** | **93.5%** | 76% |
| 200 | 163 | 168 字 | 79.5% | 82.5% | 83% |
| 300 | 108 | 254 字 | 75.3% | 77.6% | 86% |
| 400 | 85 | 322 字 | 67.5% | 69.2% | 90% |

结论：**100 最优**，命中率随切片增大单调下降。拒答率的"反向提升"是假象——切片越大向量被稀释，所有距离整体漂移，正例也被推过阈值；用 AUC 剔除阈值影响后，仍是 100 的分离度最高（0.981 vs 0.931）。

### 2. 候选池宽度（3 → 10）

重排只能对进入候选池的片段排序。正确片段排在 4~10 名时，池子只有 3 就永远进不了重排：

| 配置 | 重排 Top1 | 重排 Top3 |
| --- | ---: | ---: |
| 向量 Top3 + 重排 | 91.2% | 94.8% |
| **向量 Top10 + 重排** | **94.5%** | **99.0%** |

### 3. 拒答策略

| 方案 | Top1 | Top3 | 拒答 |
| --- | ---: | ---: | ---: |
| 纯距离阈值（0.70） | 89.3% | 93.8% | 93.5% |
| 纯距离阈值（0.75） | 91.9% | 96.4% | 82.0% |
| **三段式（当前）** | **94.5%** | **99.0%** | **95.0%** |

三段式的关键是把"要不要答"和"答哪几条"分开：只有候选池内**最近距离**参与拒答判断，模糊带（0.65~0.85）才调用一次模型判定片段能否支撑回答。

## 历史演进

| 阶段 | 评测集 | 说明 |
| --- | --- | --- |
| Baseline V1 | 15 题 | 验证链路可用，发现"正确答案进了 Top3 但 Top1 被相似文档占据" |
| Baseline V2 | 50 题 + 10 负向 | 扩充语料后复测，首次引入负向问题检查误召回 |
| **现行** | **308 正向 + 200 负向** | 改为片段级判定 + 分档负向，支持切片/池宽/拒答策略的对照实验 |

早期 50 题版本的结论（Top1 86%、Top3 94%）已被现行评测集取代，保留在 `evals/results/` 中作为过程记录。

---

# Rerank（生产链路）

重排不是实验特性，而是当前检索链路的固定环节。

```text
Question
   ↓
Embedding → Chroma Top10 候选
   ↓
bge-reranker-base（CrossEncoder，CPU）
   ↓
按 Question/Chunk 相关性重排
   ↓
取前 3 条进入上下文
```

几个实现细节：

* 模型在应用启动时预热（`lifespan`），避免首个请求承担加载延迟
* 重排**只改变顺序，不改变距离**——阈值判定始终基于双塔的原始距离
* 重排失败自动回落到 Chroma 原始顺序，并记录 `fallback=chroma_order`，不让排序增强变成单点故障

---

# 技术栈

## Frontend

* React
* TypeScript
* Vite
* Tailwind CSS
* Axios

## Backend

* Python 3.11
* FastAPI
* Pydantic
* Uvicorn
* SQLAlchemy
* Alembic

## AI / RAG

* DeepSeek（兼容 OpenAI SDK，模型与密钥可在界面配置、加密存库）
* BAAI/bge-small-zh-v1.5（Embedding）
* BAAI/bge-reranker-base（CrossEncoder 重排，CPU）
* Chroma（本地持久化向量库）

## Document Processing

* python-docx（DOCX）
* PyMuPDF（PDF）
* TXT 纯文本

三种格式均已在后端解析器注册（`app/services/parsers/`），新增格式只需实现 `BaseParser` 子类并注册到工厂。

---

# 核心功能

### 知识库

* 文档上传（DOCX / PDF / TXT）
* 文档解析与文本分块（chunk=100）
* Embedding 与 Chroma 向量存储
* 文档列表、删除、改名
* **文件夹管理**：上传时归档、已有文档可随时切换或移回未分配
* 语义检索（带片段级来源）
* RAG 问答（答案 + 来源引用）
* 三段式拒答：知识库没有答案时明确拒答，不编造

### 权限

* JWT 身份认证
* RBAC
* 用户角色权限
* 文档可见性
* SQL 文档白名单
* Chroma 检索范围限制
* 检索结果二次权限校验

### 企业管理

* User
* Department
* Team
* Role
* Permission

### 系统能力

* Conversation 会话隔离
* ChatMessage 消息记录
* AuditLog 审计日志
* Alembic 数据库迁移
* RAG Evaluation

---

# 项目目录

```text
enterprise-ai-kb/
│
├── app/
│   ├── api/                 # 业务路由（文档/检索/问答/用户/部门/小组/模型配置/审计）
│   ├── routers/             # 认证路由
│   ├── auth/                # JWT、密码哈希、RBAC 依赖、对象级权限
│   ├── models/              # 10 张表（用户/角色/权限/部门/小组/文档/会话/消息/审计/模型配置）
│   ├── services/            # 业务服务：检索、重排、拒答判定、文档、审计…
│   │   └── parsers/         # DOCX / PDF / TXT 解析器
│   ├── database/            # 引擎、建表、RBAC 种子、首管理员 bootstrap
│   ├── core/                # 路径与日志配置
│   └── main.py              # FastAPI 应用入口
│
├── alembic/versions/        # 6 个数据库迁移
│
├── evals/                   # 评测资产
│   ├── questions_v2_positive.csv   # 308 道正向题（金标文档+条款+答案片段）
│   ├── questions_v2_negative.csv   # 200 道负向题（near/mid/far）
│   ├── build_question_set.py       # 题库构建与校验
│   └── results/                    # 切片对照、阈值扫描、拒答策略实验
│
├── scripts/                 # 评测、重建索引、语料生成、可见性审计
│
├── samples/                 # 评测语料（29 篇制度文档）
│
├── tests/                   # 214 个后端测试
│
├── frontend-react/          # React 前端（当前）
│
├── frontend/                # 历史前端（Streamlit + Vue，未启用）
│
├── desktop/                 # Electron 桌面封装
│
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── pytest.ini
├── requirements.txt
├── .env.example
└── README.md
```

---

# 快速开始

## 1. 克隆项目

```bash
git clone <your-repository-url>
cd enterprise-ai-kb
```

---

## 2. 创建 Python 虚拟环境

Windows：

```bash
python -m venv venv
venv\Scripts\activate
```

安装依赖：

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3. 配置环境变量

在项目根目录创建：

```text
.env
```

根据 `.env.example` 配置实际运行环境。

例如：

```text
DEEPSEEK_API_KEY=your_deepseek_api_key
JWT_SECRET_KEY=your_random_secret
MODEL_CONFIG_ENCRYPTION_KEY=your_encryption_key
```

请勿将真实 API Key、JWT Secret 或其他敏感信息提交到 Git。

---

# 首次部署

系统不开放匿名注册。

首先执行数据库 Migration：

```bash
python -m alembic upgrade head
```

然后初始化 RBAC 权限并创建首个管理员：

```bash
python -m app.database.bootstrap
```

建议组织创建顺序：

```text
Department
    ↓
Team
    ↓
User
```

admin 不强制要求所属 Team。

---

# 启动后端

```bash
python -m uvicorn app.main:app --reload
```

默认地址：

```text
http://127.0.0.1:8000
```

FastAPI Swagger：

```text
http://127.0.0.1:8000/docs
```

---

# 启动前端

```bash
cd frontend-react
npm install
npm run dev
```

Vite 会在终端输出实际访问地址。

开发环境通常为：

```text
http://127.0.0.1:5173
```

生产构建：

```bash
npm run build
```

---

# 测试

项目包含后端功能、权限和数据完整性相关测试。

测试内容主要包括：

```text
Document Permission
Team Permission Matrix
Document Mutation
Document List Permission
Conversation Isolation
Audit
User Management
Migration
Data Integrity
```

同时 `evals/` 用于 RAG 检索效果评测，与普通功能测试分开管理。

---

# 数据与安全

项目按照企业知识库场景对敏感数据进行隔离。

以下内容不应提交至 Git：

```text
.env
API Key
JWT Secret
真实企业文档
Chroma 本地数据
模型缓存
运行日志
本地数据库敏感数据
```

权限设计遵循：

```text
Authentication
      ↓
Authorization
      ↓
Document Permission
      ↓
Retrieval
      ↓
LLM
```

即：

**先判断用户能够看到什么，再进行知识检索，而不是先检索敏感知识再让 LLM 判断是否应该回答。**

---

# 后续计划

已完成：

* [x] Team（小组）管理与小组级文档可见性
* [x] PDF / TXT 文档解析
* [x] 评测集扩展到 308 正向 + 200 负向，并改为片段级判定
* [x] 切片大小 / 候选池宽度 / 拒答策略的对照实验
* [x] 文档文件夹分配与切换
* [x] 自动化测试覆盖权限矩阵、检索、拒答、迁移（214 个用例）

后续重点：

* [ ] 分析剩余 Top1 Bad Case（约 5%，集中在跨条款综合类问题）
* [ ] 对比更强的 Embedding 与 Rerank 模型（bge-large / bge-m3）
* [ ] 将阈值标定固化为脚本，换模型后可一键重标
* [ ] 前端权限管理体验优化
* [ ] 部署流程与桌面打包流程完善

---

# 项目定位

该项目主要用于学习和实践企业级 AI 应用开发中的：

**RAG、Embedding、Vector Database、LLM API、FastAPI、RBAC、企业权限控制、数据库设计、检索评测和 AI 应用工程化。**

项目重点并非单纯调用大模型 API，而是尝试解决企业 AI 知识库实际落地过程中涉及的：

> **知识从哪里来、如何检索、谁可以访问、检索是否准确、如何评测以及如何避免越权访问。**

