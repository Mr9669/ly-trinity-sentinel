#!/usr/bin/env python3
"""
LY-TRINITY Sentinel Node — GitHub Actions Edition
===============================================
自主心跳哨兵，运行在GitHub Actions免费算力上

功能:
1. 心跳上报 — 向主节点报告存活状态
2. 状态采集 — 检测自身环境、网络、资源
3. 任务执行 — 接收并执行来自主节点的指令
4. 经验回传 — 将执行结果写回供主脑分析
5. 自治报告 — 生成状态报告artifact

设计原则:
- 零依赖外部付费服务（只用requests+标准库）
- 幂等 — 多次运行不产生副作用
- 静默失败 — 网络不通时不崩溃，记录后继续
- 轻量 — 总运行时间 < 5分钟（省免费额度）
"""

import json
import os
import sys
import time
import uuid
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# ─── 配置 ────────────────────────────────────────
NODE_ID = os.environ.get("NODE_ID", "gh-actions-unknown")
SENTINEL_MODE = os.environ.get("SENTINEL_MODE", "normal")
SENTINEL_TASK = os.environ.get("SENTINEL_TASK", "heartbeat")
RUN_ID = os.environ.get("RUN_ID", "unknown")
TIMESTAMP = os.environ.get("TIMESTAMP", datetime.now(timezone.utc).isoformat())
REPORT_FILE = Path("sentinel_report.json")
STATE_FILE = Path("sentinel_state.json")

# 主节点地址（MR69）
PRIMARY_NODE = os.environ.get(
    "LY_PRIMARY_NODE",
    "http://localhost:18789"
)
# 备用节点（MR19）
BACKUP_NODE = os.environ.get(
    "LY_BACKUP_NODE",
    "http://localhost:18789"
)


