# Seaf 各版本提测变更总览

> 来源：360AI企业智能体知识库（孙强/李雪整理）
> 更新：2026-04-14

---

## 版本时间线

| 版本 | 日期 | 主要内容 |
|------|------|---------|
| 0731 | 2025-07-31 | 无相关信息 |
| 0815 | 2025-08-15 | 模型管理、精选智能体、统计表、智能体评价、评测数据 |
| 0831 | 2025-08-31 | 自定义分组、资源空间关系表、MCP审核、引擎地址变更 |
| 0915 | 2025-09-15 | 提示词模板、智能体模板、超级智能体、S3存储配置 |
| 0923 | 2025-09-23 | _待补充_ |
| 1030 | 2025-10-30 | GUI接入、端口收敛(/gui、/bees)、蜂群配置、小引擎配置、语音输入 |
| 1130 | 2025-11-30 | AI策略配置表、资源可见性表、L2智能体接入、流式代理 |
| V1.2.0.0115 | 2026-01-15 | 浏览器360发布、Runtime包管理(7张表)、多渠道发布 |
| V1.2.1.0210 | 2026-02-10 | 多租户(cid)、操作日志体系(4张表)、MCP管理后台 |
| V3.0.5.0312 | 2026-03-12 | 磁盘清理规则、界面UI配置、安全智能体、租户管理 |
| **V3.0.6.0510** | **2026-05-10** | **存储收敛(统一中间件)、VI界面配置** |

---

## 一、0815 版本（2025-08-15）

### 1.1 新增表

| 表名 | 用途 |
|------|------|
| `model_info` | 模型信息表（供应商、名称、地址、密钥、能力、参数） |
| `t_top_pick_agents` | 精选智能体 |
| `t_agent_stat` | 智能体数据统计（活跃用户、点击、算力消耗） |
| `t_user_stat_month` | 用户活跃数月度统计 |
| `t_user_stat_summary` | 用户日维度统计（工作流/工具MCP/知识库/提示词调用） |
| `t_token_stat` | Token消耗日维度统计 |
| `t_agent_stat_summary` | 智能体数据整体统计 |
| `t_user_agent_stat` | 用户×智能体使用统计（次数、时长、采纳数，按日） |
| `t_agent_msg_remark` | 智能体消息点赞点踩表 |
| `t_agent_msg_tag` | 点赞/点踩关联的标签 |
| `t_agent_remark` | 智能体整体评分评价表 |
| `evaluation_dimension` | 评测维度 |
| `evaluation_set` | 评测集 |
| `evaluation_set_case` | 评测集问答列表 |
| `evaluation_task` | 评测任务 |
| `evaluation_task_case_result` | 评测任务执行结果 |
| `evaluation_task_case_score` | 评测任务评分 |

### 1.2 评价标签

- **好评标签**（tag_type=23）：准确有效、回答全面、简明易懂、内容权威可信、响应速度快、互动体验友好
- **差评标签**（tag_type=24）：答非所问、回答不完整、表述模糊、内容缺乏可信度、响应速度慢、互动体验不佳

### 1.3 其他变更

- `team.team_desc` 扩容至 512
- `team_audit.application_information` 扩容至 512
- `application_flow_relation` 增加 `agent_id` 字段
- 新增 `third_party_platforms` 第三方平台配置（QPaaS）
- 新增 casbin 权限规则（构建侧查询评价列表）

### 1.4 配置变更

- QPaaS token 获取地址：`http://11.43.182.93/api/api-uaa/oauth/app/token`

---

## 二、0831 版本（2025-08-31）

### 2.1 新增/变更表

| 表名 | 变更类型 | 说明 |
|------|---------|------|
| `t_user_collection` | 新增 | 收藏智能体分组（分组名、创建人、排序） |
| `t_user_agent_collection` | 变更 | 增加 `collection_id` 和 `location` 字段 |
| `t_resource_team` | 新增 | 资源使用空间关系表（mcp/知识库/apimcp与团队关系） |
| `action_chain_flow_version` | 变更 | 增加审核相关字段（`template_check_id`、`template_check_status`） |
| `team_template_check` | 变更 | 增加 `submit_remark`（提交说明）和 `down_remark`（下架原因） |
| `channels` | 变更 | 默认渠道名改为 `SeaFactory`（原来未知名） |

### 2.2 配置变更

- 新引擎地址：`NEW_AGENTRUNNER_URL` → `http://11.123.125.102:3004/api`

---

## 三、0915 版本（2025-09-15）

