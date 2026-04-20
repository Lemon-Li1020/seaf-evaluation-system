"""
Notification utilities.
"""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class NotificationConfig:
    """Configuration for evaluation notifications."""
    enabled: bool = False
    webhook_url: Optional[str] = None
    channels: List[str] = field(default_factory=list)  # e.g., ["email", "slack"]
    notify_on: List[str] = field(default_factory=list)  # e.g., ["completion", "regression"]


@dataclass
class NotificationPayload:
    """Payload for evaluation notifications."""
    event_type: str
    task_id: int
    agent_id: int
    team_id: int
    status: str
    summary: Dict[str, Any] = field(default_factory=dict)
    regression: Optional[Dict[str, Any]] = None
    report_url: Optional[str] = None


class NotificationService:
    """Service for sending evaluation notifications."""
    
    def __init__(self, config: Optional[NotificationConfig] = None) -> None:
        self.config = config or NotificationConfig()
        self._http_client: Optional[Any] = None
    
    async def send(
        self,
        payload: NotificationPayload,
    ) -> bool:
        """
        Send a notification based on configuration.
        
        Returns True if notification was sent successfully.
        """
        if not self.config.enabled:
            return False
        
        if payload.event_type not in self.config.notify_on:
            return False
        
        try:
            if "webhook" in self.config.channels and self.config.webhook_url:
                await self._send_webhook(payload)
            
            # Additional notification channels can be added here
            return True
        
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    async def _send_webhook(self, payload: NotificationPayload) -> None:
        """Send webhook notification."""
        import httpx
        
        webhook_data = {
            "event": payload.event_type,
            "task_id": payload.task_id,
            "agent_id": payload.agent_id,
            "team_id": payload.team_id,
            "status": payload.status,
            "summary": payload.summary,
        }
        
        if payload.regression:
            webhook_data["regression"] = payload.regression
        
        if payload.report_url:
            webhook_data["report_url"] = payload.report_url
        
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                self.config.webhook_url,
                json=webhook_data,
            )
    
    async def notify_completion(
        self,
        task_id: int,
        agent_id: int,
        team_id: int,
        summary: Dict[str, Any],
        report_url: Optional[str] = None,
    ) -> bool:
        """Send completion notification."""
        payload = NotificationPayload(
            event_type="completion",
            task_id=task_id,
            agent_id=agent_id,
            team_id=team_id,
            status="completed",
            summary=summary,
            report_url=report_url,
        )
        return await self.send(payload)
    
    async def notify_regression(
        self,
        task_id: int,
        agent_id: int,
        team_id: int,
        regression: Dict[str, Any],
        summary: Dict[str, Any],
    ) -> bool:
        """Send regression alert notification."""
        payload = NotificationPayload(
            event_type="regression",
            task_id=task_id,
            agent_id=agent_id,
            team_id=team_id,
            status="regression_detected",
            summary=summary,
            regression=regression,
        )
        return await self.send(payload)
