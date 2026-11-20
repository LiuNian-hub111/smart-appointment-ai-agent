# 物理辅导约课 Agent

这是一个面向物理辅导场景的本地学习原型。学生可以咨询课程信息、提出约课需求；系统查询老师课表，在时间冲突时推荐其他可用老师，并在用户确认后保存排班。

项目基于 [jerry-ai-dev/smart-appointment-ai-agent](https://github.com/jerry-ai-dev/smart-appointment-ai-agent) 二次改造。原项目面向按摩预约；本分支的物理辅导场景、相应代码改动与验证记录见 [改造记录](EDUCATION_ADAPTATION.md)。这不是从零开发的项目，也尚未上线。

## 为什么做

我曾担任物理辅导老师，遇到学生不了解价格、约课流程不清晰和老师排班难核对的问题。这个原型用于练习把咨询、知识检索和预约排班串成一条可验证的流程。

## 已实现的改造

- 将默认知识、咨询与任务分类提示词、演示老师资料及主要网页文案调整为物理辅导场景。
- 约课收集课程主题、开始时间和时长；老师可以由系统推荐，性别不再是必填条件。
- 保存前再次检查同一老师的时间冲突；保存成功后才返回“约课成功”。冲突时可推荐其他老师，待用户确认后再保存。
- 修复知识录入接口，支持问答或自由填写内容，并拒绝空字符串与纯空格内容。
- 常见价格和约课流程问题直接读取本地知识库；明确的“我想预约……”请求由本地规则分类。其他咨询和预约信息提取仍会调用模型。

## 运行

已在 Python 3.12 下验证；运行还需要项目依赖，以及可用的聊天模型和 Embedding 模型 API。密钥只放在本地 `.env`，不要提交到仓库。

Windows PowerShell 示例：

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

在 `.env` 中填入所选服务商的 `MODEL_PROVIDER`、`LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`，以及 Embedding 对应的配置。然后启动：

```powershell
.venv\Scripts\python.exe app.py
```

访问：

- 聊天页面：<http://127.0.0.1:8001/>
- 知识库页面：<http://127.0.0.1:8001/knowledge>
- API 文档：<http://127.0.0.1:8001/docs>

默认知识库中的价格、上课方式和取消规则均标为“未确认”。如需演示具体价格，可在知识库页面编辑“课程价格”条目，并明确标注“演示价格”；不要把示例金额当作真实报价。

## 验证结果

离线测试命令：

```powershell
.venv\Scripts\python.exe -m pytest tests/test_teacher_schema_migration.py tests/test_intent_rules_offline.py tests/test_common_faq_offline.py tests/test_lesson_booking_offline.py tests/test_knowledge_api_offline.py -q
```

本地运行结果：**14 passed，6 warnings**。测试覆盖旧数据库迁移、知识接口输入校验、知识写入与读取、常见问题快捷回复、明确预约意图分类，以及同一老师的重叠时间冲突。

另外完成过一次本地网页联调：先将演示老师 A 的 `2026-12-01 15:00–16:30` 保存为 `busy`；再请求老师 A 的 `15:30–16:30` 时，系统识别冲突并推荐演示老师 C。用户确认后，数据库新增老师 C 的预约，老师 A 没有第二条重叠记录。演示数据保存在本机数据库中，不随仓库提交。

完成老师命名与数据库迁移后，又通过聊天接口预约演示老师 B 在 `2026-12-02 15:00–16:00` 的电磁学课；接口返回约课成功，数据库查到对应 `busy` 记录。该次请求约耗时 18 秒，时间会受模型服务状态影响。

## 当前限制

- 老师 A/B/C 是演示资料；真实价格、授课方式、地点和改期规则尚未配置。
- 开放式咨询及预约信息提取依赖模型服务；服务商限流时可能等待较久或失败。
- 当前为单用户本地原型；会话状态未按用户隔离，知识管理页面也尚无权限控制。
- 冲突检查是“先查再写”，尚无数据库级原子防重，不适用于多人同时抢同一时段。
- 原有本地数据库会在启动时迁移为 `teachers` / `teacher_schedules`；迁移前建议备份数据库。`strength` 等少量数据库字段沿用旧结构，含义在本项目中是教学专长。

## 主要代码位置

| 作用 | 文件 |
| --- | --- |
| 网页和聊天入口 | `web/routes.py`、`api/chat_handler.py` |
| 任务分类与预约分流 | `agents/task_classification/` |
| 咨询与知识检索 | `agents/consultant/`、`services/knowledge_service.py` |
| 约课解析、老师匹配和保存 | `agents/appointment/`、`services/appointment_service.py` |
| 老师课表与冲突查询 | `db/repositories/teacher_repository.py` |

原项目的架构说明与完整历史可在[上游仓库](https://github.com/jerry-ai-dev/smart-appointment-ai-agent)查看。