### 3.1 新增/变更表

| 表名 | 变更类型 | 说明 |
|------|---------|------|
| `agent_prompt_tpl` | 新增 | 提示词模板表 |
| `t_agent_template` | 新增 | 智能体模板表 |
| `t_prompt_tpl_log` | 新增 | 提示词模板操作记录表 |
| `agent` | 变更 | 增加 `qpaas_app_code`（GUI应用对应QPaas侧应用编码） |
| `agent_history` | 变更 | 同上 |

### 3.2 超级智能体

- 新增系统智能体 ID=1，名称"超级智能体"
- 配置路径：`docker/config/agent_config.json`
- 内部API：`go_internal_api` = `http://11.123.252.212:25710`
- 认证Token：`go_internal_auth_token` = `SR6B310fsir2pGnAQ8iG3oT4J2iR3xJd`

### 3.3 配置变更

- S3 存储：`s3Url` = `http://agent-minio:9000`，AK=`admin`，SK=`admin123456`

### 3.4 执行脚本

无

---

## 四、0923 版本（2025-09-23）

### 4.1 核心主题：超级智能体激活

**字段变更**：

| 表名 | 变更 |
|------|------|
| `agent` | 增加 `is_super`（1=超级智能体） |
| `agent_history` | 增加 `is_super` |
| `agent_channel` | 增加 `is_super` |

**插入超级智能体记录**：
- `agent_history` 插入超级智能体记录（id=1）
- `agent_channel` 插入超级智能体渠道记录（`agent_history_id=804`）
- 超级智能体 prompt：`##角色设定##\n你是一个超级智能体\n##回答方式##...`

### 4.2 配置变更

**agent-web-backend**：
- s3 新增 `external_url` = `http://11.123.255.179:9000`

**global 新增**：
- `L4_AGENTRUNNER_URL` = `http://11.123.255.179:5001`
- `go_internal_api` = `http://11.123.255.179:25710`
- `go_internal_auth_token` = `SR6B310fsir2pGnAQ8iG3oT4J2iR3xJd`
- `super_agent.greeting_message` = `您好，%s`

**agents（application.toml）**：
- `deploymentUrl` = `http://11.123.255.179:30080/api`

### 4.3 执行脚本

需将图片 `pic_super_agent.png` 上传至各环境 MinIO：
- 地址：`http://11.123.255.179:9001/`
- 路径：`teamprivkey/pic_super_agent.png`
- 账号：`admin` / 密码：`admin123456`

---

## 五、1030 版本（2025-10-30）

### 4.1 核心主题：GUI 接入 & 端口收敛

**新增/变更表**：

| 表名 | 变更类型 | 说明 |
|------|---------|------|
| `evaluation_task_case_result` | 变更 | 增加 `tokens` 字段（消耗token数） |
| `agent.prompt` | 变更 | 改为 MEDIUMTEXT |
| `agent_history.prompt` | 变更 | 改为 MEDIUMTEXT |
| `agent.agent_type` | 变更 | 增加枚举：1=自主对话、2=GUI智能应用、3=Multi智能体、4=异构智能体 |
| `agent_history.agent_type` | 变更 | 同上 |
| `t_user_collection` | 新增 | 收藏智能体分组表（0831已列，此处补充） |
| `t_user_agent_collection` | 变更 | 增加 `collection_id` 和 `location` 字段 |
| `agent_prompt_tpl.content` | 变更 | 改为 LONGTEXT |
| `action_chain_flow_publish_agent`（agent_nami库） | 变更 | 增加 `ui_mcp_data` 字段 |
| `t_agent_visible.visible_scope` | 变更 | 扩容至 16000 字符 |

### 4.2 配置变更

**Nginx 新增代理路径**：
- `/bees` → 蜂群服务
- `/gui` → QPaaS GUI 服务
- `/gui/ai-web-seaf` → GUI 业务路径

**agents 服务配置**：`guiAddr` = `https://seaf.360.cn:30080`

**agent-web-backend 配置**：
- `qpass_domain` = `https://seaf.360.cn:30080/gui`
- QPaaS token 地址改为 `/gui/api/api-uaa/oauth/app/token`

**蜂群配置**：
- `l4_agent.web_host` = `https://seaf.360.cn:30080/bees`
- 关键词映射（模式名称中文化）：`simpleact模式`→`极速执行模式`、`orchestrator模式`→`调度决策模式`等

### 4.3 小引擎配置

