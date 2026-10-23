FROM oven/bun:1.4.4 AS deps
WORKDIR /app
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

# ---- dev: hot reload, code được mount từ máy vào ----
FROM deps AS dev
ENV NEXT_TELEMETRY_DISABLED=1
COPY . .
CMD ["bun", "--bun", "next", "dev", "--hostname", "0.0.0.0", "--port", "3000"]

# ---- build bản production ----
FROM deps AS build
ENV NEXT_TELEMETRY_DISABLED=1
COPY . .
RUN bun --bun next build

# ---- prod: chỉ chứa output standalone, user không phải root ----
FROM oven/bun:1.4.4-slim AS prod
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
COPY --from=build --chown=bun:bun /app/.next/standalone ./
COPY --from=build --chown=bun:bun /app/.next/static ./.next/static
COPY --from=build --chown=bun:bun /app/public ./public
USER bun
EXPOSE 3000
CMD ["bun", "server.js"]
