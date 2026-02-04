import argparse
import json
import os
import sys
from datetime import datetime, timezone

import boto3


def require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        print(f"missing env: {name}")
        sys.exit(1)
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a test message to SQS")
    parser.add_argument("--body", help="Raw body string")
    parser.add_argument("--json", dest="json_body", help="JSON string")
    args = parser.parse_args()

    region = require_env("AWS_REGION")
    queue_url = require_env("SQS_QUEUE_URL")

    if args.json_body is not None:
        body = args.json_body
    elif args.body is not None:
        body = args.body
    else:
        body = json.dumps(
            {
                "type": "test",
                "sent_at": datetime.now(timezone.utc).isoformat(),
            },
            ensure_ascii=False,
        )

    sqs = boto3.client("sqs", region_name=region)
    resp = sqs.send_message(QueueUrl=queue_url, MessageBody=body)
    message_id = resp.get("MessageId")
    print(f"sent message_id={message_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