- `CUSTOM_UI_HOST` = `http://nami-backend:8000`（卡片列表）
- `GENERATE_HTML_HOST` = `http://gui-mcp:3000`（HTML卡片生成）
- `MCP_ENHANCER_HOST` = `http://gui-mcp:3000`
- `KNOWLEDGE_API_HOST` = `http://11.123.254.218:30082`

### 4.4 GUI MCP 配置

- `TENANT_API_BASE_URL_OVERRIDE` = `https://seaf.360.cn:30080/bees`
- 需将 `easy-render.global.js` 上传至 S3

### 4.5 涉及服务

agent-go、agent-web、agent-api、GUI QPaaS、小引擎、蜂群前后端、seafUser、seafManagement、GUI MCP、agent-mcp-server

---

## 六、1130 版本（2025-11-30）

### 5.1 新增表

| 表名 | 说明 |
|------|------|
| `t_ai_policy_config` | AI策略配置表（智能体/MCP内部可见自动审核、智能体撤销权限） |
| `t_resource_visible` | 资源可见性关系表（mcp/知识库/工具mcp/apimcp 的可见范围） |

### 5.2 字段变更

| 表名 | 变更 |
|------|------|
| `team_template_check` | 增加 `visible_scope`（可见性字段） |
| `agent_history` | 增加 `updated_user_id`（更新人id，撤销发布时记录） |
| `agent` | 增加 `extra_info`（异构智能体配置信息） |
| `agent_chat_session` | 增加 `third_conversation_id`（第三方平台会话ID） |
| `prompt_tags` | 新增 tag_type=28：Coze、Dify |

### 5.3 配置变更

**小引擎轮询配置**：
- `POLL_INTERVAL` = 100ms
- `POLL_MAX_ATTEMPTS` = 18000（约30分钟超时）

**模型配置**：`model_template_*.yaml` 中 `input_modal` 扩展为 text/image/audio/video

**L2 智能体配置**：
- `host` = `http://11.121.244.80:8099`
- `web_host` = `http://11.123.255.179:30080/l2`

**蜂群配置**：
- `flow_continue_url` = `http://11.123.121.48:3005`（小引擎服务）
- `graph_runner_url_v2` = `http://11.123.252.212:5001`（大引擎）

**Nginx**：新增流式代理 `/api/v2/agents/ai_stream_system_prompt` 和 `/api/v2/chat/l2_ask_with_session`

### 5.4 执行脚本

- 历史MCP可见性初始化：`./bin/agents -conf=config/application.toml -init-mcp-visible`
- Redis清理：`redis-cli` 5号库清理 `user*` 相关key

---

## 七、V1.2.0.0115 版本（2026-01-15）

### 4.1 新增表

| 表名 | 说明 |
|------|------|
| `agent_browser_360` | 浏览器360发布记录（agent_id、app_id、展示方式1侧边栏/2弹框/3全屏） |
| `t_runtime_package` | Runtime包主表（客户名、创建者、智能体/模型/MCP/插件/知识库计数） |
| `t_runtime_package_plugin` | Runtime包-插件配置 |
| `t_runtime_package_model` | Runtime包-模型配置 |
| `t_runtime_package_mcp` | Runtime包-MCP配置（含openapi_spec字段） |
| `t_runtime_package_knowledge` | Runtime包-知识库配置 |
| `t_runtime_package_agent` | Runtime包-智能体关联表（含版本快照ID） |
| `t_runtime_resource_mapping` | Runtime资源映射表（运营平台↔Runtime平台资源ID映射） |
| `publish_channel` | 发布渠道表 |

### 4.2 字段变更

| 表名 | 变更 |
|------|------|
| `mcp` | 增加 `openapi_spec`（JSON/YAML格式，仅 api转mcp 时使用） |
| `agent_iframe` | 增加 `creator_uid` |
| `agent_api_auth` | 增加 `creator_id`、`ip_whitelist`、`permissions`、`last_used_at` |
| `agent.name` | 扩容至 100 字符 |
| `agent_history.name` | 扩容至 100 字符 |
| `t_agent_template.template_desc` | 扩容至 1024 |
| `chain_flow_access.inputs` | 改为 longtext |
| `agent` | 增加 `public_access`（0-非公开，1-公开） |
| `t_agent_visible.visible_scope` | 改为 text |
| `t_user_stat_summary` | 字段扩容 |

### 4.3 配置变更

