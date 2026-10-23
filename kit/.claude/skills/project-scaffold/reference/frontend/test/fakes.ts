import type { Health, IHealthApi, IUserApi, NewUser, User } from "@/services/api/interfaces";

export class FakeUserApi implements IUserApi {
  users: User[] = [];
  failWith: Error | null = null;
  private nextId = 1;

  async list(): Promise<User[]> {
    if (this.failWith) throw this.failWith;
    return [...this.users].reverse();
  }

  async register(input: NewUser): Promise<User> {
    if (this.failWith) throw this.failWith;
    const user: User = { id: this.nextId++, email: input.email, fullName: input.fullName, createdAt: null };
    this.users.push(user);
    return user;
  }
}

export class FakeHealthApi implements IHealthApi {
  constructor(public result: Health | Error = { status: "ok", database: "ok", cache: "ok" }) {}

  async check(): Promise<Health> {
    if (this.result instanceof Error) throw this.result;
    return this.result;
  }
}
