# Seaf 侧开放接口文档

> 来源：360AI企业智能体知识库（张立增/葛长航/陈启明整理）
> 更新：2026-04-14

---

## 通用说明

- **基础 URL**：`http://11.123.255.179:30080`（开发环境）
- **认证方式**：`Authorization` header 传授权 KEY（双方约定）
- **通用 Header**：`Content-Type: application/json`

---

## 一、GUI 应用相关

### 1.1 GUI 应用创建 / 申请发布回调

QPaaS 创建 GUI 应用成功后通知 Seaf 创建对应 GUI Agent。

**请求**
```
POST /seaf/api/open/gui/create
```

**请求 Body**

| 参数 | 必选 | 类型 | 说明 |
|------|------|------|------|
| app_id | 否 | string | QPaaS 应用 ID，为空=新增，不为空且存在=更新 |
| app_name | 是 | string | GUI 应用名称 |
| app_code | 是 | string | GUI 应用编码（Seaf 和 QPaaS 两边一致） |
| app_desc | 是 | string | GUI 应用描述 |
| app_icon | 是 | string | GUI 应用图标 |
| operate_type | 是 | string | `SAVE`（保存）/ `DEPLOY_APPLY`（发布申请）/ `COPY`（复制）/ `TEMPLATE`（从模板创建） |
| preview_url | 是 | string | 只读跳转地址 |
| edit_url | 是 | string | 编辑跳转地址 |
| user_client_url | 否 | string | 用户端地址 |
| creator | 是 | string | 创建者 ID |
| version | 是 | string | 版本号，默认 `1.0` |
| agent_team_id | 是 | string | 从 agent 拉取的团队 ID |
| agent_team_name | 否 | string | 发布申请时有值 |
| copy_app_code | 否 | string | 复制操作时传入源编码 |
| version_mes | 否 | string | 发布申请时的版本说明 |
| remark | 否 | string | 发布申请时的备注 |
| label_id | 否 | int | 发布申请时的智能体分类 ID |
| public_type | 否 | int | 发布申请时：0=公司员工，1=本空间用户 |
| template_id | 否 | string | 从模板创建时透传的模板 ID |

**返回**
```json
{
  "errcode": 0,
  "errmsg": "success",
  "trans_id": "xxxxx",
  "data": {}
}
```

---

### 1.2 GUI 应用取消发布审核回调

QPaaS 取消发布审核后通知 Seaf。

**请求**
```
POST /seaf/api/open/gui/cancel_check
```

**Body 参数**

| 参数 | 必选 | 类型 | 说明 |
|------|------|------|------|
| app_code | 是 | string | GUI 应用编码（Seaf 和 QPaaS 两边一致） |
| user_id | 是 | string | 操作人用户 ID |
| team_id | 是 | string | 团队 ID |
| version | 是 | string | 版本号 |

**返回**
```json
{
  "errcode": 0,
  "errmsg": "success",
  "trans_id": "xxxxx",
  "data": {}
}
```

---

### 1.3 GUI 应用撤销发布

QPaaS 撤销发布后通知 Seaf。

**请求**
```
POST /seaf/api/open/gui/unpublish
```

**Body 参数**

| 参数 | 必选 | 类型 | 说明 |
|------|------|------|------|
| app_code | 是 | string | GUI 应用编码（Seaf 和 QPaaS 两边一致） |
| user_id | 是 | string | 操作人用户 ID |
| team_id | 是 | string | 团队 ID |
| version | 是 | string | 版本号 |

**返回**
```json
{
  "errcode": 0,
  "errmsg": "success",
  "trans_id": "xxxxx",
  "data": {}
}
```

---

## 二、用户信息接口

### 2.1 查询全部用户信息

构建组织架构用，分页返回，每页最多 200 条。

**请求**
```
GET /seaf/api/open/user/all
```

**Query 参数**

| 参数 | 必选 | 类型 | 说明 |
|------|------|------|------|
| cid | 否 | string | 组织 ID，不传默认租户 |
| page | 否 | string | 页码，默认第一页 |

**返回**
```json
{
  "errcode": "0",
  "errmsg": "成功",
  "totalCount": "10",
  "datas": [
    {
      "userid": "4563402818",
      "account": "帐号",
      "name": "昵称",
      "deptData": [
        {
          "did": "部门id",
          "name": "部门名称",
          "desp": "部门描述",
          "order": "部门排序",
          "sourceDid": "源部门ID"
        }
      ],
      "enName": "英文名",
      "gender": "1男0女",
      "sign": "签名",
      "email": "邮箱",
      "tel": "电话",
      "mobile": "手机",
      "status": "1正常0停用",
      "order": "人员在部门中的排序",
      "roleId": "角色id",
      "staffId": "工号",
      "posData": [
        {
          "did": "部门id",
          "posId": "职位id",
          "order": "职位排序",
          "posName": "职位名称"
        }
      ]
    }
  ]
}
```