- 浏览器360：`browser_360.domain`（上线前需协调正式环境KEY）
- agents 服务：超时改为 60s，信任代理 IP `172.22.0.1`
- L2 配置：`l2WebHost`、`l2AppId`、`L2Secret`
- L4 蜂群：`l4Addr`、`l4AppId`、`L4Secret`
- 发布渠道：`publishChannel`（360AI企业浏览器，app_id=`1268adcb73b6d740`）

---

## 八、V1.2.1.0210 版本（2026-02-10）

### 5.1 核心主题：多租户（cid）

**几乎所有主要表都增加了 `cid` 字段**，这是本期最大变更：

已确认增加 `cid bigint unsigned default 1` 的表：
`team`、`team_audit`、`team_template_check`、`t_resource_visible`、`t_resource_team`、`t_runtime_package`（及其子表）、`t_agent_visible`、`t_agent_template`、`t_agent_stat_summary`、`model`、`category_relation`、`category`、`publish_channel`、`t_corp`、`t_agent_log`、`prompt_user`、`prompt`、`mcp_version`、`mcp`、`knowledge_data`、`agent`、`agent_channel`、`prompt_tags`、`team_member_role`、`agent_prompt_tpl`、`t_prompt_tpl_log`、`agent_api_auth`

### 5.2 操作日志体系（4张核心表）

| 表名 | 说明 |
|------|------|
| `operation_log_module` | 操作日志模块表（30+模块：MCP发布、发布渠道、工作记录、我的助手...） |
| `operation_log_type` | 操作日志类型表（100+类型：创建、编辑、发布、删除...） |
| `operation_log_template` | 操作日志模板配置表（平台×模块×类型 → 详情模板） |
| `operation_log_template_param` | 操作日志模板参数表（枚举值/文本参数） |
| `operation_log` | 操作日志实际记录表 |

**平台分布**：
- platform_id=1：运营平台
- platform_id=2：构建平台
- platform_id=3：用户平台
- platform_id=4：租户管理平台

### 5.3 其他重要变更

- `t_corp`：增加 `agent_num`（智能体创建数）、`agent_max_num`（智能体分配数）、`expire_time`（到期时间）、`admin_uid`（系统管理员uid）
- `model_info`：增加 `is_removed`（是否删除）、`display_name`（显示名）
- `t_runtime_package_model`：增加 `display_name`
- `agent_api_auth`：增加 `cid`、`auth_type`（1-agent/2-system/3-tenant）
- `t_ai_policy_config`：增加 `space_whitelist`、`space_wl_enabled`
- `category`：增加 `is_default`
- 新增 `t_disk_clean_rule`（磁盘清理规则：系统日志7天/API日志30天/用户日志180天/评测365天/工作记录730天）
- MongoDB：`agent_version_info` 和 `agent_openapi_call_log` 增加 cid 字段

---

## 九、V3.0.5.0312 版本（2026-03-12）

### 6.1 新增表

| 表名 | 说明 |
|------|------|
| `system_ui_config` | 界面资源配置宽表（common/operation/build/user/runtime 五个模块的图标、Logo、标题、配色） |

### 6.2 其他变更

- 新增分类"安全工作流智能体"（category id=200）
- `model_info.model_desc` 扩容至 1024
- `publish_channel`：增加 `identifier`（渠道标识，默认=`360browser`），默认状态改为关闭
- `t_runtime_package_model`：增加 `display_name`

### 6.3 配置变更

- 安全智能体：`safety_agent_host` = `https://dev-saas.secgpt.360zqaq.net`
- 纳米引擎：`NAMI_AGENTRUNNER_URL` = `http://agentrunner-level4:5001`
- seaf-agents：安全智能体配置 + `channel_identifier` = `360browser`

---

## 十、V3.0.6.0510 版本（2026-05-10）⭐本期

### 7.1 核心主题：存储收敛

**各业务统一使用 ABOP 的存储中间件，版本定义如下**：

| 组件 | 版本 | 业务方 | 说明 |
|------|------|--------|------|
| MySQL | 8.4.3 | ABOP、API2MCP、QPAAS GUI、知识库 | ABOP需从7.4.2降至7.2 |
| MongoDB | 4.4.29 | ABOP、API2MCP | |
| Redis | 7.2 | ABOP、API2MCP、QPAAS GUI、知识库 | ABOP从7.4.2降至7.2 |
| ElasticSearch | 8.17.0 | 知识库 | 向量召回 |
| ETCD | 3.5.16 | API2MCP | 服务注册发现 |
| NACOS | 2.4.3.1 | QPAAS GUI | 配置管理 |
| RabbitMQ | 3.7.26 | QPAAS GUI | 消息队列 |
| MinIO | 2024-11-21 | ABOP、知识库 | 对象存储 |

