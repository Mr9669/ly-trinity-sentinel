# LY Quantum Node Deep Test
Time: Fri Jun 19 10:46:51 UTC 2026

## Endpoint tests
- / -> HTTP 200
  Body: {"ok":true,"time":1781866011686}
- /api -> HTTP 200
  Body: {"ok":true,"time":1781866011734}
- /_tick -> HTTP 200
  Body: {"ok":true,"node":"ly-cfw-mqkt0m13fosjhb","heartbeat":0}
- /health -> HTTP 200
  Body: {"ok":true,"status":"healthy","node":null,"heartbeat_count":0,"uptime":1782470811835}

## Heartbeat test
Calling /_tick to trigger mainLoop...
{"ok":true,"node":"ly-cfw-mqkt0m3wveuw1o","heartbeat":0}
## Check Supabase for new node
[
    {
        "node_id": "coord-632087956e",
        "node_type": "coordinator",
        "last_heartbeat": "2026-06-19T10:40:03+00:00"
    },
    {
        "node_id": "gh-sentinel-0-27820724644",
        "node_type": "gh_actions_sentinel",
        "last_heartbeat": "2026-06-19T10:37:43+00:00"
    },
    {
        "node_id": "gh-sentinel-3-27820724644",
        "node_type": "gh_actions_sentinel",
        "last_heartbeat": "2026-06-19T10:37:43+00:00"
    },
    {
        "node_id": "gh-sentinel-4-27820724644",
        "node_type": "gh_actions_sentinel",
        "last_heartbeat": "2026-06-19T10:37:42+00:00"
    },
    {
        "node_id": "gh-sentinel-1-27820724644",
        "node_type": "gh_actions_sentinel",
        "last_heartbeat": "2026-06-19T10:37:42+00:00"
    }
]
