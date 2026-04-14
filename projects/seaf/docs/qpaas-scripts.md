# QPaaS GUI 侧部署脚本

> 来源：360AI企业智能体知识库（张立增/陈建波等整理）
> 更新：2025-10 至 2026-03

---

## feat:700199 - QPaaS GUI 端口合并修改

> 将 QPaaS GUI 接入 Seaf 统一域名（/gui、/bees 前缀）

### 1. 升级脚本

```sql
-- xxl-job 地址添加 gui 前缀
UPDATE qpaas_nacos.config_info SET content = REPLACE(content,
  'http://service.qpaas.qihoo.net/job',
  'http://service.qpaas.qihoo.net/gui/job')
WHERE data_id='nacos-config-demo.properties';

-- 更新菜单路径
UPDATE qpaas_system.sys_menu SET PARAMS_='/gui/job/' WHERE MENU_ID_='1254981434737713153';
UPDATE qpaas_system.sys_menu SET PARAMS_='/gui/job/jobinfo' WHERE MENU_ID_='1255012367289311233';
UPDATE qpaas_system.sys_menu SET PARAMS_='/gui/job/joblog' WHERE MENU_ID_='1255012498449391618';
UPDATE qpaas_system.sys_menu SET PARAMS_='/gui/job/jobgroup' WHERE MENU_ID_='1255012627294216194';
UPDATE qpaas_system.sys_menu SET PARAMS_='/gui/job/user' WHERE MENU_ID_='1420924834176888834';

-- 更新 Seaf 访问地址（替换为实际 IP/域名）
UPDATE sys_auth_manager SET
  APP_WEB_URL_='http://11.123.255.179:30080',
  APP_PC_URL_='http://11.123.255.179:30080',
  APP_MOBILE_URL_='http://11.123.255.179:30080'
WHERE ID_='100000001';
```

### 2. Nginx 配置（vhost-qpaas-web.conf）

```nginx
location /gui/ai-web-seaf {
    alias /u01/programs/front/qpaas-ai-web-seaf;
    index index.html;
    try_files $uri $uri /gui/ai-web-seaf/index.html;
}

location /gui {
    alias /u01/programs/front/qpaas-web-all/;
    index index.html;
    try_files $uri $uri/ /gui/index.html;
}

location /gui/api/ {
    proxy_set_header Host $host:$server_port;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_pass http://qpaas-gateway-balance-upstream/;
}

location /gui/job {
    proxy_pass http://qpaas-job-balance-upstream/gui/job;
}
```

### 3. 部署项目

- qpaas-job（新部署）
- qpaas-system（新部署）
- 重启 user-job

---

## feat:708605 - 加入 OnlyOffice 服务

### Nginx 配置

```nginx
location /onlyoffice/ {
    if ($request_uri ~ /onlyoffice/(.+)) {
        set $rightUrl $1;
    }
    proxy_pass http://11.121.244.30:30756/$rightUrl;
    proxy_set_header Host $host:30080;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /web-apps/ {
    proxy_pass http://11.121.244.30:30756;
}

location ~ ^/(7.4.0-0|8.1.0-169)/ {
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_pass http://11.121.244.30:30756;
}

location /cache/files/ {
    proxy_pass http://11.121.244.30:30756;
}
```

QPaaS 侧追加文件下载配置：
```nginx
location ^~ /gui/download/anony {
    alias /u01/upload/anony;
    if ($arg_filename) {
        add_header Content-Disposition 'attachment; filename="$arg_filename"';
    }
    add_header Cache-Control "no-cache, no-store, must-revalidate";
    add_header Pragma "no-cache";
    add_header Expires "0";
}
```

---

## feat:712885 - GUI 添加版本控制

### 新增表

