import logging
import os
import requests
from datetime import timedelta
import azure.functions as func
import azure.durable_functions as df

app = df.DFApp(http_auth_level=func.AuthLevel.FUNCTION)

# 1️⃣ HTTP STARTER
@app.route(route="takeattendance")
@app.durable_client_input(client_name="client")
async def http_start(req: func.HttpRequest, client: df.DurableOrchestrationClient):
    logging.info("HTTP trigger processed a request.")

    event_uid = req.params.get("eventUID")
    if not event_uid:
        try:
            req_body = req.get_json()
            event_uid = req_body.get("eventUID")
        except ValueError:
            event_uid = None

    logging.info(f"Param received = '{event_uid}'.")

    if not event_uid:
        return func.HttpResponse("No se ha enviado el eventUID", status_code=400)

    instance_id = await client.start_new("TakeAttendanceOrchestator", event_uid, event_uid)
    logging.info(f"Started orchestration with ID = '{instance_id}'.")
    return client.create_check_status_response(req, instance_id)


# 2️⃣ ORCHESTRATOR
@app.orchestration_trigger(context_name="context")
def TakeAttendanceOrchestator(context: df.DurableOrchestrationContext):
    event_uid = context.get_input()

    if not event_uid:
        logging.error("No eventUID found in orchestration input.")
        return {"status": "error", "message": "No eventUID provided."}

    retry_options = df.RetryOptions(first_retry_interval_in_milliseconds=5000, max_number_of_attempts=3)

    while True:
        should_continue = yield context.call_activity_with_retry("CallLaravelApi", retry_options, event_uid)

        if not should_continue:
            logging.info("Activity returned False. Exiting loop.")
            break

        yield context.create_timer(context.current_utc_datetime + timedelta(seconds=12))

    return {"status": "ok", "message": "Orchestration finished"}


# 3️⃣ ACTIVITY
@app.activity_trigger(input_name="event_uid")
def CallLaravelApi(event_uid: str) -> bool:
    logging.info(f"Llamando al endpoint Laravel con UID: {event_uid}")

    admin_domain = os.environ.get("ADMIN_DOMAIN")
    if not admin_domain:
        logging.error("ADMIN_DOMAIN no está definido")
        return False

    try:
        laravel_url = f"{admin_domain}api/async-task"
        response = requests.post(laravel_url, json={"eventUID": event_uid}, timeout=20)
        response.raise_for_status()

        data = response.json()
        logging.info(f"Respuesta Laravel: {data}")
        return data.get("should_continue", False)

    except requests.exceptions.RequestException as e:
        logging.error(f"Error al llamar a Laravel API: {e}")
        # Lanza la excepción para que el orquestador la capture y active el reintento
        raise e