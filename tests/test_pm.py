from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1] / "kit" / ".claude" / "tools"
spec = importlib.util.spec_from_file_location("pm", KIT / "pm.py")
pm = importlib.util.module_from_spec(spec)
sys.modules["pm"] = pm
spec.loader.exec_module(pm)


class PMTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self._old_env = os.environ.get("PM_ROOT")
        os.environ["PM_ROOT"] = str(self.root)
        self.run_pm("init", "--name", "Shop hoa")
        config = json.loads((self.root / ".pm/config.json").read_text())
        config["gates"] = {"lint": "true", "unit": "true", "api": "true", "e2e": "true"}
        (self.root / ".pm/config.json").write_text(json.dumps(config))
        (self.root / "backend").mkdir()
        (self.root / "backend/app.py").write_text("print('v1')\n")

    def tearDown(self) -> None:
        if self._old_env is None:
            os.environ.pop("PM_ROOT", None)
        else:
            os.environ["PM_ROOT"] = self._old_env
        self._tmp.cleanup()

    def run_pm(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = pm.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def ok(self, *argv: str) -> str:
        code, out, err = self.run_pm(*argv)
        self.assertEqual(code, 0, msg=err)
        return out

    def fail(self, *argv: str) -> str:
        code, _, err = self.run_pm(*argv)
        self.assertEqual(code, 1)
        return err

    def board(self) -> dict:
        return json.loads((self.root / ".pm/board.json").read_text())

    def set_gate(self, name: str, command: str) -> None:
        path = self.root / ".pm/config.json"
        config = json.loads(path.read_text())
        config["gates"][name] = command
        path.write_text(json.dumps(config))

    def add_ready_task(self, title: str = "Đăng ký", *extra: str) -> str:
        self.ok("add", title, "--ac", "Given A When B Then C", *extra)
        return self.board()["tasks"][-1]["id"]


class InitTests(PMTestCase):
    def test_init_creates_board_config_and_markdown(self) -> None:
        self.assertEqual(self.board()["project"]["name"], "Shop hoa")
        self.assertTrue((self.root / "docs/BOARD.md").exists())
        self.assertTrue((self.root / "docs/decisions").is_dir())

    def test_init_refuses_twice_without_force(self) -> None:
        self.assertIn("đã được khởi tạo", self.fail("init", "--name", "X"))
        self.ok("init", "--name", "X", "--force")
        self.assertEqual(self.board()["project"]["name"], "X")

    def test_commands_require_init(self) -> None:
        with tempfile.TemporaryDirectory() as other:
            os.environ["PM_ROOT"] = other
            self.assertIn("chưa khởi tạo", self.fail("list"))


class TaskTests(PMTestCase):
    def test_add_assigns_sequential_ids_and_fields(self) -> None:
        self.ok("add", "Đăng ký", "--priority", "p1", "--api", "--ui", "--ac", "AC 1", "--ac", "AC 2",
                "--milestone", "M1")
        self.ok("add", "Đăng nhập")
        first, second = self.board()["tasks"]
        self.assertEqual((first["id"], second["id"]), ("T-001", "T-002"))
        self.assertEqual(first["priority"], "P1")
        self.assertTrue(first["needs_api"] and first["needs_ui"])
        self.assertEqual([c["text"] for c in first["acceptance"]], ["AC 1", "AC 2"])
        self.assertEqual(second["priority"], "P2")
        self.assertFalse(second["needs_api"])

    def test_add_rejects_bad_priority_and_unknown_dependency(self) -> None:
        self.assertIn("Ưu tiên", self.fail("add", "X", "--priority", "P9"))
        self.assertIn("Không tìm thấy", self.fail("add", "X", "--after", "T-099"))

    def test_edit_appends_ac_and_toggles_flags(self) -> None:
        task_id = self.add_ready_task("Đăng ký", "--api")
        self.ok("edit", task_id, "--ac", "AC mới", "--no-api", "--title", "Đăng ký tài khoản")
        task = self.board()["tasks"][0]
        self.assertEqual(len(task["acceptance"]), 2)
        self.assertFalse(task["needs_api"])
        self.assertEqual(task["title"], "Đăng ký tài khoản")

    def test_start_sets_branch_and_enforces_wip_limit(self) -> None:
        first = self.add_ready_task("Đăng ký tài khoản")
        second = self.add_ready_task("Đăng nhập")
        out = self.ok("start", first)
        self.assertIn("feat/t-001-dang-ky-tai-khoan", out)
        self.assertIn("Giới hạn 1", self.fail("start", second))

    def test_start_requires_acceptance_criteria_and_dependencies(self) -> None:
        self.ok("add", "Không có AC")
        self.assertIn("tiêu chí", self.fail("start", "T-001"))
        self.ok("edit", "T-001", "--ac", "AC")
        dependent = self.add_ready_task("Phụ thuộc", "--after", "T-001")
        self.assertIn("phải làm sau", self.fail("start", dependent))

    def test_block_and_unblock(self) -> None:
        task_id = self.add_ready_task()
        self.ok("block", task_id, "Chờ PO chọn cổng thanh toán")
        self.assertEqual(self.board()["tasks"][0]["status"], "blocked")
        self.ok("unblock", task_id)
        self.assertEqual(self.board()["tasks"][0]["status"], "todo")
        self.assertIn("không bị chặn", self.fail("unblock", task_id))

    def test_ac_marks_and_validates_index(self) -> None:
        task_id = self.add_ready_task()
        self.ok("ac", task_id, "1", "--evidence", "tests/unit/test_x.py")
        criterion = self.board()["tasks"][0]["acceptance"][0]
        self.assertTrue(criterion["done"])
        self.assertEqual(criterion["evidence"], "tests/unit/test_x.py")
        self.ok("ac", task_id, "1", "--undo")
        self.assertFalse(self.board()["tasks"][0]["acceptance"][0]["done"])
        self.assertIn("chỉ có 1", self.fail("ac", task_id, "5"))

    def test_next_prefers_priority_and_ready_dependencies(self) -> None:
        self.add_ready_task("Thấp", "--priority", "P3")
        self.add_ready_task("Cao nhưng chờ", "--priority", "P0", "--after", "T-001")
        self.add_ready_task("Trung bình", "--priority", "P1")
        self.assertIn("T-003", self.ok("next"))


class VerifyAndSubmitTests(PMTestCase):
    def start_task(self, *extra: str) -> str:
        task_id = self.add_ready_task("Đăng ký", *extra)
        self.ok("start", task_id)
        self.ok("ac", task_id, "1")
        return task_id

    def test_verify_runs_required_gates_for_task(self) -> None:
        task_id = self.start_task("--api")
        self.ok("verify")
        gates = self.board()["tasks"][0]["verify"]["gates"]
        self.assertEqual(sorted(gates), ["api", "lint", "unit"])
        self.ok("submit", task_id)
        self.assertEqual(self.board()["tasks"][0]["status"], "done")

    def test_failing_gate_is_reported_and_blocks_submit(self) -> None:
        task_id = self.start_task()
        self.set_gate("unit", "echo 'boom: 1 failed' && exit 1")
        code, out, err = self.run_pm("verify")
        self.assertEqual(code, 1)
        self.assertIn("boom: 1 failed", out)
        self.assertIn("KHÔNG đạt", err)
        self.assertIn("verify", self.fail("submit", task_id))

    def test_submit_requires_reverify_after_code_change(self) -> None:
        task_id = self.start_task()
        self.ok("verify")
        (self.root / "backend/app.py").write_text("print('v2')\n")
        self.assertIn("sau lần sửa code", self.fail("submit", task_id))
        self.ok("verify")
        self.ok("submit", task_id)

    def test_submit_requires_all_acceptance_criteria(self) -> None:
        task_id = self.add_ready_task()
        self.ok("edit", task_id, "--ac", "AC 2")
        self.ok("start", task_id)
        self.ok("ac", task_id, "1")
        self.ok("verify")
        self.assertIn("Còn tiêu chí chưa đạt: 2", self.fail("submit", task_id))

    def test_submit_with_acceptance_goes_to_review_then_accept_or_reject(self) -> None:
        path = self.root / ".pm/config.json"
        config = json.loads(path.read_text())
        config["require_acceptance"] = True
        path.write_text(json.dumps(config))
        task_id = self.start_task()
        self.ok("verify")
        self.ok("submit", task_id)
        self.assertEqual(self.board()["tasks"][0]["status"], "review")
        self.ok("reject", task_id, "Nút bấm khó thấy")
        task = self.board()["tasks"][0]
        self.assertEqual(task["status"], "doing")
        self.assertNotIn("verify", task)
        self.ok("verify")
        self.ok("submit", task_id)
        self.ok("accept", task_id)
        self.assertEqual(self.board()["tasks"][0]["status"], "done")

    def test_check_fresh_for_commit_hook(self) -> None:
        self.assertIn("chưa từng kiểm tra", self.fail("check-fresh"))
        self.ok("verify", "--all")
        self.ok("check-fresh")
        (self.root / "backend/new.py").write_text("x = 1\n")
        self.fail("check-fresh")

    def test_check_fresh_ignores_files_outside_source_paths(self) -> None:
        self.ok("verify", "--all")
        (self.root / "docs/notes.md").write_text("ghi chú\n")
        self.ok("check-fresh")

    def test_fingerprint_respects_gitignore(self) -> None:
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        (self.root / ".gitignore").write_text("__pycache__/\n")
        self.ok("verify", "--all")
        (self.root / "backend/__pycache__").mkdir()
        (self.root / "backend/__pycache__/app.cpython-312.pyc").write_bytes(b"\0")
        self.ok("check-fresh")


class FinishAndContextTests(PMTestCase):
    def git(self, *argv: str) -> str:
        return subprocess.run(["git", *argv], cwd=self.root, check=True, capture_output=True,
                              text=True).stdout.strip()

    def setUp(self) -> None:
        super().setUp()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "Test")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "chore: init")

    def start_on_branch(self) -> str:
        task_id = self.add_ready_task()
        self.ok("start", task_id)
        self.git("switch", "-q", "-c", self.board()["tasks"][0]["branch"])
        (self.root / "backend/app.py").write_text("print('v2')\n")
        self.ok("ac", task_id, "1")
        self.ok("verify")
        return task_id

    def test_finish_submits_commits_merges_and_deletes_branch(self) -> None:
        task_id = self.start_on_branch()
        branch = self.board()["tasks"][0]["branch"]
        self.ok("finish", task_id, "-m", f"feat({task_id}): add sign up")
        self.assertEqual(self.board()["tasks"][0]["status"], "done")
        self.assertEqual(self.git("rev-parse", "--abbrev-ref", "HEAD"), "main")
        self.assertEqual(self.git("log", "-1", "--format=%s"), f"Merge {task_id}: add sign up")
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertEqual(self.git("branch", "--list", branch), "")

    def test_finish_validates_message_branch_and_freshness(self) -> None:
        task_id = self.start_on_branch()
        self.assertIn("Commit message", self.fail("finish", task_id, "-m", "add sign up"))
        self.assertIn("Commit message", self.fail("finish", task_id, "-m", "feat(T-999): x"))
        (self.root / "backend/app.py").write_text("print('v3')\n")
        self.assertIn("verify", self.fail("finish", task_id, "-m", f"feat({task_id}): x"))
        self.assertEqual(self.board()["tasks"][0]["status"], "doing")
        self.git("switch", "-q", "main")
        self.assertIn("nhánh của task", self.fail("finish", task_id, "-m", f"feat({task_id}): x"))

    def test_context_summarizes_task_decisions_and_code_map(self) -> None:
        task_id = self.add_ready_task("Đăng ký", "--api")
        self.ok("ask", "Cho đặt trước tối đa mấy ngày? Đề xuất: 14 ngày.")
        self.ok("answer", "Q-001", "Đồng ý.")
        (self.root / "backend/app/modules/order").mkdir(parents=True)
        (self.root / "backend/app/modules/order/service.py").write_text("x = 1\n")
        (self.root / "frontend/src/app/orders").mkdir(parents=True)
        (self.root / "frontend/src/app/orders/page.tsx").write_text("x\n")
        out = self.ok("context")
        self.assertIn(f"{task_id} · Đăng ký", out)
        self.assertIn("Q-001: Cho đặt trước tối đa mấy ngày? Đề xuất: 14 ngày. → Đồng ý.", out)
        self.assertIn("Module backend: order", out)
        self.assertIn("Trang: /orders", out)


