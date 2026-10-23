---
name: hexagonal-backend
description: Luật kiến trúc Hexagonal của backend FastAPI (controller → usecase → module service → repository, mỗi tầng qua interface ABC), cách thêm module, usecase, endpoint, migration và cách test từng tầng. Dùng mỗi khi đọc hoặc sửa code trong backend/.
user-invocable: false
---

# Các tầng và luật phụ thuộc

```
HTTP ─► controllers/  ──dùng──► IUseCase (usecases/<area>/interfaces.py)
                                   │ implementation: usecases/<area>/<name>.py
                                   ▼
                     IXxxService (modules/<m>/interfaces.py)    + ICache… (shared/interfaces.py)
                                   │ implementation: modules/<m>/service.py
                                   ▼
                     IXxxRepository (modules/<m>/interfaces.py)
                                   ▲ implementation: modules/<m>/repository.py (SQLAlchemy)
container.py = composition root: nơi DUY NHẤT `new` implementation và ghép qua interface
```

| Tầng | Được làm | KHÔNG được làm |
|---|---|---|
| `controllers/` | Định nghĩa route, schema request/response (Pydantic), gọi **interface** usecase, ánh xạ DTO ↔ response | Logic nghiệp vụ; import `modules`, `shared`, `container`, `sqlalchemy`, `redis` |
| `usecases/<area>/` | Một class = một hành động người dùng (`RegisterUserUseCase`). Điều phối một hoặc nhiều service, cache, transaction. Input/Output là dataclass DTO | Import `fastapi`, `sqlalchemy`, `redis`, repository, adapter cụ thể |
| `modules/<m>/entity.py` | Dataclass entity + lỗi nghiệp vụ (kế thừa `core.errors`) | Import framework |
| `modules/<m>/interfaces.py` | `I<M>Service`, `I<M>Repository` (ABC + `@abstractmethod`) | Implementation |
| `modules/<m>/service.py` | Quy tắc nghiệp vụ của MỘT module, chỉ dùng repository của chính module đó | Import module khác (phối hợp nhiều module thì làm ở usecase), import SQLAlchemy |
| `modules/<m>/repository.py` | ORM model + `Postgres<M>Repository`, ánh xạ model ↔ entity | Logic nghiệp vụ |
| `shared/` | Interface hạ tầng dùng chung (`ICache`, `IDatabaseHealth`…) + adapter (`redis_cache.py`…) | Logic nghiệp vụ |
| `core/` | Config, kết nối DB/Redis, lỗi gốc | Phụ thuộc tầng trên |

Luật được **máy kiểm tra**:
- `lint-imports` (file `.importlinter`, nằm trong `make lint`) kiểm tra hướng phụ thuộc.
- `tests/unit/test_architecture.py` kiểm tra: mỗi module có `I<M>Service`/`I<M>Repository`; service và mọi `...UseCase` kế thừa interface.

Không được nới lỏng hai file này.

# Mẫu tham chiếu

Module mẫu đầy đủ là **user** (đăng ký, xem, liệt kê, có cache Redis). Khi thêm tính năng, **sao chép đúng khuôn** của nó:

- `backend/app/modules/user/{entity,interfaces,service,repository}.py`
- `backend/app/usecases/user/{interfaces,mappers,register_user,list_users,get_user}.py`
- `backend/app/controllers/user_controller.py`, `backend/app/container.py`, `backend/app/main.py`
- `backend/tests/fakes/*`, `backend/tests/unit/**`, `backend/tests/integration/**`

(Bản gốc nằm ở `.claude/skills/project-scaffold/reference/backend/` nếu cần so sánh.)

# Công thức: thêm tính năng mới (ví dụ module `order`)

