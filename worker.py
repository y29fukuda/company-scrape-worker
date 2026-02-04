import json
import os
import sys
import traceback
import uuid
from datetime import datetime, timezone

import boto3


def require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        print(f"missing env: {name}")
        sys.exit(1)
    return value


def normalize_prefix(prefix: str) -> str:
    if not prefix:
        return ""
    prefix = prefix.lstrip("/")
    if not prefix.endswith("/"):
        prefix += "/"
    return prefix


def main() -> int:
    try:
        region = require_env("AWS_REGION")
        queue_url = require_env("SQS_QUEUE_URL")
        bucket = require_env("S3_BUCKET")
        prefix = normalize_prefix(require_env("S3_PREFIX"))
        worker_id = os.getenv("WORKER_ID", "worker")

        def log(message: str) -> None:
            print(f"[{worker_id}] {message}")

        sqs = boto3.client("sqs", region_name=region)
        s3 = boto3.client("s3", region_name=region)

        log("receiving message from SQS...")
        resp = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=10,
        )

        messages = resp.get("Messages", [])
        if not messages:
            log("no messages")
            return 0

        msg = messages[0]
        message_id = msg.get("MessageId", "unknown")
        body = msg.get("Body", "")

        try:
            parsed = json.loads(body)
            payload = {"body": parsed, "is_json": True}
        except json.JSONDecodeError:
            payload = {"raw_body": body, "is_json": False}

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        suffix = uuid.uuid4().hex[:8]
        key = f"{prefix}{timestamp}_{message_id}_{suffix}.json"

        record = {
            "worker_id": worker_id,
            "message_id": message_id,
            "received_at": timestamp,
            **payload,
        }

        log(f"putting to S3: s3://{bucket}/{key}")
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(record, ensure_ascii=False).encode("utf-8"),
            ContentType="application/json",
        )

        receipt_handle = msg.get("ReceiptHandle")
        if receipt_handle:
            log("deleting message from SQS...")
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle,
            )

        log("done")
        return 0

    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
