"""Kiểm tra kiến trúc: mỗi module phải có đủ interface và implementation phải kế thừa interface."""
import importlib
import inspect
import pkgutil
from abc import ABC
from pathlib import Path

import pytest

import app.modules
import app.usecases

APP_DIR = Path(__file__).resolve().parents[2] / "app"
MODULE_NAMES = [info.name for info in pkgutil.iter_modules(app.modules.__path__) if info.ispkg]
USECASE_AREAS = [info.name for info in pkgutil.iter_modules(app.usecases.__path__) if info.ispkg]


def _pascal(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


def _interfaces_in(module_path: str) -> list[type]:
    module = importlib.import_module(module_path)
    return [obj for name, obj in inspect.getmembers(module, inspect.isclass)
            if name.startswith("I") and issubclass(obj, ABC) and obj.__module__ == module.__name__]


@pytest.mark.parametrize("name", MODULE_NAMES)
def test_module_has_required_files(name: str) -> None:
    for filename in ("entity.py", "interfaces.py", "service.py", "repository.py"):
        assert (APP_DIR / "modules" / name / filename).exists(), f"modules/{name}/{filename} thiếu"


@pytest.mark.parametrize("name", MODULE_NAMES)
def test_module_declares_service_and_repository_interfaces(name: str) -> None:
    names = {interface.__name__ for interface in _interfaces_in(f"app.modules.{name}.interfaces")}
    assert f"I{_pascal(name)}Service" in names
    assert f"I{_pascal(name)}Repository" in names


@pytest.mark.parametrize("name", MODULE_NAMES)
def test_module_service_implements_interface(name: str) -> None:
    interfaces = importlib.import_module(f"app.modules.{name}.interfaces")
    service = importlib.import_module(f"app.modules.{name}.service")
    interface = getattr(interfaces, f"I{_pascal(name)}Service")
    implementations = [obj for _, obj in inspect.getmembers(service, inspect.isclass)
                       if obj.__module__ == service.__name__ and issubclass(obj, interface)]
    assert implementations, f"modules/{name}/service.py phải có class kế thừa {interface.__name__}"


@pytest.mark.parametrize("area", USECASE_AREAS)
def test_every_usecase_class_implements_an_interface(area: str) -> None:
    interfaces = _interfaces_in(f"app.usecases.{area}.interfaces")
    package = importlib.import_module(f"app.usecases.{area}")
    for info in pkgutil.iter_modules(package.__path__):
        if info.name in {"interfaces", "mappers"}:
            continue
        module = importlib.import_module(f"app.usecases.{area}.{info.name}")
        classes = [obj for _, obj in inspect.getmembers(module, inspect.isclass)
                   if obj.__module__ == module.__name__ and obj.__name__.endswith("UseCase")]
        assert classes, f"usecases/{area}/{info.name}.py phải có class ...UseCase"
        for cls in classes:
            assert any(issubclass(cls, interface) for interface in interfaces), (
                f"{cls.__name__} phải kế thừa một interface trong usecases/{area}/interfaces.py")
