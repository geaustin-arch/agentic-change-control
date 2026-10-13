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