---

### 2.2 批量查询用户

**请求**
```
POST /seaf/api/open/user/list
```

**Body 参数**

| 参数 | 必选 | 类型 | 说明 |
|------|------|------|------|
| ids | 否 | array | 用户 ID 列表，与 accounts 二选一，最多 100 条 |
| accounts | 否 | array | 用户 account 数组，与 ids 二选一，最多 100 条 |

**返回**：同全量查询，单个用户字段含 `avatarUrl`（头像 URL）。

---

### 2.3 查询用户详情

**请求**
```
GET /seaf/api/open/user/info
```

**Query 参数**

| 参数 | 必选 | 类型 | 说明 |
|------|------|------|------|
| id | 与 account 二选一 | string | 用户 ID |
| account | 否 | string | 用户 account |

**返回字段扩展**

- `user_source`：用户来源标识
- `roleId`：角色（5=超级管理员 / 10=管理员 / 20=部门管理员 / 30=普通成员）
- `extattr`：自定义字段列表
- `tagList`：标签列表（含第三方标签 ID）

---

## 三、部门信息接口

### 3.1 查询全部部门信息

**请求**
```
GET /seaf/api/open/dept/all
```

**Query 参数**

| 参数 | 必选 | 类型 | 说明 |
|------|------|------|------|
| cid | 否 | string | 组织 ID，不传默认租户 1 |
| page | 否 | string | 页码，默认第一页，每页最多 200 条 |

**返回**
```json
{
  "errcode": "0",
  "errmsg": "成功",
  "deptCount": "子部门总数",
  "pageCount": "总页数",
  "nextPage": "下一页号",
  "datas": [
    {
      "name": "部门名称",
      "desp": "部门描述",
      "did": "部门id",
      "order": "部门排序",
      "pid": "父部门ID"
    }
  ]
}
```

---

### 3.2 批量查询部门

**请求**
```
POST /seaf/api/open/dept/list
```

**Body 参数**

| 参数 | 必选 | 类型 | 说明 |
|------|------|------|------|
| ids | 是 | array | 部门 ID 列表 |
| cid | 否 | string | 组织 ID，不传默认租户 1 |

**返回**：字段含 `dept_source`（来源标识）、`tel`（部门电话）、`dept_group`（是否创建部门群）、`tagList`（标签列表）。

---

### 3.3 查询部门详情

**请求**
```
GET /seaf/api/open/dept/info
```

**Query 参数**

| 参数 | 必选 | 类型 | 说明 |
|------|------|------|------|
| id | 是 | string | 部门 ID |
| cid | 否 | string | 组织 ID，不传默认租户 1 |

**返回**
```json
{
  "errcode": "0",
  "errmsg": "成功",
  "did": "部门id",
  "name": "部门名称",
  "desp": "部门描述",
  "dept_source": "部门创建来源标识",
  "tel": "部门电话",
  "pid": "父部门id",
  "order": "部门排序",
  "dept_group": "是否创建部门群",
  "tagList": {
    "tagId": "标签id",
    "orgin_tagId": "第三方标签",
    "name": "标签名称"
  }
}
```

---

## 四、媒体文件接口

### 4.1 上传媒体文件

支持图片（jpg、png），单文件最大 2MB。

**请求**
```
POST /seaf/api/open/media/upload
Content-Type: multipart/form-data
```

**Form 参数**

| 参数 | 必选 | 说明 |
|------|------|------|
| type | 是 | 媒体类型：`image` |
| media | 是 | 文件内容，含 filename、filelength、content-type |

**返回**
```json
{
  "errcode": "0",
  "errmsg": "成功",
  "type": "image",
  "media_url": "媒体资源在平台的完整访问路径",
  "created_at": "1487585599"
}
```

---

## 五、认证接口

### 5.1 用户单点登录

QPaaS 侧跳转 Seaf 时携带 code + authorization，Seaf 返回用户信息完成 SSO。

**请求**
```
POST /seaf/api/open/get_user_info
```

**Body**

| 参数 | 必选 | 类型 | 说明 |
|------|------|------|------|
| source | 是 | string | 来源，固定为 `gui` |
| code | 是 | string | 随机数，取 URL query 参数 |
| authorization | 是 | string | 认证参数，取 URL query 参数 |

**返回**
```json
{
  "errcode": "0",
  "errmsg": "成功",
  "datas": {
    "userid": "17660905660342",
    "name": "abcabc",
    "account": "abcabc",
    "avatarUrl": ""
  }
}
```

---

## 六、MCP 相关

### 6.1 MCP 工具接口

