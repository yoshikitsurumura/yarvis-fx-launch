# API Endpoints

開発中の手早い確認用に、主なエンドポイントと例をまとめます。

## Health
- GET `/health`
```
curl -s http://localhost:3000/health | jq
```

## Tasks
- GET `/tasks`
```
curl -s http://localhost:3000/tasks | jq
```
- POST `/tasks`
```
curl -s -X POST http://localhost:3000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"hello"}' | jq
```
- PATCH `/tasks/:id`
```
curl -s -X PATCH http://localhost:3000/tasks/<ID> \
  -H 'Content-Type: application/json' \
  -d '{"done":true}' | jq
```
- DELETE `/tasks/:id`
```
curl -s -X DELETE -i http://localhost:3000/tasks/<ID>
```

## Seed
- シード投入（ローカル）
```
npm run seed -w @app/api
```

## Automation (MVP)
- POST `/automation/plan`
  - body: `{ text: string }`
  - returns: `{ plan: AutomationPlan }`
- POST `/automation/dry-run`
  - body: `{ plan: AutomationPlan }`
  - returns: `{ valid: boolean, issues: { level: 'error'|'warn', message: string, index?: number }[] }`
- POST `/automation/execute`
  - body: `{ plan: AutomationPlan }`
  - behavior: 現在はシミュレーション実行。`.data/automation/<ts>/` に `plan.json` と `result.json`、擬似スクリーンショット(`.svg`)を保存。
  - returns: `AutomationResult`（`{ ok, artifactsPath, summary, artifacts: [{name,url}] }`）
  - notes: `AUTOMATION_ALLOWED_DOMAINS`（カンマ区切り）環境変数で `goto` の許可ドメインを制限（未設定時は `example.com` のみ許可）。

## Static files
- GET `/files/...`
  - `.data`（または `DATA_DIR`）配下のファイルを静的配信。`/automation/execute` の成果物参照に利用。

## Automation Policy
- GET `/automation/config`
  - returns: `{ policy: { allowedDomains: string[], allowedActions: string[], maxSteps: number, maxRunMs: number, notes?: string[] } }`
  - 備考: `DATA_DIR/automation.config.json` または `AUTOMATION_CONFIG` で上書き可能。`AUTOMATION_ALLOWED_DOMAINS`（カンマ区切り）も反映。

注意: 現段階では安全性担保のため固定プランまたはホワイトリスト検証のみ。実機操作は未対応です。
