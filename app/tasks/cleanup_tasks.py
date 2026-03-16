from app.tasks.celery_app import celery_app


@celery_app.task
def cancel_stale_orders():
    # NOTE: will be implemented later
    pass