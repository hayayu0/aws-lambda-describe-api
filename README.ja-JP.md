# aws-lambda-describe-api

AWSの参照系API (**describe_xxxx, get_xxxx**, **list_xxxx**) を HTTP GETメソッドでWebクライアント(通常はWebブラウザー)から実行します。

実行結果を中継してWebクライアントに返答します。

このプログラムは AWS Lambda 関数上で動作する Python スクリプトであり、リバースプロキシのように振る舞います。

## フロー図

![aws-describe-api flow diagram](image/aws-describe-api_drawio.png)

1. WebブラウザーでLambda関数のエンドポイントURLへアクセスする
2. URLのパラメータに含まれるAPIがLambda関数で実行される
3. Webブラウザーは結果のJsonを受け取る

## 特徴

- AWSの参照系APIをHTTP GETで実行:  
**describe_xxxx, get_xxxx, list_xxxx** のAPIを URL パラメータで指定して実行します。
- キャッシュ機能 (S3利用可能):  
S3バケットにキャッシュを保存して、次回以降の高速な応答を実現します。
- 複雑なJSONデータの整形・加工:  
  - **select=項目**：取得項目の絞り込み
  - **simpletag**：複雑なタグ構造をシンプル化
  - **flatten**：EC2のインスタンス情報のフラット化
- IPアドレスによるアクセス制御:  
環境変数 source_cidr_list により、アクセスを許可するCIDRを指定可能
- Base64形式のPNG画像返却:  
CloudWatchの **get_metric_widget_image** 専用の機能

## 動作環境

- AWS Lambda (Python 3.x)
- 必要なIAMポリシー:
  - ReadOnlyAccess
  - AWSLambdaBasicExecutionRole
  - AmazonS3FullAccess (キャッシュ利用時)

## 実行例

AZ(アベイラビリティゾーン)のリスト

- Webクライアントで呼び出すURL

```text
https://xxxxxxxx.lambda-url.ap-northeast-1.on.aws/?api=ec2:describe_availability_zones&region=ap-northeast-1&select=ZoneName:ZoneId
```

- 応答

```json
{
    "AvailabilityZones": [
        {
            "ZoneName": "ap-northeast-1a",
            "ZoneId": "apne1-az4"
        },
        {
            "ZoneName": "ap-northeast-1c",
            "ZoneId": "apne1-az1"
        },
        {
            "ZoneName": "ap-northeast-1d",
            "ZoneId": "apne1-az2"
        }
    ]
}
```

※AWS Lambdaの環境変数 default_region が ap-northeast-1 の場合

### その他の使用例

いくつかの使用例を [examples.md](examples.md) にて提示しています。

## AWS Lambda環境変数

- ```s3_bucket```  
キャッシュとして利用するS3バケット名です。環境変数が無い場合、S3にキャッシュする機能が無効となります。
- ```default_region```  
  APIを実行するデフォルトのリージョンです。環境変数が無い場合、```us-east-1``` となります。
- ```default_cache```  
キャッシュの秒数です。S3上のキャッシュデータの期限を判定に使われます(S3のキャッシュ機能が有効な場合)。また、```Cache-Control```ヘッダーの max-age=秒数 として返します。環境変数が無い場合、```60``` となります。
- ```source_cidr_list```  
実行を許可するソースIPアドレスのリストです。CIDR形式で指定します。空白区切りで複数のCIDRが指定できます。環境変数が無い場合、 ```0.0.0.0/0 ::/0``` となり、全てのIPが許可となります。設定値以外のソースIPからのアクセスは HTTPステータスコード **400** を返します。
- ```remove_key_list```  
APIの結果データから、特定のキーとそのキーの値を削除して返します。キー名は空白区切りで複数指定できます。環境変数が無い場合、```ResponseMetadata Marker NextToken nextToken IsTruncated MaxResults``` となります。

## URLパラメータ

- ```api=service:operation```  
実行するAWS APIを指定します。必須。例: ```api=ec2:describe_instances```
- ```arg={}```  
AWS APIの引数をJSON形式で指定します。AWS APIによっては必須かどうかが変わります。```{``` と ```}``` は ```%7b``` と ```%7d``` にエンコードしないとエラーとなります。特に ```Filters``` を指定する場合は複雑になりますので [examples.md](examples.md) を確認ください。
- ```select=key1:key2```  
必要な項目を絞り込んで取得します。コロン区切りで複数指定可能です。実行結果のデータ部にキー名が1つの場合のみ有効です。例: ```select=InstanceId:InstanceType```
- ```region=ap-northeast-1```  
Lambda環境変数 ```default_region``` で指定されたリージョンの代わりに指定します。
- ```cache=秒数```  
Lambda環境変数 ```default_cache``` で指定されたキャッシュの有効期限の秒数の代わりに指定します。値を ```never``` とするとキャッシュしません。
- ```simpletag```  
タグ情報をシンプルな ```{"タグキー名": タグの値}``` の構造に変換します。```=値``` は指定しません。
- ```flatten```  
ec2:describe_instances 専用です。```Reservations``` キーを取り除いて、インスタンス情報をフラット化します。```=値``` は指定しません。

## 通常のAWS API実行と比較した利点

- ページネーションの自動処理:  
全ページ分を取得して1回で全データを返却します。
- S3キャッシュによる高速化:  
同一リクエストに対してはキャッシュを返却するため、APIコールを削減します。
- JSONレスポンスの整形とフィルタリング:  
複雑なJSONから必要な情報だけをシンプルに取得可能です。
- 一般ユーザーにも参照を許可:  
Lambda関数のIAM ロールで実行されるため、AWSのIAMユーザーを持たないユーザー向けに閲覧専用のWebサービスを提供することができます。

## 命名規則「○○ケース」

- ```api=``` では snake_case で指定します。例：**iam:list_users**
- ```select=``` のキー名は CamelCase で指定します。例：**select=InstanceId**
- ```arg=``` の ```Filters``` の ```Name``` では kebab-case で指定します。例：**"Name": "instance-id"**
- このように命名規則がバラバラなのは、Boto3 に準じているためであり、Lambda関数で命名規則を強制的に統一させることによってバグを埋め込んでしまわないようにしています。

## 制限事項

- 応答のデータサイズが 5.75 MiB を超える場合、HTTPステータスコード **413** エラーとなります。
- 実行時間が59秒以上かかる場合は、Lambda関数が失敗します。

## インストール

### AWS CloudFormation テンプレート

S3利用版:
[cfn-lambda-describe-api-with-s3.yaml](src/cfn-lambda-describe-api.yaml)

S3利用なし版:
[cfn-lambda-describe-api.yaml](src/cfn-lambda-describe-api.yaml)

### CloudFormationを利用しない場合の注意点

- 上記 動作環境 で記載したIAMポリシーをアタッチしたIAMロールを作成して、Lambda関数に指定してください。
- Lambda関数の実行時間を 3秒→59秒にしてください。
- Lambda関数のメモリ量を必要に応じて 256MiB 以上に増やしてください。
