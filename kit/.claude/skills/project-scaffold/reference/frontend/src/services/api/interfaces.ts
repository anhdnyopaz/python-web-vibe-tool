// Interface (port) mà component được phép dùng. Implementation HTTP nằm ở *-api.ts.
export type User = {
  id: number;
  email: string;
  fullName: string;
  createdAt: string | null;
};

export type NewUser = { email: string; fullName: string };

export type ServiceState = "ok" | "down";
export type Health = { status: ServiceState; database: ServiceState; cache: ServiceState };

export interface IUserApi {
  list(): Promise<User[]>;
  register(input: NewUser): Promise<User>;
}

export interface IHealthApi {
  check(): Promise<Health>;
}
