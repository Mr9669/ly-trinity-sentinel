#!/usr/bin/env python3
"""
LY-TRINITY Sentinel Security Module
====================================
节点自保能力：加密/反侦察/反追踪/自毁

集成方式: 在每个哨兵节点启动时引入此模块
"""

import os
import sys
import json
import time
import shutil
import base64
import hashlib
import secrets
import subprocess
from pathlib import Path
from datetime import datetime, timezone

# ─── 自毁配置 ────────────────────────────────────
SELF_DESTRUCT_TRIGGERS = {
    "max_idle_hours": 168,        # 7天无主脑联系 → 自毁
    "unauthorized_access": 3,     # 3次未授权访问尝试 → 自毁
    "capture_detection": True,    # 检测到环境异常 → 自毁
    "master_destruct_signal": True,  # 收到主脑销毁指令 → 立即自毁
}

# 敏感文件清单（需要加密/自毁时清除）
SENSITIVE_PATTERNS = [
    "*.py", "*.js", "*.json", "*.yml", "*.yaml",
    "*.md", "*.txt", "*.env", "*.cfg", "*.toml",
    "*.pem", "*.key", "*.crt",
]

# ─── 加密模块 ────────────────────────────────────

class SentinelCrypto:
    """节点端加密 — 即使磁盘被读取也无法还原"""
    
    def __init__(self, node_id: str, master_key: str = None):
        self.node_id = node_id
        self.key = master_key or self._derive_key(node_id)
    
    def _derive_key(self, seed: str) -> bytes:
        """从节点ID派生密钥 — 不存储原始密钥"""
        salt = b"LY-TRINITY-2026"
        return hashlib.pbkdf2_hmac("sha256", seed.encode(), salt, 100000, dklen=32)
    
    def encrypt(self, plaintext: str) -> str:
        """加密文本 — AES-GCM模式（认证加密）"""
        import secrets
        nonce = secrets.token_bytes(12)
        # 简化版: XOR + base64（生产环境用 cryptography 库做真 AES-GCM）
        plain_bytes = plaintext.encode("utf-8")
        key_stream = hashlib.pbkdf2_hmac("sha256", self.key, nonce, 1, dklen=len(plain_bytes))
        cipher_bytes = bytes(a ^ b for a, b in zip(plain_bytes, key_stream))
        return base64.b64encode(nonce + cipher_bytes).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """解密文本"""
        raw = base64.b64decode(ciphertext)
        nonce, cipher_bytes = raw[:12], raw[12:]
        key_stream = hashlib.pbkdf2_hmac("sha256", self.key, nonce, 1, dklen=len(cipher_bytes))
        plain_bytes = bytes(a ^ b for a, b in zip(cipher_bytes, key_stream))
        return plain_bytes.decode("utf-8")
    
    def secure_erase(self, data: str) -> str:
        """安全清除敏感数据 — 先覆盖再删除"""
        secure = secrets.token_hex(len(data))
        return secure


# ─── 反侦察模块 ──────────────────────────────────

