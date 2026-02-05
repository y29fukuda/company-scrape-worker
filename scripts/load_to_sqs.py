import csv
import json
import os
import sys

import boto3


def require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        print(f"missing env: {name}")
        sys.exit(1)
    return value


def main() -> int:
    queue_url = os.getenv("SQS_QUEUE_URL") or os.getenv("SQS_URL")
    if not queue_url:
        print("missing env: SQS_QUEUE_URL (or SQS_URL)")
        return 1

    csv_path = require_env("CSV_PATH")
    region = os.getenv("AWS_REGION", "ap-northeast-1")

    sqs = boto3.client("sqs", region_name=region)

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        batch = []
        for i, row in enumerate(reader, 1):
            body = json.dumps(row, ensure_ascii=False)
            batch.append({"Id": str(i), "MessageBody": body})

            if len(batch) == 10:
                resp = sqs.send_message_batch(QueueUrl=queue_url, Entries=batch)
                failed = resp.get("Failed", [])
                if failed:
                    print("failed:", failed)
                    return 1
                batch = []
                if i % 10000 == 0:
                    print("sent", i)

        if batch:
            resp = sqs.send_message_batch(QueueUrl=queue_url, Entries=batch)
            failed = resp.get("Failed", [])
            if failed:
                print("failed:", failed)
                return 1

    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
