# 智能体评测系统 - 异步任务设计

> 文档版本：V1.0  
> 日期：2026-04-19  
> 状态：待评审

---

## 一、概述

### 1.1 为什么需要异步任务？

评测任务的特点：
- **耗时长**：一次评测可能需要几十秒到几分钟
- **可中断**：评测过程可以分步执行
- **需要进度反馈**：用户需要实时看到评测进度

因此，评测任务必须使用异步执行，否则：
- 用户请求会超时
- 无法支持长时任务
- 无法实时反馈进度

### 1.2 技术选型

| 方案 | 优点 | 缺点 |
|------|------|------|
| **Celery + Redis** | 成熟稳定，支持分布式，监控完善 | 需要额外部署 Redis |
| asyncio + aiohttp | 轻量，无需额外依赖 | 单机，监控需自行实现 |
| FastAPI BackgroundTasks | 简单，无需额外依赖 | 不支持分布式 |

**选择 Celery + Redis**，原因：
1. 支持分布式部署
2. 任务状态持久化，重启不丢失
3. 完善的监控和重试机制
4. 与 FastAPI 集成良好

---

## 二、Celery 配置

### 2.1 项目结构

```
evaluation_system/
├── worker/
│   ├── __init__.py
│   ├── celery_app.py      # Celery 配置
│   └── tasks.py           # 任务定义
```

### 2.2 Celery 应用配置

```python
# worker/celery_app.py
from celery import Celery
import os

# Redis 配置
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 创建 Celery 应用
celery_app = Celery(
    "evaluation_system",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["worker.tasks"]
)

# 配置
celery_app.conf.update(
    # 任务序列化方式
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # 时区
    timezone="Asia/Shanghai",
    enable_utc=True,
    
    # 任务超时
    task_soft_time_limit=600,  # 10 分钟软超时
    task_time_limit=900,       # 15 分钟硬超时
    
    # 重试配置
    task_acks_late=True,       # 任务完成后确认
    task_reject_on_worker_lost=True,
    
    # 并发配置
    worker_prefetch_multiplier=1,  # 防止任务积压
    worker_concurrency=5,
    
    # 结果过期时间
    result_expires=3600,  # 1 小时
    
    # 任务路由
    task_routes={
        "worker.tasks.run_evaluation": {"queue": "evaluation"},
        "worker.tasks.cleanup_old_results": {"queue": "maintenance"},
    },
    
    # 定期任务
    beat_schedule={
        "cleanup-old-results": {
            "task": "worker.tasks.cleanup_old_results",
            "schedule": 86400,  # 每天执行
        },
        "check-pending-tasks": {
            "task": "worker.tasks.check_pending_tasks",
            "schedule": 300,    # 每 5 分钟执行
        },
    },
)
```

---

## 三、任务定义

### 3.1 评测任务

```python
# worker/tasks.py
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
import logging
from datetime import datetime

from service.executor import EvaluationExecutor
from service.notification import NotificationService
from database import Database

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="worker.tasks.run_evaluation")
def run_evaluation(self, task_id: int):
    """
    执行评测任务
    
    Args:
        task_id: 任务 ID
    """
    db = Database()
    executor = EvaluationExecutor()
    notification_service = NotificationService()
    
    try:
        logger.info(f"开始执行评测任务: {task_id}")
        
        # 1. 更新任务状态
        db.update_task_status(task_id, "running", started_at=datetime.now())
        
        # 2. 执行评测
        report = executor.execute_task(task_id)
        
        # 3. 更新任务完成状态
        db.update_task_status(
            task_id, 
            "completed",
            completed_at=datetime.now(),
            duration_ms=int(report.duration_ms)
        )
        
        # 4. 发送完成通知
        if report.regression.get("detected"):
            notification_service.send_regression_alert(task_id)
        else:
            notification_service.send_completion_notification(task_id)
        
        logger.info(f"评测任务完成: {task_id}, 得分: {report.summary['weighted_score']}")
        
        return {
            "task_id": task_id,
            "status": "completed",
            "report_id": report.id,
            "weighted_score": report.summary["weighted_score"],
            "grade": report.summary["grade"]
        }
        
    except SoftTimeLimitExceeded:
        # 软超时处理
        logger.warning(f"评测任务超时: {task_id}")
        db.update_task_status(
            task_id,
            "failed",
            error_message="任务执行超时"
        )
        raise
        
    except Exception as e:
        # 异常处理
        logger.error(f"评测任务执行失败: {task_id}, error: {e}")
        db.update_task_status(
            task_id,
            "failed",
            error_message=str(e)
        )
        
        # 发送失败通知
        notification_service.send_failure_notification(task_id, str(e))
        
        raise


@shared_task(name="worker.tasks.run_evaluation_with_retry")
def run_evaluation_with_retry(task_id: int, max_retries: int = 3):
    """
    带重试的评测任务
    
    Args:
        task_id: 任务 ID
        max_retries: 最大重试次数
    """
    try:
        return run_evaluation(task_id)
    except Exception as e:
        # 获取当前重试次数
        task = run_evaluation.request
        if task.retries < max_retries:
            # 计算退避时间
            countdown = 2 ** task.retries * 30  # 30s, 60s, 120s
            
            logger.info(
                f"任务 {task_id} 失败，准备重试 "
                f"(retry {task.retries + 1}/{max_retries}, "
                f"countdown={countdown}s)"
            )
            
            raise run_evaluation.retry(
                exc=e,
                countdown=countdown,
                max_retries=max_retries
            )
        else:
            logger.error(f"任务 {task_id} 重试次数耗尽，标记为失败")
            raise
```