class InboxQuestionTests(PMTestCase):
    def test_request_inbox_and_add_from_request(self) -> None:
        self.ok("request", "feature", "Lọc đơn theo ngày")
        self.assertIn("R-001", self.ok("inbox"))
        self.ok("add", "Bộ lọc ngày", "--from", "R-001", "--ac", "AC")
        request = self.board()["requests"][0]
        self.assertEqual(request["status"], "triaged")
        self.assertEqual(request["tasks"], ["T-001"])
        self.assertIn("trống", self.ok("inbox"))

    def test_triage_links_tasks(self) -> None:
        self.ok("request", "bug", "Nút lưu không chạy")
        self.add_ready_task("Sửa nút lưu", "--type", "bug")
        self.ok("triage", "R-001", "--tasks", "T-001", "--note", "trùng lỗi cũ")
        self.assertEqual(self.board()["requests"][0]["tasks"], ["T-001"])

    def test_ask_and_answer(self) -> None:
        self.ok("ask", "Có cần đăng nhập bằng Google không?")
        self.assertIn("Q-001", self.ok("questions"))
        self.ok("answer", "Q-001", "Không cần")
        question = self.board()["questions"][0]
        self.assertEqual((question["status"], question["answer"]), ("answered", "Không cần"))

    def test_status_brief_mentions_pending_items(self) -> None:
        self.ok("request", "feature", "abc")
        self.ok("ask", "xyz?")
        out = self.ok("status", "--brief")
        self.assertIn("[pm]", out)
        self.assertIn("1 yêu cầu mới", out)
        self.assertIn("1 câu hỏi", out)


