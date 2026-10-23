import { describe, expect, it } from "bun:test";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ApiProvider } from "@/services/api-context";
import { FakeHealthApi, FakeUserApi } from "../../../../test/fakes";
import { UsersPanel } from "./UsersPanel";

function setup(userApi: FakeUserApi) {
  render(
    <ApiProvider apis={{ userApi, healthApi: new FakeHealthApi() }}>
      <UsersPanel />
    </ApiProvider>,
  );
}

describe("UsersPanel", () => {
  it("lists users and refreshes after registering", async () => {
    const userApi = new FakeUserApi();
    await userApi.register({ email: "an@example.com", fullName: "An" });
    setup(userApi);
    expect(await screen.findByText("An")).toBeInTheDocument();

    await userEvent.type(screen.getByTestId("full-name"), "Bình");
    await userEvent.type(screen.getByTestId("email"), "binh@example.com");
    await userEvent.click(screen.getByTestId("register-submit"));

    expect(await screen.findByText("Bình")).toBeInTheDocument();
  });

  it("shows an error when loading fails", async () => {
    const userApi = new FakeUserApi();
    userApi.failWith = new Error("Không kết nối được máy chủ");
    setup(userApi);
    expect(await screen.findByRole("alert")).toHaveTextContent("Không kết nối được máy chủ");
  });
});
