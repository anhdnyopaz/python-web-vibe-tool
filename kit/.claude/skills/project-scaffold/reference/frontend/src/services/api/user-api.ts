import type { HttpClient } from "./http-client";
import type { IUserApi, NewUser, User } from "./interfaces";

type UserDto = { id: number; email: string; full_name: string; created_at: string | null };

const toUser = (dto: UserDto): User => ({
  id: dto.id,
  email: dto.email,
  fullName: dto.full_name,
  createdAt: dto.created_at,
});

export class HttpUserApi implements IUserApi {
  constructor(private readonly http: HttpClient) {}

  async list(): Promise<User[]> {
    const body = await this.http<{ items: UserDto[] }>("/api/v1/users");
    return body.items.map(toUser);
  }

  async register(input: NewUser): Promise<User> {
    const dto = await this.http<UserDto>("/api/v1/users", {
      method: "POST",
      body: JSON.stringify({ email: input.email, full_name: input.fullName }),
    });
    return toUser(dto);
  }
}
