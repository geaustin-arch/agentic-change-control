"""Pure risk and tool policy. The agent cannot expand this allowlist."""
from dataclasses import dataclass
from enum import IntEnum

class Risk(IntEnum): LOW = 1; MEDIUM = 2; HIGH = 3; CRITICAL = 4
ALLOWED_ACTIONS = {"run_unit_tests", "build_container", "deploy_staging"}

@dataclass(frozen=True)
class ChangeRequest:
    change_id: str
    summary: str
    environment: str
    actions: tuple[str, ...]

def assess(req: ChangeRequest) -> tuple[Risk, list[str]]:
    findings=[]
    if req.environment == "production": findings.append("production target requires release approval")
    if any(a not in ALLOWED_ACTIONS for a in req.actions): findings.append("request includes a non-allowlisted action")
    if "deploy_staging" in req.actions: findings.append("staging deployment changes a shared environment")
    if any(w in req.summary.lower() for w in ("credential", "secret", "payment", "customer data")):
        findings.append("sensitive change keyword requires security review")
    risk = Risk.CRITICAL if any("non-allowlisted" in f for f in findings) else Risk.HIGH if len(findings)>1 or req.environment == "production" else Risk.MEDIUM if findings else Risk.LOW
    return risk, findings

def plan(req: ChangeRequest) -> list[str]:
    return [a for a in req.actions if a in ALLOWED_ACTIONS]
