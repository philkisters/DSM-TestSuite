from fastapi import HTTPException, Request

def get_engine(request: Request):
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        raise HTTPException(503, "Database not configured")
    return engine

def get_run_manager(request: Request):
    run_manager = getattr(request.app.state, "run_manager", None)
    if run_manager is None:
        raise HTTPException(503, "Run manager not configured")
    return run_manager