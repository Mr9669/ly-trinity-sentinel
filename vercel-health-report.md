# Vercel Health Probe

Time: 2026-06-19T05:08:14Z

## nano-perf-api.vercel.app
- `https://nano-perf-api.vercel.app/` -> HTTP 404
  Body: `The page could not be found

NOT_FOUND

sfo1::fwmzk-1781845694793-154f1f1f3de9`
- `https://nano-perf-api.vercel.app/health` -> HTTP 500
  Body: `A server error has occurred

FUNCTION_INVOCATION_FAILED

sfo1::q8sqj-1781845694893-25ded8e0e011`
- `https://nano-perf-api.vercel.app/api/` -> HTTP 500
  Body: `A server error has occurred

FUNCTION_INVOCATION_FAILED

sfo1::kj7hj-1781845695729-aa99fe5469fb`
- `https://nano-perf-api.vercel.app/api/health` -> HTTP 404
  Body: `The page could not be found

NOT_FOUND

sfo1::6qzp2-1781845696060-984e35456a1e`

## ly-distilled-node.vercel.app
- `https://ly-distilled-node.vercel.app/` -> HTTP 404
  Body: `The page could not be found

NOT_FOUND

sfo1::cctl4-1781845696148-edf5f29182d0`
- `https://ly-distilled-node.vercel.app/health` -> HTTP 200
  Body: `{"ok": true, "status": "healthy", "node_id": "vercel-distilled-01", "timestamp": "2026-06-19T05:08:16.856173+00:00", "hb_configured": true, "python": "3.12.13 (main, May 15 2026, 17:14:48) [G", "platform": "Linux-5.10.253-286.1015.amzn2.x86_64-x86_64-with-glibc2.34"}`
- `https://ly-distilled-node.vercel.app/api` -> HTTP 200
  Body: `{"ok": true, "status": "healthy", "node_id": "vercel-distilled-01", "timestamp": "2026-06-19T05:08:17.046060+00:00", "hb_configured": true, "python": "3.12.13 (main, May 15 2026, 17:14:48) [G", "platform": "Linux-5.10.253-286.1015.amzn2.x86_64-x86_64-with-glibc2.34"}`
- `https://ly-distilled-node.vercel.app/api/` -> HTTP 200
  Body: `{"ok": true, "status": "healthy", "node_id": "vercel-distilled-01", "timestamp": "2026-06-19T05:08:17.215869+00:00", "hb_configured": true, "python": "3.12.13 (main, May 15 2026, 17:14:48) [G", "platform": "Linux-5.10.253-286.1015.amzn2.x86_64-x86_64-with-glibc2.34"}`
- `https://ly-distilled-node.vercel.app/api/health` -> HTTP 200
  Body: `{"ok": true, "status": "healthy", "node_id": "vercel-distilled-01", "timestamp": "2026-06-19T05:08:17.388767+00:00", "hb_configured": true, "python": "3.12.13 (main, May 15 2026, 17:14:48) [G", "platform": "Linux-5.10.253-286.1015.amzn2.x86_64-x86_64-with-glibc2.34"}`
- `https://ly-distilled-node.vercel.app/api/heartbeat` -> HTTP 404
  Body: `The page could not be found

NOT_FOUND

sfo1::nc8kb-1781845697493-6fcdd40b4fb3`