```sql
-- qpaas_portal 库
CREATE TABLE qpaas_portal.ins_intelligent_def_version (
    ID_ VARCHAR(64),           -- 主键
    DEF_ID_ VARCHAR(64),       -- 智能定义ID
    KEY_ VARCHAR(64),          -- key
    NAME_ VARCHAR(128),        -- 名称
    EXT_ LONGTEXT,             -- 页眉/数据结构JSON
    TYPE_ VARCHAR(10),
    APP_CODE_ VARCHAR(64),     -- 应用编码
    FLOW_CONF_MES_ TEXT,       -- 技能配置信息
    VERSION_ VARCHAR(64),       -- 版本号
    VERSION_MSG_ VARCHAR(500),  -- 版本信息
    VIEW_TYPE_ INT DEFAULT 0,   -- 可见范围：0=公司员工，1=本空间成员
    IS_AUTO_PUBLISH_ INT DEFAULT 0,  -- 是否自动免审发布
    AUTH_ TEXT,                -- 权限信息
    DEPLOY_STATUS_ VARCHAR(64) DEFAULT 'UNPUBLISHED',  -- 发布状态
    PUBLISH_LABEL_ID_ VARCHAR(50),
    AUDIT_MES_ VARCHAR(500),
    PUBLISH_USER_ID_ VARCHAR(64),  -- 发布人seaf侧id
    AUDIT_USER_ID_ VARCHAR(64),   -- 审核人seaf侧id
    REMARK_ VARCHAR(500),
    SN_ INT DEFAULT 1,
    TENANT_ID_ VARCHAR(64),
    CREATE_DEP_ID_ VARCHAR(64),
    CREATE_BY_ VARCHAR(64),
    CREATE_TIME_ datetime,
    UPDATE_BY_ VARCHAR(64),
    UPDATE_TIME_ datetime,
    PRIMARY KEY (ID_),
    KEY def_app_code_index (APP_CODE_)
);
```

### 接口权限脚本

```sql
INSERT INTO sys_interface_api VALUES
  ('1985906463594180610','保存文件', ...),
  ('1996195769516716033','运用基础信息', ...),
  ('1996192328732012546','知识库文件列表', ...),
  ('1996192240722931714','知识库数据集', ...),
  ('1996192138402885633','发布版本列表', ...),
  ('1996192040008708098','删除版本', ...),
  ('1996522527638102018','查询智能运用', ...);

-- 扩容请求体字段
ALTER TABLE qpaas_system.sys_interface_call_logs MODIFY REQUEST_BODY_ LONGTEXT;
```

### 部署项目

- qpaas-web-all（需部署）
- qpaas-auth、qpaas-system、qpaas-user、qpaas-user-job（需部署）

---

## feat:729282 - GUI 存为模板提供数据

### 接口权限

```sql
-- 获取GUI数据
INSERT INTO sys_auth_interface VALUES (..., '/restApi/sys/intelligentAppManage/getGuiData', ...);

-- GUI应用从模板创建
INSERT INTO sys_auth_interface VALUES (..., '/restApi/sys/intelligentAppManage/createFromTemplate', ...);

-- 导入gui运用
INSERT INTO sys_auth_interface VALUES (..., '/restApi/sys/intelligentAppManage/importGui', ...);

-- 发布版本
INSERT INTO sys_auth_interface VALUES (..., '/restApi/sys/intelligentAppManage/deployVersion', ...);

-- 更新版本状态
INSERT INTO sys_auth_interface VALUES (..., '/restApi/sys/intelligentAppManage/updateVersionStatus', ...);
```

### L2 智能体项目配置

```sql
-- L2智能体(非测试勿删勿改)
INSERT INTO sys_interface_project (PROJECT_ID_, PROJECT_NAME_, PROTOCOL_DOMAIN_NAME_, ...)
VALUES ('2001478844073021442', 'L2智能体(非测试勿删勿改)',
  'http://11.123.255.179:30080', ...);

-- L2智能体参数信息接口
INSERT INTO sys_interface (INTERFACE_ID_, INTERFACE_NAME_, RESTFUL_REQUEST_URL_, ...)
VALUES ('2001481183886479361', 'L2智能体参数信息',
  '/inner_flow/flow_params/{template_id}', 'GET', ...);
```