### 3.2 定时任务

```python
@shared_task(name="worker.tasks.cleanup_old_results")
def cleanup_old_results(days: int = 30):
    """
    清理过期的评测结果
    
    Args:
        days: 保留天数，默认 30 天
    """
    db = Database()
    deleted_count = db.delete_old_results(days)
    logger.info(f"清理了 {deleted_count} 条过期评测结果")
    return {"deleted_count": deleted_count}


@shared_task(name="worker.tasks.check_pending_tasks")
def check_pending_tasks():
    """
    检查待处理任务，防止任务卡住
    """
    db = Database()
    
    # 查找卡住的任务（pending 状态超过 1 小时）
    stuck_tasks = db.get_stuck_tasks(threshold_minutes=60)
    
    for task in stuck_tasks:
        logger.warning(f"发现卡住的任务: {task.id}")
        
        # 可选：自动标记为失败
        # db.update_task_status(task.id, "failed", error_message="任务超时")
    
    return {"stuck_count": len(stuck_tasks)}
```

### 3.3 调度任务

```python
@shared_task(name="worker.tasks.schedule_daily_evaluation")
def schedule_daily_evaluation(test_set_id: int):
    """
    每日定时评测
    
    Args:
        test_set_id: 评测集 ID
    """
    db = Database()
    
    # 获取评测集信息
    test_set = db.get_test_set(test_set_id)
    if not test_set:
        logger.error(f"评测集不存在: {test_set_id}")
        return
    
    # 创建新的评测任务
    task = db.create_task(
        test_set_id=test_set_id,
        agent_id=test_set.agent_id,
        agent_type=test_set.agent_type,
        trigger="scheduled"
    )
    
    # 异步执行
    run_evaluation.delay(task.id)
    
    logger.info(f"创建定时评测任务: {task.id}")
    return {"task_id": task.id}
```

---

## 四、API 集成

### 4.1 FastAPI 路由

```python
# api/tasks.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from worker.tasks import run_evaluation, run_evaluation_with_retry

router = APIRouter(prefix="/api/v1/evaluation", tags=["tasks"])


class CreateTaskRequest(BaseModel):
    test_set_id: int
    agent_id: int
    agent_type: str
    agent_version: Optional[str] = None
    trigger: str = "manual"


class TaskResponse(BaseModel):
    task_id: int
    task_uuid: str
    status: str
    total_cases: int


@router.post("/tasks", response_model=TaskResponse)
async def create_task(request: CreateTaskRequest):
    """创建评测任务"""
    db = Database()
    
    # 1. 验证评测集
    test_set = db.get_test_set(request.test_set_id)
    if not test_set:
        raise HTTPException(status_code=404, detail="评测集不存在")
    
    # 2. 验证智能体
    agent = db.get_agent(request.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    
    # 3. 创建任务记录
    task = db.create_task(
        test_set_id=request.test_set_id,
        agent_id=request.agent_id,
        agent_type=request.agent_type,
        agent_version=request.agent_version,
        trigger=request.trigger,
        created_by=get_current_user_id()
    )
    
    # 4. 异步执行任务
    run_evaluation_with_retry.delay(task.id)
    
    return TaskResponse(
        task_id=task.id,
        task_uuid=task.task_uuid,
        status=task.status,
        total_cases=test_set.total_cases
    )


@router.get("/tasks/{task_id}")
async def get_task(task_id: int):
    """获取任务详情"""
    db = Database()
    task = db.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return task


@router.get("/tasks/{task_id}/progress")
async def get_task_progress(task_id: int):
    """获取任务进度"""
    db = Database()
    task = db.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 从 Redis 获取实时进度
    progress = redis_client.get(f"task_progress:{task_id}")
    
    return {
        "task_id": task_id,
        "status": task.status,
        "total_cases": task.total_cases,
        "completed_cases": task.completed_cases,
        "progress": task.progress,
        "started_at": task.started_at,
        "estimated_remaining_seconds": calculate_eta(task)
    }
```

### 4.2 进度更新

