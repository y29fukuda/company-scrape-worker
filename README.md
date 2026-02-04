# SQS to S3 Worker (ECS Fargate)

SQS(Standard)からメッセージを1件受信し、処理結果をS3へJSONとして保存、成功時にSQSメッセージを削除します。

## 必須環境変数
- `AWS_REGION`
- `SQS_QUEUE_URL`
- `S3_BUCKET`
- `S3_PREFIX`

任意:
- `WORKER_ID`

`.env.example` と `worker.py` の環境変数は一致しています。

## ローカル実行
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export $(cat .env | xargs)
python worker.py
```

## Docker 実行
```bash
docker build -t sqs-s3-worker:latest .
docker run --rm --env-file .env sqs-s3-worker:latest
```

## テストメッセージ送信
```bash
python scripts/send_test_message.py
# または任意のボディ
python scripts/send_test_message.py --body "hello"
# JSON文字列を送る場合
python scripts/send_test_message.py --json "{\"hello\": \"world\"}"
```

## ECS(Fargate) 起動確認手順
1. ECRへイメージをpush
1. ECSタスク定義を作成
1. タスク定義の `Container definitions` で以下の環境変数を設定
   - `AWS_REGION`, `SQS_QUEUE_URL`, `S3_BUCKET`, `S3_PREFIX`, `WORKER_ID`(任意)
1. タスクロールに必要権限を付与
   - `sqs:ReceiveMessage`, `sqs:DeleteMessage`, `sqs:GetQueueAttributes`, `sqs:GetQueueUrl`
   - `s3:PutObject`
1. ワンオフでタスクを起動
1. CloudWatch Logs でログを確認
1. SQSにテストメッセージ投入
1. S3の `S3_PREFIX` 配下に `timestamp_messageId_*.json` が作成されることを確認

## ECR push 例
```bash
AWS_ACCOUNT_ID=<YOUR_AWS_ACCOUNT_ID>
AWS_REGION=ap-northeast-1
REPO_NAME=sqs-s3-worker

aws ecr get-login-password --region $AWS_REGION \
  | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

aws ecr create-repository --repository-name $REPO_NAME --region $AWS_REGION

docker tag sqs-s3-worker:latest \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_NAME}:latest

docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_NAME}:latest
```
