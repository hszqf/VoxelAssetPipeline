import { createReadStream, existsSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join, normalize, resolve, sep } from "node:path";

const root = resolve(process.cwd());
const port = Number.parseInt(process.argv[2] ?? "5177", 10);
const host = "127.0.0.1";

const contentTypes = new Map([
  [".html", "text/html; charset=utf-8"],
  [".css", "text/css; charset=utf-8"],
  [".js", "text/javascript; charset=utf-8"],
  [".mjs", "text/javascript; charset=utf-8"],
  [".json", "application/json; charset=utf-8"],
  [".png", "image/png"],
  [".svg", "image/svg+xml; charset=utf-8"],
  [".vox", "application/octet-stream"],
]);

function send(res, status, body) {
  res.writeHead(status, { "Content-Type": "text/plain; charset=utf-8" });
  res.end(body);
}

function resolveRequestPath(urlPath) {
  const decoded = decodeURIComponent(urlPath.split("?")[0]);
  const relative = normalize(decoded).replace(/^([/\\])+/, "");
  const target = resolve(join(root, relative || "viewer/index.html"));
  if (target !== root && !target.startsWith(root + sep)) {
    return null;
  }
  return target;
}

const server = createServer((req, res) => {
  if (!req.url || req.method !== "GET") {
    send(res, 405, "Only GET is supported.");
    return;
  }

  const target = resolveRequestPath(req.url);
  if (!target || !existsSync(target)) {
    send(res, 404, "Not found.");
    return;
  }

  const stats = statSync(target);
  const file = stats.isDirectory() ? join(target, "index.html") : target;
  if (!existsSync(file) || !statSync(file).isFile()) {
    send(res, 404, "Not found.");
    return;
  }

  res.writeHead(200, {
    "Content-Type": contentTypes.get(extname(file).toLowerCase()) ?? "application/octet-stream",
    "Content-Length": statSync(file).size,
    "Cache-Control": "no-store",
  });
  createReadStream(file).pipe(res);
});

server.listen(port, host, () => {
  console.log(`Voxel viewer: http://${host}:${port}/viewer/index.html`);
});
