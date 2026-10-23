# Hệ thống phải báo đủ 3 thành phần hoạt động
GET {{base_url}}/api/health
HTTP 200
[Asserts]
jsonpath "$.status" == "ok"
jsonpath "$.database" == "ok"
jsonpath "$.cache" == "ok"
