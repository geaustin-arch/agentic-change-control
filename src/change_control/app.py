from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .graph import submit, resume

app=FastAPI(title="Agentic Change Control", version="0.1.0")
class ChangeIn(BaseModel):
    change_id:str=Field(min_length=1,max_length=120)
    summary:str=Field(min_length=5,max_length=2000)
    environment:str
    actions:list[str]
class ApprovalIn(BaseModel):
    approved:bool
    approver:str=Field(min_length=2,max_length=120)
    reason:str=Field(default="",max_length=1000)
@app.get("/health")
def health(): return {"status":"ok"}
@app.post("/changes")
def create(body:ChangeIn):
    result=submit(body.model_dump(),body.change_id)
    if "__interrupt__" in result: return {"change_id":body.change_id,"status":"awaiting_approval","interrupt":result["__interrupt__"][0].value}
    return {"change_id":body.change_id,**result}
@app.post("/changes/{change_id}/approval")
def approve(change_id:str, body:ApprovalIn):
    try: result=resume(change_id,body.model_dump())
    except Exception as e: raise HTTPException(409,"No pending approval for this change") from e
    return {"change_id":change_id,**result}
