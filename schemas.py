from typing import Literal
from pydantic import BaseModel


class BugTriage(BaseModel):
    severity: Literal["low", "medium", "high", "critical"]
    component: str
    is_security_issue: bool
    summary: str