```python
# 在评测执行器中更新进度
class EvaluationExecutor:
    
    async def execute_task(self, task_id: int):
        db = Database()
        task = db.get_task(task_id)
        test_cases = db.get_test_cases(task.test_set_id)
        
        for i, case in enumerate(test_cases):
            # 执行评测...
            
            # 更新 Redis 进度（实时）
            redis_client.setex(
                f"task_progress:{task_id}",
                3600,  # 1 小时过期
                {
                    "completed": i + 1,
                    "total": len(test_cases),
                    "current_case_id": case.id
                }
            )
            
            # 更新数据库进度（定期，如每 10 条更新一次）
            if (i + 1) % 10 == 0:
                db.update_task_progress(
                    task_id,
                    completed_cases=i + 1,
                    progress=int((i + 1) / len(test_cases) * 100)
                )
        
        # 最终更新
        db.update_task_progress(
            task_id,
            completed_cases=len(test_cases),
            progress=100
        )
```

---

## 五、监控与日志

### 5.1 Flower 监控

Flower 是 Celery 的监控工具：

```bash
# 启动 Flower
celery -A worker.celery_app flower --port=5555

# 访问 http://localhost:5555 查看监控界面
```

### 5.2 Prometheus 指标

```python
from prometheus_client import Counter, Histogram, Gauge

# 定义指标
task_started = Counter("evaluation_task_started_total", "评测任务启动次数")
task_completed = Counter("evaluation_task_completed_total", "评测任务完成次数")
task_failed = Counter("evaluation_task_failed_total", "评测任务失败次数")
task_duration = Histogram("evaluation_task_duration_seconds", "评测任务耗时")
task_progress = Gauge("evaluation_task_progress", "评测任务进度", ["task_id"])


@shared_task(bind=True, name="worker.tasks.run_evaluation")
def run_evaluation(self, task_id: int):
    task_started.inc()
    
    start_time = time.time()
    try:
        # 执行任务...
        task_completed.inc()
    except Exception:
        task_failed.inc()
        raise
    finally:
        task_duration.observe(time.time() - start_time)
```

### 5.3 日志配置

```python
# logging_config.py
import logging.config
import structlog

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": "%(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "loggers": {
        "worker": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "celery": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}

# structlog 配置
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)
```

---

## 六、部署配置

### 6.1 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    command: uvicorn main:app --host 0.0.0.0 --port 8080
    ports:
      - "8080:8080"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://user:pass@postgres:5432/evaluation
    depends_on:
      - redis
      - postgres
    deploy:
      replicas: 2

  worker:
    build: .
    command: celery -A worker.celery_app worker --loglevel=info --concurrency=5
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://user:pass@postgres:5432/evaluation
    depends_on:
      - redis
      - postgres
    deploy:
      replicas: 2

  beat:
    build: .
    command: celery -A worker.celery_app beat --loglevel=info
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  flower:
    build: .
    command: celery -A worker.celery_app flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=evaluation
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  redis_data:
  postgres_data:
```

### 6.2 Kubernetes 部署

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: evaluation-worker
spec:
  replicas: 3
  selector:
    matchLabels:
      app: evaluation-worker
  template:
    metadata:
      labels:
        app: evaluation-worker
    spec:
      containers:
        - name: worker
          image: evaluation-system:latest
          command: ["celery", "-A", "worker.celery_app", "worker", "--loglevel=info", "--concurrency=5"]
          env:
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: evaluation-secrets
                  key: redis_url
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: evaluation-secrets
                  key: database_url
          resources:
            requests:
              memory: "512Mi"
              cpu: "500m"
            limits:
              memory: "1Gi"
              cpu: "1000m"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: evaluation-beat
spec:
  replicas: 1
  selector:
    matchLabels:
      app: evaluation-beat
  template:
    metadata:
      labels:
        app: evaluation-beat
    spec:
      containers:
        - name: beat
          image: evaluation-system:latest
          command: ["celery", "-A", "worker.celery_app", "beat", "--loglevel=info"]
          env:
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: evaluation-secrets
                  key: redis_url
```

---

## 七、运维命令

### 7.1 常用命令

```bash
# 启动 Worker
celery -A worker.celery_app worker --loglevel=info

# 启动 Beat（定时任务）
celery -A worker.celery_app beat --loglevel=info

# 启动 Flower（监控）
celery -A worker.celery_app flower --port=5555

# 查看任务队列
celery -A worker.celery_app inspect active

# 查看 Worker 状态
celery -A worker.celery_app inspect stats

# 手动触发任务
celery -A worker.celery_app call worker.tasks.run_evaluation --args=[1]

# 取消任务
celery -A worker.celery_app control revoke <task_id>

# 清理过期结果
celery -A worker.celery_app call worker.tasks.cleanup_old_results --kwargs='{"days": 30}'
```

### 7.2 故障排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 任务一直 pending | Worker 未启动 / Redis 不可用 | 检查 Worker 日志 / Redis 连接 |
| 任务失败 | 代码异常 / 超时 | 查看任务日志 / 调整超时时间 |
| 任务重复执行 | ack_late 未启用 | 启用 `task_acks_late=True` |
| 内存持续增长 | 结果未清理 | 调整 `result_expires` / 手动清理 |

---

*文档状态：待评审*
