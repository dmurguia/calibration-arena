import http from "node:http";
import { readFile, stat } from "node:fs/promises";
import path from "node:path";
import { build, root } from "./build.mjs";

if (!process.argv.includes("--production")) await build();
const base = path.join(root, "dist");
const types = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
  ".png": "image/png",
  ".woff2": "font/woff2",
  ".json": "application/json",
  ".txt": "text/plain; charset=utf-8",
  ".xml": "application/xml",
};
const server = http.createServer(async (req, res) => {
  try {
    if (!["GET", "HEAD"].includes(req.method)) {
      res.writeHead(405, { Allow: "GET, HEAD" });
      res.end();
      return;
    }
    const pathname = decodeURIComponent(
      new URL(req.url, "http://localhost").pathname,
    );
    let file = path.resolve(base, "." + pathname);
    if (!file.startsWith(base + path.sep) && file !== base) {
      res.writeHead(403);
      res.end();
      return;
    }
    try {
      if ((await stat(file)).isDirectory())
        file = path.join(file, "index.html");
    } catch {}
    const body = await readFile(file);
    res.writeHead(200, {
      "Content-Type": types[path.extname(file)] || "application/octet-stream",
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
      "Referrer-Policy": "strict-origin-when-cross-origin",
      "Content-Security-Policy":
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'; frame-ancestors 'none'",
    });
    res.end(req.method === "HEAD" ? undefined : body);
  } catch {
    res.writeHead(404, { "Content-Type": "text/html; charset=utf-8" });
    res.end(
      req.method === "HEAD"
        ? undefined
        : await readFile(path.join(base, "404.html")),
    );
  }
});
server.on("error", (error) => {
  console.error(`Preview could not start: ${error.code}. Choose another PORT.`);
  process.exitCode = 1;
});
server.listen(Number(process.env.PORT || 4317), "127.0.0.1", () =>
  console.log(
    `Calibrated marketing: http://127.0.0.1:${server.address().port}/\nCompare directions: http://127.0.0.1:${server.address().port}/review/`,
  ),
);