class RecordTests(PMTestCase):
    def test_adr_numbering_and_slug(self) -> None:
        self.ok("adr", "Dùng Đăng nhập bằng email")
        self.ok("adr", "Chọn Traefik")
        names = sorted(p.name for p in (self.root / "docs/decisions").glob("*.md"))
        self.assertEqual(names, ["0001-dung-dang-nhap-bang-email.md", "0002-chon-traefik.md"])

    def test_release_writes_changelog_once_per_task(self) -> None:
        task_id = self.add_ready_task("Đăng ký")
        self.ok("start", task_id)
        self.ok("ac", task_id, "1")
        self.ok("verify")
        self.ok("submit", task_id)
        self.ok("release", "v0.1.0")
        changelog = (self.root / "CHANGELOG.md").read_text()
        self.assertIn("## v0.1.0", changelog)
        self.assertIn("Đăng ký (T-001)", changelog)
        self.assertIn("Không có task", self.fail("release", "v0.2.0"))
        self.assertIn("đã tồn tại", self.fail("release", "v0.1.0"))

    def test_link_and_deploy_log(self) -> None:
        self.ok("link", "share", "https://abc.trycloudflare.com")
        self.assertEqual(json.loads((self.root / ".pm/config.json").read_text())["links"]["share"],
                         "https://abc.trycloudflare.com")
        self.ok("link", "share", "--remove")
        self.ok("deploy-log", "--version", "v0.1.0", "--target", "vps", "--result", "success")
        self.assertEqual(self.board()["deploys"][0]["target"], "vps")
        self.assertIn("v0.1.0", (self.root / "docs/BOARD.md").read_text())