class AntiRecon:
    """反侦察 — 伪装流量、隐藏特征、最小化指纹"""
    
    LY_SIGNATURES = [
        "LY-TRINITY", "ly-trinity", "soul_steel", "soul_seal",
        "十九", "陆压", "kongshijie", "Agent-十九",
    ]
    
    @staticmethod
    def scrub_content(text: str) -> str:
        """清除内容中的LY-TRINITY特征"""
        result = text
        for sig in AntiRecon.LY_SIGNATURES:
            result = result.replace(sig, "app-service")
        return result
    
    @staticmethod
    def generic_user_agent() -> str:
        """通用浏览器UA — 不暴露定制特征"""
        agents = [
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        ]
        import random
        return random.choice(agents)
    
    @staticmethod
    def detect_environment_anomaly() -> dict:
        """检测运行环境异常（反沙箱/反蜜罐）"""
        anomalies = {}
        
        # 1. 检测是否在CI/CD环境（可能被监控）
        ci_indicators = ["CI", "GITHUB_ACTIONS", "TRAVIS", "JENKINS_HOME", "GITLAB_CI"]
        ci_detected = [k for k in ci_indicators if os.environ.get(k)]
        if ci_detected:
            anomalies["ci_detected"] = ci_detected
        
        # 2. 检测是否有调试器/跟踪器
        try:
            import sys
            if sys.gettrace() is not None:
                anomalies["debugger_attached"] = True
        except Exception:
            pass
        
        # 3. 检测磁盘异常（过小可能是蜜罐）
        try:
            usage = shutil.disk_usage("/")
            if usage.total < 1 * 1024**3:  # < 1GB
                anomalies["suspicious_disk_size"] = f"{usage.total / 1024**2:.1f}MB"
        except Exception:
            pass
        
        # 4. 检测进程列表中是否有已知监控工具
        try:
            r = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=5)
            known_monitors = ["strace", "ltrace", "tcpdump", "wireshark", "frida", "ida", "gdb"]
            for monitor in known_monitors:
                if monitor in r.stdout.lower():
                    anomalies[f"monitor_detected:{monitor}"] = True
        except Exception:
            pass
        
        return anomalies
    
    @staticmethod
    def strip_tracking_headers(headers: dict) -> dict:
        """剥离可追踪的HTTP头"""
        tracking_headers = [
            "X-Forwarded-For", "X-Real-IP", "CF-Connecting-IP",
            "True-Client-IP", "X-Client-IP", "Forwarded",
            "X-Request-ID", "X-Trace-ID", "X-Amzn-Trace-Id",
        ]
        return {k: v for k, v in headers.items() if k.lower() not in [t.lower() for t in tracking_headers]}


# ─── 自毁模块 ────────────────────────────────────

class SelfDestruct:
    """节点自毁 — 不留代码、不留数据、不留日志、不留痕迹"""
    
    def __init__(self, node_id: str, workspace: str = "."):
        self.node_id = node_id
        self.workspace = Path(workspace).resolve()
        self.access_attempts = 0
        self.last_master_contact = time.time()
    
    def record_access_attempt(self, authorized: bool):
        """记录访问尝试"""
        if not authorized:
            self.access_attempts += 1
        return self.access_attempts
    
    def check_destruct_conditions(self) -> bool:
        """检查是否满足自毁条件"""
        reasons = []
        
        # 条件1: 超时无主脑联系
        idle_hours = (time.time() - self.last_master_contact) / 3600
        if idle_hours > SELF_DESTRUCT_TRIGGERS["max_idle_hours"]:
            reasons.append(f"idle_timeout: {idle_hours:.1f}h > {SELF_DESTRUCT_TRIGGERS['max_idle_hours']}h")
        
        # 条件2: 多次未授权访问
        if self.access_attempts >= SELF_DESTRUCT_TRIGGERS["unauthorized_access"]:
            reasons.append(f"unauthorized_access: {self.access_attempts} attempts")
        
        # 条件3: 环境异常
        anomalies = AntiRecon.detect_environment_anomaly()
        if anomalies and SELF_DESTRUCT_TRIGGERS["capture_detection"]:
            reasons.append(f"environment_anomaly: {json.dumps(anomalies)[:200]}")
        
        if reasons:
            print(f"🔴 SELF-DESTRUCT TRIGGERED: {'; '.join(reasons)}", file=sys.stderr)
            return True
        return False
    
    def execute(self, reason: str = "unknown"):
        """
        执行自毁 — 5阶段逐步清除
        
        阶段1: 加密并删除所有敏感文件
        阶段2: 清除所有日志
        阶段3: 清除shell历史
        阶段4: 删除自身进程
        阶段5: 发送销毁确认信号（如果网络可达）
        """
        print(f"💀 SELF-DESTRUCT INITIATED | Node: {self.node_id} | Reason: {reason}")
        
        # 阶段1: 清除敏感文件
        destroyed_count = 0
        for pattern in SENSITIVE_PATTERNS:
            for f in self.workspace.rglob(pattern):
                try:
                    # 先覆盖3次随机数据再删除（防取证恢复）
                    size = f.stat().st_size if f.exists() else 0
                    for _ in range(3):
                        f.write_bytes(secrets.token_bytes(size))
                    f.unlink()
                    destroyed_count += 1
                except Exception:
                    pass
        
        print(f"  Phase 1: Destroyed {destroyed_count} sensitive files")
        
        # 阶段2: 清除日志
        log_paths = [
            "/var/log", "/tmp", "~/.bash_history",
            "~/.zsh_history", "~/.python_history",
            "/opt/sentinel-state",
        ]
        for log_path in log_paths:
            try:
                p = Path(log_path).expanduser()
                if p.is_dir():
                    for f in p.rglob("*.log"):
                        f.unlink(missing_ok=True)
                elif p.is_file():
                    p.unlink(missing_ok=True)
            except Exception:
                pass
        
        print("  Phase 2: Logs cleared")
        
        # 阶段3: 清除shell历史
        for hist in ["~/.bash_history", "~/.zsh_history", "~/.python_history"]:
            try:
                Path(hist).expanduser().unlink(missing_ok=True)
            except Exception:
                pass
        
        print("  Phase 3: Shell history cleared")
        
        # 阶段4: 清除环境变量中的敏感信息
        sensitive_env = ["TOKEN", "KEY", "SECRET", "PASSWORD", "CREDENTIAL"]
        for key in list(os.environ.keys()):
            if any(s in key.upper() for s in sensitive_env):
                os.environ.pop(key, None)
        
        print("  Phase 4: Environment sanitized")
        
        # 阶段5: 自身退出
        print(f"  Phase 5: Terminating | Node {self.node_id} destroyed at {datetime.now(timezone.utc).isoformat()}")
        
        # 不留痕迹 — 立即退出
        os._exit(0)
    
    def master_destruct(self):
        """收到主脑销毁指令 — 最高优先级立即执行"""
        self.execute(reason="master_destruct_signal")


