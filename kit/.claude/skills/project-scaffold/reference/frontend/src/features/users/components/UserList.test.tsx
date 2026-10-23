import { describe, expect, it } from "bun:test";
import { render, screen } from "@testing-library/react";
import { UserList } from "./UserList";

describe("UserList", () => {
  it("shows an invitation when empty", () => {
    render(<UserList users={[]} />);
    expect(screen.getByTestId("user-list-empty")).toHaveTextContent("Chưa có ai");
  });

  it("renders each user", () => {
    render(<UserList users={[{ id: 1, email: "an@example.com", fullName: "An", createdAt: null }]} />);
    expect(screen.getByText("An")).toBeInTheDocument();
    expect(screen.getByText("an@example.com")).toBeInTheDocument();
  });
});