class DashboardActionTests(PMTestCase):
    def store(self):
        return pm.Store(self.root)

    def test_request_question_and_review_actions(self) -> None:
        store = self.store()
        pm.handle_dashboard_action(store, "/api/requests", {"kind": "bug", "text": "Lỗi nút", "task": None})
        self.ok("ask", "Màu chủ đạo?")
        pm.handle_dashboard_action(store, "/api/questions/Q-001/answer", {"text": "Xanh lá"})
        board = self.board()
        self.assertEqual(board["requests"][0]["kind"], "bug")
        self.assertEqual(board["questions"][0]["answer"], "Xanh lá")

    def test_review_actions_require_review_status_and_reason(self) -> None:
        store = self.store()
        task_id = self.add_ready_task()
        with self.assertRaises(pm.PMError):
            pm.handle_dashboard_action(store, f"/api/tasks/{task_id}/accept", {})
        board = self.board()
        board["tasks"][0]["status"] = "review"
        (self.root / ".pm/board.json").write_text(json.dumps(board))
        with self.assertRaises(pm.PMError):
            pm.handle_dashboard_action(store, f"/api/tasks/{task_id}/reject", {"reason": " "})
        pm.handle_dashboard_action(store, f"/api/tasks/{task_id}/reject", {"reason": "Sai màu"})
        self.assertEqual(self.board()["tasks"][0]["status"], "doing")

    def test_unknown_action_and_empty_request(self) -> None:
        store = self.store()
        with self.assertRaises(pm.PMError):
            pm.handle_dashboard_action(store, "/api/whatever", {})
        with self.assertRaises(pm.PMError):
            pm.handle_dashboard_action(store, "/api/requests", {"kind": "feature", "text": "  "})

    def test_state_contains_summary(self) -> None:
        self.add_ready_task()
        state = pm.dashboard_state(self.store())
        self.assertEqual(state["summary"]["total"], 1)
        self.assertEqual(state["summary"]["next"], "T-001")
        self.assertIn("app", state["links"])


class DashboardServerTests(PMTestCase):
    def test_server_requires_token_for_writes(self) -> None:
        import threading
        import urllib.error
        import urllib.request

        handler = type("H", (pm.DashboardHandler,), {"store": pm.Store(self.root), "token": "secret",
                                                    "allowed_hosts": {"127.0.0.1", "localhost"}})
        server = pm.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        port = server.server_address[1]
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            html = urllib.request.urlopen(f"http://127.0.0.1:{port}/").read().decode()
            self.assertIn('"secret"', html)
            state = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/api/state").read())
            self.assertEqual(state["project"]["name"], "Shop hoa")
            body = json.dumps({"kind": "feature", "text": "abc"}).encode()
            bad = urllib.request.Request(f"http://127.0.0.1:{port}/api/requests", data=body, method="POST")
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(bad)
            self.assertEqual(ctx.exception.code, 403)
            good = urllib.request.Request(f"http://127.0.0.1:{port}/api/requests", data=body, method="POST",
                                          headers={"X-PM-Token": "secret", "Content-Type": "application/json"})
            self.assertIn("R-001", json.loads(urllib.request.urlopen(good).read())["message"])
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
