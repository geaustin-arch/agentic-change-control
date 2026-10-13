from typing import TypedDict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from .policy import ChangeRequest, assess, plan, Risk

class State(TypedDict, total=False):
    request: dict[str, Any]
    risk: int
    findings: list[str]
    approved_plan: list[str]
    approval: dict[str, Any]
    execution: list[dict[str, Any]]
    audit: list[dict[str, Any]]
    status: str

def evaluate(s: State) -> State:
    r=s["request"]; req=ChangeRequest(r["change_id"],r["summary"],r["environment"],tuple(r["actions"]))
    risk, findings=assess(req)
    return {"risk": int(risk), "findings": findings, "approved_plan": plan(req),
            "audit": s.get("audit",[])+[{"event":"risk_assessed","risk":risk.name.lower()}]}

def gate(s: State) -> str:
    if s["risk"] >= int(Risk.CRITICAL): return "execute"
    return "approval" if s["risk"] >= int(Risk.MEDIUM) else "execute"

def approval(s: State) -> State:
    decision=interrupt({"type":"change_approval","request":s["request"],"risk":s["risk"],"findings":s["findings"],"proposed_actions":s["approved_plan"]})
    return {"approval":decision,"audit":s.get("audit",[])+[{"event":"human_approval_recorded","approver":decision.get("approver","unknown")}]}

def execute(s: State) -> State:
    if s.get("risk",0) >= int(Risk.CRITICAL):
        return {"status":"blocked","execution":[],"audit":s.get("audit",[])+[{"event":"execution_blocked","reason":"critical risk cannot be overridden"}]}
    if s.get("risk",0) >= int(Risk.MEDIUM) and not s.get("approval",{}).get("approved"):
        return {"status":"blocked","execution":[]}
    # Simulated adapter: it records allowlisted actions and never runs arbitrary shell commands.
    results=[{"action":a,"result":"simulated_success","idempotency_key":f"{s['request']['change_id']}:{a}"} for a in s.get("approved_plan",[])]
    return {"execution":results,"status":"completed","audit":s.get("audit",[])+[{"event":"execution_simulated","actions":len(results)}]}

def build_graph():
    b=StateGraph(State); b.add_node("evaluate",evaluate); b.add_node("approval",approval); b.add_node("execute",execute)
    b.add_edge(START,"evaluate"); b.add_conditional_edges("evaluate",gate,{"approval":"approval","execute":"execute"})
    b.add_edge("approval","execute"); b.add_edge("execute",END)
    return b.compile(checkpointer=MemorySaver())

graph=build_graph()
def submit(request:dict, thread_id:str): return graph.invoke({"request":request,"audit":[]},{"configurable":{"thread_id":thread_id}})
def resume(thread_id:str, decision:dict): return graph.invoke(Command(resume=decision),{"configurable":{"thread_id":thread_id}})
