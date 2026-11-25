from nicegui import app


def get_org_id() -> int:
    if app.is_started:
        return app.storage.user.get("org_id", 1)
    return 1