**Redis DB号分配**：
- 5号DB：ABOP
- 3号DB：API2MCP
- 0号DB：知识库
- 1号DB：语音输入
- 2号DB：QPAAS GUI

> ⚠️ 本期若赶不上，则 v3.0.7 必须实现（且存量版本升级时也要实现）

### 7.2 VI需求

- `system_ui_config` 表中插入 5 个模块的初始化配置：common、operation、build、user、runtime

### 7.3 Redis 降级脚本

1. 老 Redis 执行 `bgsave`
2. 创建新版本 Redis，使用 `redis-migrate` 工具迁移
3. 配置文件 `config.yaml` 填写新老 IP、端口、密码
4. 迁移完成后修改新 Redis 名字

---

## 十一、测试关注点汇总

### 8.1 跨版本重点

1. **多租户（cid）**：几乎所有表都加了 cid，测试时注意租户隔离
2. **操作日志**：4张表的日志体系，覆盖30+模块、100+操作类型，上线后需验证各操作是否正确落库
3. **Runtime包导入导出**：涉及智能体、模型、MCP、插件、知识库的全量打包，注意关联数据完整性
4. **存储收敛**：Redis DB 号分配、各组件版本统一，跨业务调用时注意连接配置

### 8.2 各版本特色测试点

- **0815**：评价功能（点赞/点踩/标签）、评测任务全流程（创建维度→建评测集→跑任务→评分）
- **0831**：智能体分组收藏、MCP审核流程
- **0915**：超级智能体调用、S3文件上传
- **V1.2.0.0115**：浏览器360发布、Runtime包打包/导入、公开访问
- **V1.2.1.0210**：操作日志完整性和准确性、租户创建/切换/到期
- **V3.0.5.0312**：界面UI定制（各模块Logo/配色/标题）、安全智能体
- **V3.0.6.0510**：Redis降级后的业务连续性、存储中间件连接配置

---

*最后更新：2026-04-14（补充1030、1130版本）*

## V3.0.7.0510-dev (2026-04-20)

### 新增

- **评测系统设计文档**（完整版）
  - `docs/agent-evaluation-system-requirements.md` — 完整需求规格说明书（推理+编排+工作流三大类型）
  - `docs/agent-evaluation-system-requirements-mvp.md` — MVP版需求规格说明书
  - `docs/requirement-evaluation-v2.md` — 评测系统需求V2
  - `design/evaluation-system/01-architecture.md` — 总体技术方案
  - `design/evaluation-system/02-database.md` — 数据库设计（含编排类型表结构）
  - `design/evaluation-system/03-api.md` — RESTful API 接口设计（含编排类型API）
  - `design/evaluation-system/04-evaluator.md` — 评测器设计（推理+工作流）
  - `design/evaluation-system/05-llm-judge.md` — LLM 评委服务设计（含置信度机制）
  - `design/evaluation-system/06-celery-tasks.md` — 异步任务设计
  - `design/evaluation-system/07-orchestration-evaluator.md` — **编排评测器设计（新增）**
  - `design/evaluation-system/08-seaf-interface-contract.md` — **Seaf 外部接口契约（新增）**
  - `docs/llm-judge-prompts.md` — LLM 评委 Prompt 合集

- **评测集数据**
  - `docs/evaluation-dataset-reasoning.json` — 推理评测集（10题）
  - `docs/evaluation-dataset-swarm.json` — 蜂群评测集（5题）
  - `docs/evaluation-dataset-workflow.json` — 工作流评测集（6题）

- **评测框架**
  - `docs/agent-evaluation-framework.md` — 评测体系总览与路线图

### 完善

- LLM 评委 Prompt 补充置信度（confidence）和 needs_human_review 字段
- 响应解析逻辑补充置信度解析
- 需求文档补充置信度完整处理链路
- 数据库 test_case 表字段从 TEXT 升级为 JSONB（expected_tools / expected_nodes / expected_sub_agents 等）
- agent_type CHECK 约束扩展支持 orchestration 类型
- evaluation_config 表初始化数据扩展编排智能体配置
- API 文档 agent_type 参数说明扩展编排类型
- API 文档补充编排类型评测项请求示例
- README.md 索引文档更新（新增 07、08）
- 评测结果上报结构补充 needs_review_count 和 confidence_distribution

### 已知缺口

- Seaf 编排智能体需支持 `include_call_chain=true` 参数（接口契约文档已定义）
