// Luật kiến trúc frontend: component/feature chỉ dùng interface qua useApi(), không tự gọi HTTP.
import { describe, expect, it } from "bun:test";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

const SRC = join(import.meta.dir);

function files(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    return statSync(path).isDirectory() ? files(path) : /\.(ts|tsx)$/.test(name) ? [path] : [];
  });
}

const features = files(join(SRC, "features")).filter((f) => !/\.test\.tsx?$/.test(f));

describe("architecture", () => {
  it("features never import HTTP implementations or call fetch directly", () => {
    const offenders = features.filter((file) => {
      const code = readFileSync(file, "utf8");
      return /from ["']@\/services\/api\/(http-client|[\w-]+-api)["']/.test(code) || /\bfetch\(/.test(code);
    });
    expect(offenders).toEqual([]);
  });

  it("pages under src/app stay thin (no fetch)", () => {
    const offenders = files(join(SRC, "app")).filter((file) => !file.endsWith("providers.tsx") && /\bfetch\(/.test(readFileSync(file, "utf8")));
    expect(offenders).toEqual([]);
  });
});
