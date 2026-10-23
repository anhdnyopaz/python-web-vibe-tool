import { describe, expect, it } from "bun:test";
import { render, screen, waitFor } from "@testing-library/react";
import { ApiProvider } from "@/services/api-context";
import { FakeHealthApi, FakeUserApi } from "../../../../test/fakes";
import { SystemStatus } from "./SystemStatus";

function renderWith(healthApi: FakeHealthApi) {
  return render(
    <ApiProvider apis={{ healthApi, userApi: new FakeUserApi() }}>
      <SystemStatus />
    </ApiProvider>,
  );
}

describe("SystemStatus", () => {
  it("shows every part as working when healthy", async () => {
    renderWith(new FakeHealthApi());
    await waitFor(() => expect(screen.getAllByText("Hoạt động")).toHaveLength(4));
  });

  it("marks only the failing dependency as down", async () => {
    renderWith(new FakeHealthApi({ status: "down", database: "down", cache: "ok" }));
    await screen.findAllByText("Không phản hồi");
    expect(screen.getByTestId("status-database").dataset.state).toBe("down");
    expect(screen.getByTestId("status-cache").dataset.state).toBe("ok");
  });

  it("marks backend parts down when the API is unreachable", async () => {
    renderWith(new FakeHealthApi(new Error("offline")));
    await waitFor(() => expect(screen.getAllByText("Không phản hồi")).toHaveLength(3));
  });
});
