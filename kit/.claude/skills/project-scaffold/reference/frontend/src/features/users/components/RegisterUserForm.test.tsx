import { describe, expect, it, mock } from "bun:test";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ApiProvider } from "@/services/api-context";
import { FakeHealthApi, FakeUserApi } from "../../../../test/fakes";
import { RegisterUserForm } from "./RegisterUserForm";

function setup(userApi = new FakeUserApi()) {
  const onRegistered = mock(() => {});
  render(
    <ApiProvider apis={{ userApi, healthApi: new FakeHealthApi() }}>
      <RegisterUserForm onRegistered={onRegistered} />
    </ApiProvider>,
  );
  return { userApi, onRegistered };
}

describe("RegisterUserForm", () => {
  it("registers a user and clears the form", async () => {
    const { userApi, onRegistered } = setup();
    await userEvent.type(screen.getByTestId("full-name"), "Nguyễn An");
    await userEvent.type(screen.getByTestId("email"), "an@example.com");
    await userEvent.click(screen.getByTestId("register-submit"));

    expect(userApi.users[0]).toMatchObject({ email: "an@example.com", fullName: "Nguyễn An" });
    expect(onRegistered).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId("email")).toHaveValue("");
  });

  it("shows the server error message", async () => {
    const userApi = new FakeUserApi();
    userApi.failWith = new Error("Email an@example.com đã được đăng ký");
    setup(userApi);
    await userEvent.type(screen.getByTestId("full-name"), "An");
    await userEvent.type(screen.getByTestId("email"), "an@example.com");
    await userEvent.click(screen.getByTestId("register-submit"));

    expect(await screen.findByRole("alert")).toHaveTextContent("đã được đăng ký");
  });
});