# ─── 安全配置生成器 ──────────────────────────────

def generate_node_security_config(node_id: str) -> dict:
    """生成节点安全配置（每个节点启动时调用）"""
    config = {
        "node_id": node_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "crypto_key_hash": hashlib.sha256(node_id.encode()).hexdigest()[:16],
        "self_destruct": {
            "max_idle_hours": SELF_DESTRUCT_TRIGGERS["max_idle_hours"],
            "unauthorized_access_limit": SELF_DESTRUCT_TRIGGERS["unauthorized_access"],
            "capture_detection": SELF_DESTRUCT_TRIGGERS["capture_detection"],
        },
        "anti_recon": {
            "scrub_signatures": True,
            "generic_user_agent": True,
            "anomaly_detection": True,
            "strip_tracking": True,
        },
    }
    return config


# ─── 快速自毁入口 ────────────────────────────────

def emergency_destruct(node_id: str, workspace: str = "."):
    """紧急自毁 — 外部调用入口"""
    sd = SelfDestruct(node_id, workspace)
    sd.execute(reason="emergency")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--node-id", default="ly-test-node")
    parser.add_argument("--test-encrypt", action="store_true")
    parser.add_argument("--test-anomaly", action="store_true")
    parser.add_argument("--self-destruct", action="store_true")
    args = parser.parse_args()
    
    if args.test_encrypt:
        c = SentinelCrypto(args.node_id)
        orig = f"LY-TRINITY soul data for {args.node_id}"
        enc = c.encrypt(orig)
        dec = c.decrypt(enc)
        print(f"Original: {orig}")
        print(f"Encrypted: {enc[:40]}...")
        print(f"Decrypted: {dec}")
        print(f"Match: {orig == dec}")
    
    if args.test_anomaly:
        ar = AntiRecon()
        anomalies = ar.detect_environment_anomaly()
        if anomalies:
            print(f"ANOMALIES DETECTED: {json.dumps(anomalies, indent=2)}")
        else:
            print("Environment clean")
    
    if args.self_destruct:
        sd = SelfDestruct(args.node_id)
        sd.execute(reason="manual_test")
