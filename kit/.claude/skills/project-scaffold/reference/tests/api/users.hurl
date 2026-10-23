# Đăng ký thành viên mới
POST {{base_url}}/api/v1/users
{
  "email": "hurl-{{newUuid}}@example.com",
  "full_name": "  Hurl   Tester "
}
HTTP 201
[Captures]
user_id: jsonpath "$.id"
user_email: jsonpath "$.email"
[Asserts]
jsonpath "$.full_name" == "Hurl Tester"
jsonpath "$.created_at" exists

# Xem lại thành viên vừa tạo
GET {{base_url}}/api/v1/users/{{user_id}}
HTTP 200
[Asserts]
jsonpath "$.email" == "{{user_email}}"

# Trùng email -> 409
POST {{base_url}}/api/v1/users
{
  "email": "{{user_email}}",
  "full_name": "Duplicate"
}
HTTP 409
[Asserts]
jsonpath "$.error.code" == "conflict"

# Email sai định dạng -> 422
POST {{base_url}}/api/v1/users
{
  "email": "not-an-email",
  "full_name": "X"
}
HTTP 422
[Asserts]
jsonpath "$.error.code" == "validation_error"

# Danh sách có thành viên vừa tạo
GET {{base_url}}/api/v1/users?limit=100
HTTP 200
[Asserts]
jsonpath "$.items[*].email" includes "{{user_email}}"

# Không tồn tại -> 404
GET {{base_url}}/api/v1/users/999999999
HTTP 404
