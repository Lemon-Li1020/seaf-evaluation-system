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

> （文档待补充）

---

### 1.3 GUI 应用撤销发布

> （文档待补充）

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

> （文档待补充）

---

## 六、MCP 相关

### 6.1 MCP 工具接口

> （文档待补充）

---

## 七、评价相关

### 7.1 评价列表查询接口

> （文档待补充）

### 7.2 点踩数据查询接口

> （文档待补充）

---

## 八、运营数据

### 8.1 运营数据接口

> （文档待补充）

---

## 九、知识库

### 9.1 GUI 侧获取智能体分类列表

> （文档待补充）

### 9.2 按空间获取知识库数据集

> （文档待补充）

### 9.3 按数据集获取知识库列表

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
| GUI应用取消发布审核回调 | ⏳ 待补充 |
| GUI应用撤销发布 | ⏳ 待补充 |
| 查询全部用户信息 | ✅ 已获取 |
| 批量查询用户接口 | ✅ 已获取 |
| 查询用户详情 | ✅ 已获取 |
| 查询全部部门信息 | ✅ 已获取 |
| 批量查询部门信息 | ✅ 已获取 |
| 查询部门详情 | ✅ 已获取 |
| 上传媒体文件 | ✅ 已获取 |
| 用户单点登录 | ⏳ 待补充 |
| MCP工具接口 | ⏳ 待补充 |
| 评价列表查询接口 | ⏳ 待补充 |
| 点踩数据查询接口 | ⏳ 待补充 |
| 运营数据接口 | ⏳ 待补充 |
| GUI侧获取智能体分类列表 | ⏳ 待补充 |
| 按空间获取知识库数据集 | ⏳ 待补充 |
| 按数据集获取知识库列表 | ⏳ 待补充 |
| 查询管理后台AI配置 | ⏳ 待补充 |
| 管理端给构建侧交互接口 | ⏳ 待补充 |
| 查询全部租户信息 | ⏳ 待补充 |

---

*最后更新：2026-04-14*
