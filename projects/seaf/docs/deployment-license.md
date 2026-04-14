# Seaf 部署流程 - agents-license

> 来源：360AI企业智能体知识库（熊浔阳整理）
> 更新：约 2025-10（推断）

---

## 一、可执行文件

| 文件 | 说明 |
|------|------|
| `agents-license` | AMD 环境版本，41.06 MB |

---

## 二、配置文件准备

在可执行文件同目录下创建 `conf/` 文件夹，放入：

- `application.toml` — 主配置文件
- `rsa_public_key.pem` — RSA 公钥文件（808 Byte）

### 配置修改

修改 `application.toml` 中的公钥文件路径：

```toml
rsaPublicKeyPath = "/实际部署路径/configs/rsa_public_key.pem"
```

---

## 三、启动命令

```bash
./agents-license -conf=conf/application.toml
```

---

## 四、License 创建接口

部署完成后，通过 POST 访问：

```
http://{{agent_host}}/seaf/api/admin/license/create
```

- `agent_host`：部署机器 IP + 端口（默认 25711）

### 请求 Body

```json
{
  "licenseId": "",
  "user_number_type": "0",
  "user_number": "100",
  "agent_number_type": "0",
  "agent_number": "100",
  "agent_types": [
    { "agent_type_id": "1", "agent_type_name": "推理智能体" },
    { "agent_type_id": "2", "agent_type_name": "GUI智能应用" },
    { "agent_type_id": "3", "agent_type_name": "多智能体蜂群" },
    { "agent_type_id": "4", "agent_type_name": "异构智能体" }
  ],
  "server_expire_type": "0",
  "server_start_time": "1758701034",
  "server_end_time": "1768981756",
  "server_fp": "UqST4NaiIJV7R6Gd3mxGupTyePQ...",
  "server_id": "fa:16:3e:c7:ea:4d",
  "version": "9.0sp2",
  "versions_type": "1",
  "license_type": "2",
  "cloud_id": "4000",
  "valid_type": "12",
  "corp_name": "179license",
  "market_mail": "1690060140@qq.com",
  "project_manager_mail": "1690060140@qq.com",
  "trans_id": "cc07df6f0c0180445c08745047c2e5d8"
}
```

### 关键字段说明

| 字段 | 说明 |
|------|------|
| `server_id` | 服务器 MAC 地址 |
| `server_fp` | 服务器指纹 |
| `server_start_time` / `server_end_time` | 授权生效/失效时间（Unix 时间戳） |
| `user_number` | 用户数量上限 |
| `agent_number` | 智能体数量上限 |
| `agent_types` | 授权的智能体类型 |

详细参数说明见： http://yapi.ccwork.qihoo.net/project/426/interface/api/13995

---

*最后更新：约 2025-10*