### 字段变更

```sql
-- qpaas_portal 库
ALTER TABLE ins_intelligent_def ADD AGENT_CHOOSE_MES_ TEXT COMMENT '选择的智能体集合信息';
ALTER TABLE ins_intelligent_def_version ADD AGENT_CHOOSE_MES_ TEXT;
```

---

## feat:755661 - GUI 实现链接地址访问

### 用户创建脚本

```sql
-- qpaas_user 库 - 创建匿名查看用户
INSERT INTO os_user (USER_ID_, FULLNAME_, USER_NO_, PWD_, ..., TENANT_ID_, ...)
VALUES ('1971545436343435465', 'qpaasviewuser', 'qpaasviewuser',
  '$2a$10$Ge3D4J9fb3PlANBkQevxEe...', ...);

INSERT INTO os_inst_users (ID_, USER_ID_, TENANT_ID_, ...)
VALUES ('1959545436343436789', '1971545436343435465', '1', ...);

-- 关联到部门
INSERT INTO os_rel_inst (INST_ID_, REL_TYPE_KEY_, PARTY1_, PARTY2_, ...)
VALUES ('2011545436343431234', 'GROUP-USER-BELONG', '1310569804087504897',
  '1971545436343435465', ...);
```

---

## feat:780672 - L2 智能体最新输入输出参数

### 新增接口

```sql
-- 查询最新L2智能体的参数情况
INSERT INTO sys_interface_api (ID_, NAME_, PATH_, ...)
VALUES ('2030932558672252930', '查询最新L2智能体的参数情况',
  '/system/aiAgent/intelligent/getL2NewParams', 'GET', ...);
```

### 字段扩容

```sql
-- qpaas_portal 库 - 扩容多个表字段至 255 字符
ALTER TABLE ins_intelligent_def MODIFY COLUMN APP_CODE_ VARCHAR(255);
ALTER TABLE ins_intelligent_def MODIFY COLUMN KEY_ VARCHAR(255);
ALTER TABLE ins_intelligent_def MODIFY COLUMN NAME_ VARCHAR(255);
ALTER TABLE ins_intelligent_def_version MODIFY COLUMN APP_CODE_ VARCHAR(255);
ALTER TABLE ins_intelligent_def_version MODIFY COLUMN KEY_ VARCHAR(255);
ALTER TABLE ins_intelligent_def_version MODIFY COLUMN NAME_ VARCHAR(255);

-- qpaas_system 库 - 扩容 sys_app_item, sys_app_manage 等
ALTER TABLE sys_app_item MODIFY COLUMN APP_CODE_ VARCHAR(255);
ALTER TABLE sys_app_item MODIFY COLUMN ITEM_KEY_ VARCHAR(255);
ALTER TABLE sys_app_item MODIFY COLUMN ITEM_NAME_ VARCHAR(255);
ALTER TABLE sys_app_manage MODIFY COLUMN CLIENT_CODE_ VARCHAR(255);
ALTER TABLE sys_app_manage MODIFY COLUMN CLIENT_NAME_ VARCHAR(255);
ALTER TABLE sys_app_manage MODIFY COLUMN DESCP_ VARCHAR(1028);
```

---

## 通用部署项目清单

以下 QPaaS 组件在本迭代中需要部署：

| 项目 | 是否需要部署 |
|------|------------|
| qpaas-web-all | ✅ |
| qpaas-auth | ✅ |
| qpaas-system | ✅ |
| qpaas-user | ✅ |
| qpaas-user-job | ✅ |
| bpm-designer | ❌ |
| qpaas-gateway | ❌ |
| qpaas-form | ❌ |
| qpaas-bpm | ❌ |
| qpaas-job | ❌ |

---

*最后更新：2026-04-14*
