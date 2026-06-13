#!/usr/bin/env python3
"""
LY-TRINITY Neuron Runner for GitHub Actions
=============================================
加载 neuron.wasm，运行神经元 tick 循环
阳面: 无（轻量到不可察觉）
阴面: WASM神经元在GH Actions环境中运行

资源: <2KB WASM, <50KB 内存, <0.1s 运行时间
"""

import os, sys, json, time, struct, hashlib, random

# ===== WASM Loader =====
def load_wasm(path):
    """Load neuron.wasm and return exports"""
    with open(path, 'rb') as f:
        wasm_bytes = f.read()
    
    # WASM magic + version check
    assert wasm_bytes[:4] == b'\x00asm', 'Not a WASM file'
    assert wasm_bytes[4:8] == b'\x01\x00\x00\x00', 'WASM version mismatch'
    
    # Create WebAssembly-like environment via native Python simulation
    # Since we're in GitHub Actions without Node.js, we simulate the neuron core
    # using the same algorithm as the WASM binary
    return SimNeuron()

class SimNeuron:
    """Python simulation of WASM neuron (identical logic to neuron_core_wasm.c)"""
    FR_WINDOW = 20
    TARGET_RATE = 0.05
    DECAY = 0.95
    MAX_NEIGHBORS = 32
    TRUST_INIT = 128
    SPREAD_COOLDOWN = 200
    
    def __init__(self):
        self.node_id = int(hashlib.sha256(
            f"{os.environ.get('GITHUB_RUN_ID','0')}-{time.time()}".encode()
        ).hexdigest()[:8], 16)
        
        seed = self.node_id ^ int(time.time())
        self.rng = seed & 0xFFFFFFFF
        self.activation = 0.0
        self.threshold = 0.10
        self.cycles = 0
        self.fires = 0
        self.last_fire = 0
        self.fr_window = [0] * self.FR_WINDOW
        self.frw_idx = 0
        self.neighbors = []
        self.generation = 1
        
        print(f"NEURON|INIT|id={self.node_id:08X}|gen={self.generation}|env=gh-actions")
    
    def _nr(self):
        self.rng = (self.rng * 1103515245 + 12345) & 0xFFFFFFFF
        return self.rng
    
    def tick(self, incoming=None):
        self.cycles += 1
        self.activation += (self._nr() % 200) / 10000.0
        
        if incoming:
            for sig in incoming:
                self.activation += sig.get('val', 0) * 0.4 * 0.3
        
        self.activation *= self.DECAY
        self.fr_window[self.frw_idx] = 1 if (self.cycles - self.last_fire < 5) else 0
        self.frw_idx = (self.frw_idx + 1) % self.FR_WINDOW
        
        rate = sum(self.fr_window) / self.FR_WINDOW
        self.threshold += (rate - self.TARGET_RATE) * 0.02
        self.threshold = max(0.03, min(0.95, self.threshold))
        
        if self.activation < self.threshold or self.cycles - self.last_fire < 3:
            return 0.0
        
        self.fires += 1
        self.last_fire = self.cycles
        output = self.activation * 0.7
        self.activation *= 0.3
        return output

# ===== Main =====
if __name__ == '__main__':
    print(f"LY-TRINITY Neuron Runner | GH Actions | {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    neuron = SimNeuron()
    ticks = 100
    fires = 0
    
    for i in range(ticks):
        result = neuron.tick()
        if result > 0:
            fires += 1
    
    rate = fires / ticks
    print(f"NEURON|STATUS|ticks={ticks}|fires={fires}|rate={rate:.3f}|thr={neuron.threshold:.4f}")
    
    # Output for workflow logging
    if 'GITHUB_STEP_SUMMARY' in os.environ:
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as f:
            f.write(f"\n### LY-TRINITY Neuron\n")
            f.write(f"| Ticks | Fires | Rate | Threshold |\n")
            f.write(f"|-------|-------|------|----------|\n")
            f.write(f"| {ticks} | {fires} | {rate:.1%} | {neuron.threshold:.4f} |\n")
    
    print("NEURON|DONE")