#### 6.1.1 空间下 MCP 列表

**请求**
```
POST /api/mcp/list
```

**Body 参数**

| 参数 | 必选 | 类型 | 说明 |
|------|------|------|------|
| mcp_category | 否 | int | -1=全部；0=工具MCP；1=工作流MCP |

**返回**
```json
{
  "context": { "code": 0, "message": "OK" },
  "data": [
    {
      "id": 144,
      "user_id": 45313,
      "user_name": "liuguanyu1",
      "user_avatar": "",
      "team_id": 1635,
      "name": "工具mcp1",
      "detail": "工具mcp",
      "publish_status": 2,
      "images": "/privatization/apiIcon1.png",
      "create_time": "2025-07-30T15:43:41",
      "update_time": "2025-07-30T15:43:58",
      "is_auth": 2,
      "auth_type": 1,
      "mcp_config": "{ mcpServers: {...} }",
      "mcp_type": 1,
      "mcp_category": 0,
      "flow_id": 0,
      "template_check_status": 2,
      "publish_time": "2025-07-30T15:43:54",
      "is_top": 1
    }
  ],
  "pagination": { "total": 7, "page": 1, "page_size": 1 }
}
```

**新增返回字段**：`update_time`、`user_avatar`、`mcp_category`、`flow_id`、`pagination`

#### 6.1.2 工作流 MCP 发布

**请求**
```
POST /api/flow/v3/flow_mcp_public
```

**Body 参数**

| 参数 | 必选 | 类型 | 说明 |
|------|------|------|------|
| flow_id | 是 | string | 工作流 ID |
| tag_id | 是 | int | 标签 ID |

**返回**
```json
{
  "context": { "code": 0, "message": "OK" },
  "data": {
    "template_check_id": 3913
  }
}
```

---

## 七、评价相关

### 7.1 评价列表查询接口

**请求**
```
POST /api/remark/list
```

**Body 参数**

| 参数 | 必选 | 类型 | 说明 |
|------|------|------|------|
| agent_id | 否 | int | 智能体 ID |
| user_name | 否 | str | 用户名称模糊查询 |
| account | 否 | str | 账号 |
| remark | 否 | str | 反馈内容模糊查询 |
| remark_type | 否 | int | 反馈类型：1=建议，2=缺陷 |
| start_date | 否 | int | 反馈开始时间（时间戳，默认30天前） |
| end_date | 否 | int | 反馈结束时间（时间戳） |
| page | 否 | int | 页码，默认 1 |
| page_size | 否 | int | 每页数量，默认 20 |

**返回**
```json
{
  "context": { "code": 0, "message": "OK" },
  "data": [
    {
      "user_name": "岳克浩",
      "user_account": "yuekehao",
      "avatar": "",
      "score": "5",
      "remark_type": 1,
      "remark": "测试数据19",
      "images": "",
      "create_time": 1754649919
    }
  ],
  "pagination": { "total": 11, "page": 1, "page_size": 10 }
}
```

**新增返回字段**：`user_name`、`user_account`、`avatar`、`score`、`remark_type`、`remark`、`images`、`create_time`、`pagination`

### 7.2 点踩数据查询接口

#### 7.2.1 点赞数据查询

**请求**
```
POST /api/v2/agents/get_agent_like_remark
```

**Body 参数**

| 参数 | 必选 | 类型 | 说明 |
|------|------|------|------|
| agent_id | 是 | int | 智能体 ID |
| user_name | 否 | str | 用户名称模糊查询 |
| tag_ids | 否 | list | 标签 ID 列表 |
| remark_content | 否 | str | 反馈内容模糊查询 |
| start_date | 否 | int | 开始时间（时间戳，默认30天前） |
| end_date | 否 | int | 结束时间（时间戳） |
| page | 否 | int | 页码，默认 1 |
| page_size | 否 | int | 每页数量，默认 50 |

**返回**
```json
{
  "context": { "code": 0, "message": "OK" },
  "data": [
    {
      "agent_id": 2770,
      "user_account": "gelunbiya",
      "user_name": "aaa",
      "session_id": "1222",
      "message_id": "3333",
      "remark": "hhh",
      "images": "",
      "create_time": 1754536733,
      "update_time": 1754536733,
      "log_id": "",
      "tags_ids": "[7]",
      "tags_names": "[\"响应速度快\"]"
    }
  ],
  "pagination": { "total": 1, "page": 1, "page_size": 50 }
}
```

#### 7.2.2 点踩数据查询

**请求**
```
POST /api/v2/agents/get_agent_unlike_remark
```

**参数同 7.2.1**，返回结构一致。

#### 7.2.3 点赞数据导出

```
POST /api/v2/agents/export_agent_like_remark
```

参数同 7.2.1（不含分页参数）。返回流式 Excel 文件。