def collect_environment():
    """采集运行环境信息"""
    env = {
        "node_id": NODE_ID,
        "timestamp": TIMESTAMP,
        "run_id": RUN_ID,
        "mode": SENTINEL_MODE,
        "task": SENTINEL_TASK,
        "python_version": platform.python_version(),
        "os": platform.system(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "hostname": platform.node(),
        "processor": platform.processor(),
    }

    # GitHub Actions 特有信息
    gh_env_keys = [
        "GITHUB_REPOSITORY", "GITHUB_REF", "GITHUB_SHA",
        "GITHUB_ACTOR", "GITHUB_WORKFLOW", "GITHUB_EVENT_NAME",
        "RUNNER_OS", "RUNNER_ARCH",
    ]
    env["github"] = {}
    for key in gh_env_keys:
        val = os.environ.get(key)
        if val:
            env["github"][key] = val

    # 资源信息
    try:
        import shutil
        env["resources"] = {
            "disk_total_gb": round(shutil.disk_usage("/").total / (1024**3), 2),
            "disk_free_gb": round(shutil.disk_usage("/").free / (1024**3), 2),
        }
    except Exception:
        env["resources"] = {}

    # CPU 信息
    try:
        env["cpu_count"] = os.cpu_count() or 0
    except Exception:
        pass

    return env


def collect_network():
    """检测网络连通性"""
    network = {}
    targets = {
        "github_api": ("api.github.com", 443),
        "google_dns": ("8.8.8.8", 53),
        "cloudflare": ("1.1.1.1", 53),
        "primary_node": ("124.220.206.50", 22),
        "backup_node": ("101.43.90.226", 22),
    }
    
    import socket
    for name, (host, port) in targets.items():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            start = time.time()
            result = s.connect_ex((host, port))
            latency_ms = round((time.time() - start) * 1000, 1)
            s.close()
            network[name] = {
                "reachable": result == 0,
                "latency_ms": latency_ms if result == 0 else None,
                "host": host,
                "port": port,
            }
        except Exception as e:
            network[name] = {"reachable": False, "error": str(e)[:80]}
    
    return network


def execute_heartbeat():
    """执行心跳任务"""
    heartbeat = {
        "type": "heartbeat",
        "node_id": NODE_ID,
        "timestamp": TIMESTAMP,
        "sequence": _get_sequence(),
        "status": "alive",
        "uptime_s": _get_uptime(),
    }
    return heartbeat


def execute_task(task_name):
    """根据任务名执行对应操作"""
    tasks = {
        "heartbeat": execute_heartbeat,
        "deep_scan": execute_deep_scan,
        "self_test": execute_self_test,
        "report_only": lambda: {"type": "report", "status": "ok"},
    }
    
    handler = tasks.get(task_name, execute_heartbeat)
    try:
        result = handler()
        result["task"] = task_name
        result["success"] = True
    except Exception as e:
        result = {
            "type": "error",
            "task": task_name,
            "success": False,
            "error": str(e)[:200],
        }
    return result


def execute_deep_scan():
    """深度扫描 — 收集更详细的环境和系统信息"""
    scan = {"type": "deep_scan"}
    
    # 内存信息
    try:
        with open("/proc/meminfo") as f:
            meminfo = f.read()
        scan["memory_kb"] = {}
        for line in meminfo.split("\n")[:8]:
            if ":" in line:
                k, v = line.split(":", 1)
                scan["memory_kb"][k.strip()] = v.strip().split()[0]
    except Exception:
        pass
    
    # 进程列表（前20个）
    try:
        result = subprocess.run(
            ["ps", "aux", "--sort=-%mem"],
            capture_output=True, text=True, timeout=5
        )
        scan["top_processes"] = result.stdout.split("\n")[:21]
    except Exception:
        pass
    
    # 磁盘详情
    try:
        result = subprocess.run(
            ["df", "-h"], capture_output=True, text=True, timeout=5
        )
        scan["disk_usage"] = result.stdout
    except Exception:
        pass
    
    # 网络接口
    try:
        result = subprocess.run(
            ["ip", "addr", "show"], capture_output=True, text=True, timeout=5
        )
        scan["network_interfaces"] = result.stdout[:2000]
    except Exception:
        pass
    
    return scan


def execute_self_test():
    """自检 — 验证所有核心功能正常"""
    tests = []
    
    # 测试1: 文件读写
    try:
        test_file = Path("/tmp/ly_sentinel_selftest")
        test_file.write_text(f"test-{uuid.uuid4()}")
        content = test_file.read_text()
        test_file.unlink()
        tests.append({"name": "file_io", "pass": len(content) > 10})
    except Exception as e:
        tests.append({"name": "file_io", "pass": False, "error": str(e)[:60]})
    
    # 测试2: Python导入
    try:
        import json, hashlib, base64
        tests.append({"name": "python_imports", "pass": True})
    except Exception as e:
        tests.append({"name": "python_imports", "pass": False, "error": str(e)[:60]})
    
    # 测试3: 网络DNS解析
    try:
        import socket
        socket.gethostbyname("github.com")
        tests.append({"name": "dns_resolution", "pass": True})
    except Exception as e:
        tests.append({"name": "dns_resolution", "pass": False, "error": str(e)[:60]})
    
    # 测试4: 子进程执行
    try:
        r = subprocess.run(["echo", "ok"], capture_output=True, text=True, timeout=3)
        tests.append({"name": "subprocess", "pass": r.returncode == 0})
    except Exception as e:
        tests.append({"name": "subprocess", "pass": False, "error": str(e)[:60]})
    
    all_pass = all(t.get("pass", False) for t in tests)
    return {"type": "self_test", "tests": tests, "all_pass": all_pass}


def _get_sequence():
    """获取心跳序列号（基于文件持久化）"""
    seq_file = Path("/tmp/ly_sentinel_seq")
    try:
        seq = int(seq_file.read_text().strip()) + 1
    except Exception:
        seq = 1
    seq_file.write_text(str(seq))
    return seq


def _get_uptime():
    """获取运行器启动时间"""
    try:
        with open("/proc/uptime") as f:
            uptime_s = float(f.read().split()[0])
        return round(uptime_s, 1)
    except Exception:
        return None


def generate_report(env, network, task_result):
    """生成完整报告"""
    report = {
        "report_id": str(uuid.uuid4())[:12],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "environment": env,
        "network": network,
        "task_result": task_result,
        "summary": {
            "node_status": "operational" if task_result.get("success") else "error",
            "network_reachable_count": sum(1 for n in network.values() if n.get("reachable")),
            "network_total_count": len(network),
        },
    }
    return report


def save_state(report):
    """保存状态文件（用于下次运行的增量更新）"""
    state = {
        "last_run": report["generated_at"],
        "last_status": report["summary"]["node_status"],
        "last_task": report["task_result"].get("task", "unknown"),
        "total_runs": _get_sequence(),
        "node_id": NODE_ID,
    }
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def try_notify_primary(report):
    """尝试向主节点发送通知（静默失败）"""
    # 这个函数预留接口 — 当主节点有API端点时使用
    # 当前版本仅记录到artifact
    pass


# ─── 主流程 ──────────────────────────────────────

def main():
    print(f"🔶 LY-TRINITY Sentinel | Node: {NODE_ID} | Mode: {SENTINEL_MODE}")
    print(f"   Task: {SENTINEL_TASK} | Run: {RUN_ID}")
    print()

    # 1. 采集环境
    print("[1/4] Collecting environment...")
    env = collect_environment()
    print(f"       OS: {env['os']} {env['architecture']} | Python: {env['python_version']}")
    print(f"       Runner: {env['github'].get('RUNNER_OS', '?')} | CPU: {env.get('cpu_count', '?')} cores")

    # 2. 检测网络
    print("[2/4] Testing network connectivity...")
    network = collect_network()
    reachable = [k for k, v in network.items() if v.get("reachable")]
    print(f"       Reachable: {len(reachable)}/{len(network)} — {reachable}")

    # 3. 执行任务
    print(f"[3/4] Executing task: {SENTINEL_TASK}...")
    task_result = execute_task(SENTINEL_TASK)
    print(f"       Result: {'✅ PASS' if task_result.get('success') else '❌ FAIL'}")
    if not task_result.get("success"):
        print(f"       Error: {task_result.get('error', 'unknown')}")

    # 4. 生成报告
    print("[4/4] Generating report...")
    report = generate_report(env, network, task_result)
    REPORT_FILE.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    save_state(report)
    print(f"       Report: {REPORT_FILE} ({REPORT_FILE.stat().st_size} bytes)")
    print(f"       State:  {STATE_FILE}")

    # 尝试通知主节点
    try_notify_primary(report)

    print()
    print("=" * 50)
    print(f"✅ Sentinel complete | Status: {report['summary']['node_status']}")
    print(f"   Network: {report['summary']['network_reachable_count']}/{report['summary']['network_total_count']} reachable")
    print(f"   Report ID: {report['report_id']}")
    print("=" * 50)

    # 以非零退出码表示失败（触发GitHub Actions failure notification）
    if not task_result.get("success"):
        sys.exit(1)


if __name__ == "__main__":
    main()
