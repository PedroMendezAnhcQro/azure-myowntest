import logging
import azure.functions as func
import azure.durable_functions as df

async def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:
    logging.info("HTTP trigger processed a request.")

    event_uid = req.params.get('eventUID')
    if not event_uid:
        try:
            req_body = req.get_json()
        except ValueError:
            req_body = {}
        event_uid = req_body.get('eventUID')
    logging.info(f"Param received = '{event_uid}'.")

    if not event_uid:
        return func.HttpResponse("No se ha enviado el eventUID", status_code=400)

    client = df.DurableOrchestrationClient(starter)
    instance_id = await client.start_new("TakeAttendanceOrchestator", None, event_uid)

    logging.info(f"Started orchestration with ID = '{instance_id}'.")
    return client.create_check_status_response(req, instance_id)