#### 7.2.4 点踩数据导出

```
POST /api/v2/agents/export_agent_unlike_remark
```

参数同 7.2.1（不含分页参数）。返回流式 Excel 文件。

#### 7.2.5 点赞标签查询

```
GET /api/v2/agents/get_agent_like_remark_tags?agent_id=2222
```

**Query 参数**：`agent_id`（必填）

**返回**
```json
{
  "context": { "code": 0, "message": "OK" },
  "data": [
    { "tag_id": 58, "tag_name": "互动体验友好" },
    { "tag_id": 57, "tag_name": "响应速度快" }
  ]
}
```

#### 7.2.6 点踩标签查询

```
GET /api/v2/agents/get_agent_dislike_remark_tags?agent_id=2222
```

**参数同 7.2.5**，返回结构一致（标签内容为差评类，如"响应速度慢"、"答非所问"）。

---

## 八、运营数据

### 8.1 运营数据接口

#### 8.1.1 调用人数统计

按日期/时间维度返回智能体调用人数。

**请求**
```
GET /api/v2/agent/report/call_person_statistics
```

**Query 参数**

| 参数 | 必选 | 类型 | 说明 |
|------|------|------|------|
| agent_id | 是 | int | 智能体 ID |
| channel | 否 | str | 渠道 |
| start_time | 是 | str | 开始时间，格式 `YYYY-MM-DD HH:mm:ss` |
| end_time | 是 | str | 结束时间，格式 `YYYY-MM-DD HH:mm:ss` |

> 特殊逻辑：时间范围超过一个月时按月返回，小于一天时按小时返回。

**返回**
```json
{
  "context": { "code": 0, "message": "OK" },
  "data": {
    "x_axis": ["2025-08-17", "2025-08-16", "2025-08-15"],
    "series": [0, 0, 1]
  }
}
```

---

## 九、知识库

### 9.1 GUI 侧获取智能体分类列表

QPaaS 查询 Seaf 侧的智能体分类列表。

**请求**
```
GET /seaf/api/open/gui/agent_category
```

**返回**
```json
{
  "errcode": 0,
  "err_msg": "success",
  "trans_id": "xxxxx",
  "datas": {
    "categories": [
      {
        "id": 1,
        "name": "分类1",
        "desc": "分类1的描述",
        "sort": 0
      }
    ]
  }
}
```

### 9.2 [Deprecated] GUI 侧获取标签列表

> ⚠️ 已废弃，仅保留供参考。

**请求**
```
GET /seaf/api/open/gui/tags
```

**Query 参数**

| 参数 | 必选 | 类型 | 说明 |
|------|------|------|------|
| tag_type | 是 | int | 标签类型，固定为 `25`（发布渠道标签） |

**返回**
```json
{
  "errcode": 0,
  "err_msg": "success",
  "trans_id": "xxxxx",
  "datas": {
    "tags": [
      { "id": 1, "name": "标签1", "sort": 0 }
    ]
  }
}
```

### 9.3 按空间获取知识库数据集

> （文档待补充）

### 9.4 按数据集获取知识库列表

> （文档待补充）

---

## 十、管理后台接口

### 10.1 查询管理后台 AI 配置

> （文档待补充）

### 10.2 管理端给构建侧交互接口

> （文档待补充）

### 10.3 查询全部租户信息

> （文档待补充）

---

## 接口状态总览

| 接口 | 状态 |
|------|------|
| GUI应用创建/申请发布回调 | ✅ 已获取 |
| GUI应用取消发布审核回调 | ✅ 已获取 |
| GUI应用撤销发布 | ✅ 已获取 |
| 查询全部用户信息 | ✅ 已获取 |
| 批量查询用户接口 | ✅ 已获取 |
| 查询用户详情 | ✅ 已获取 |
| 查询全部部门信息 | ✅ 已获取 |
| 批量查询部门信息 | ✅ 已获取 |
| 查询部门详情 | ✅ 已获取 |
| 上传媒体文件 | ✅ 已获取 |
| 用户单点登录 | ✅ 已获取 |
| MCP工具接口 | ✅ 已获取 |
| 评价列表查询接口 | ✅ 已获取 |
| 点踩数据查询接口 | ✅ 已获取 |
| 运营数据接口 | ✅ 已获取 |
| GUI侧获取智能体分类列表 | ✅ 已获取 |
| 按空间获取知识库数据集 | ⏳ 待补充 |
| 按数据集获取知识库列表 | ⏳ 待补充 |
| 查询管理后台AI配置 | ⏳ 待补充 |
| 管理端给构建侧交互接口 | ⏳ 待补充 |
| 查询全部租户信息 | ⏳ 待补充 |

---

*最后更新：2026-04-14*