1. **Entity:** `modules/order/entity.py`, gồm dataclass `Order` (frozen) và các lỗi `OrderNotFoundError(NotFoundError)`, `InvalidOrderError(ValidationError)`…
2. **Interfaces:** `modules/order/interfaces.py`, gồm `IOrderRepository`, `IOrderService` (ABC).
3. **Fake + test service trước:**
   - `tests/fakes/in_memory_order_repository.py` (implement `IOrderRepository`).
   - `tests/unit/modules/order/test_order_service.py`: viết test cho từng quy tắc và từng lỗi.
4. **Service:** `modules/order/service.py`, `OrderService(IOrderService)`. Chạy `make test-unit-be`.
5. **Repository:**
   - `modules/order/repository.py`, gồm `OrderModel(Base)` và `PostgresOrderRepository(IOrderRepository)`. Mỗi method ghi thì `commit()`.
   - `tests/integration/test_order_repository.py`.
   - `make migration name=create_orders`, đọc lại file trong `migrations/versions/`, rồi `make migrate`.
6. **Usecase:**
   - `usecases/order/interfaces.py`, gồm DTO `CreateOrderInput`/`OrderOutput` và `ICreateOrderUseCase`.
   - `usecases/order/create_order.py`, gồm `CreateOrderUseCase(ICreateOrderUseCase)`, nhận **interface** service qua `__init__`.
   - `tests/unit/usecases/order/test_create_order.py`: dùng service thật với fake repository, hoặc fake service.
7. **Controller:**
   - `controllers/order_controller.py`: `router = APIRouter(prefix="/api/v1/orders")`, kèm hàm placeholder `def get_create_order() -> ICreateOrderUseCase: raise NotImplementedError`, và route dùng `Depends(get_create_order)`.
   - `tests/unit/controllers/test_order_controller.py`: dùng `create_app(wire_dependencies=False)` và `app.dependency_overrides[...] = lambda: FakeCreateOrder()`.
8. **Wiring:**
   - `container.py`: thêm `build_order_service`, `build_create_order` (dùng `Depends` để nhận session/cache), và thêm cặp `order_controller.get_create_order: build_create_order` vào `PROVIDERS`.
   - `main.py`: thêm `order_controller.router` vào `ROUTERS`.
9. **Hurl:** `tests/api/orders.hurl`, kiểm tra cả trường hợp thành công lẫn các mã lỗi.
10. `pm verify`.

# Lỗi và mã HTTP

- Service ném lỗi nghiệp vụ (`ValidationError`, `NotFoundError`, `ConflictError` trong `core/errors.py`, hoặc lớp con).
- `controllers/error_handlers.py` ánh xạ sang 422/404/409 với body `{"error": {"code", "message"}}`. Thêm loại lỗi mới thì thêm vào `STATUS_BY_ERROR`.
- Pydantic tự trả 422 khi sai kiểu dữ liệu. Quy tắc nghiệp vụ (định dạng, độ dài, trùng lặp) kiểm tra ở **service**, để unit test được.

# Transaction & cache

- Session là theo request (`core/database.get_session`). Mỗi method ghi của repository tự `commit()`. Cần ghi nhiều bảng trong một transaction: thêm interface `IUnitOfWork` vào `shared/` (kèm ADR), không gọi `session` trong usecase.
- Cache qua `ICache`. Key có tiền tố theo resource (`orders:list:…`). Usecase ghi dữ liệu phải `delete_prefix` các key liên quan.

# Test từng tầng

| Tầng | Loại test | Phụ thuộc thay bằng |
|---|---|---|
| service | unit | `InMemory<M>Repository` |
| usecase | unit | service thật + fake repo, hoặc fake service; `FakeCache` |
| controller | unit (TestClient) | fake usecase qua `dependency_overrides` |
| repository | integration (`@pytest.mark.integration`) | Postgres thật (DB `app_test`) |
| toàn tuyến | Hurl | stack thật qua Traefik |

Coverage unit ≥ 80%. Các adapter (`repository.py`, `redis_cache.py`, `container.py`, `main.py`…) không tính coverage vì đã kiểm bằng integration + Hurl (cấu hình ở `pyproject.toml`).
