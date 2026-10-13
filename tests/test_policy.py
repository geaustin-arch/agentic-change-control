from change_control.policy import ChangeRequest, Risk, assess, plan

def test_read_only_test_run_is_low_risk():
    r,f=assess(ChangeRequest("c1","add unit tests","development",("run_unit_tests",)))
    assert r == Risk.LOW and not f

def test_production_sensitive_change_is_high_risk():
    r,f=assess(ChangeRequest("c2","rotate payment credential","production",("deploy_staging",)))
    assert r >= Risk.HIGH and len(f) >= 2

def test_arbitrary_tool_is_excluded():
    req=ChangeRequest("c3","cleanup","development",("delete_database",))
    r,f=assess(req)
    assert r == Risk.CRITICAL and "non-allowlisted" in f[0]
    assert plan(req) == []

def test_langgraph_blocks_critical_tool_without_human_override():
    from change_control.graph import submit
    result=submit({"change_id":"bad-tool-1","summary":"routine cleanup","environment":"development","actions":["delete_database"]},"bad-tool-1")
    assert result["status"] == "blocked"
    assert result["execution"] == []
    assert "__interrupt__" not in result

def test_langgraph_pauses_before_shared_environment_change():
    from change_control.graph import resume, submit
    request={"change_id":"staging-1","summary":"publish approved build","environment":"development","actions":["deploy_staging"]}
    result=submit(request,"staging-1")
    assert result["__interrupt__"][0].value["type"] == "change_approval"
    final=resume("staging-1",{"approved":True,"approver":"release-reviewer","reason":"approved"})
    assert final["status"] == "completed"
    assert final["execution"][0]["idempotency_key"] == "staging-1:deploy_staging"
