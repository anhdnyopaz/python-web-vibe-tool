FROM mcr.microsoft.com/playwright:v1.64.1-noble
COPY --from=oven/bun:1.4.4 /usr/local/bin/bun /usr/local/bin/bun
WORKDIR /e2e
CMD ["sh", "-c", "bun install --frozen-lockfile && bun run test"]
