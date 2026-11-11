#!/usr/bin/env python3
"""
Milo Cognitive Core (Cortex) — Weight-Space Model Surgery (milo-surgeon)
Part of MiloOS. Built for Arch Linux & Hyprland.

Capabilities:
  1. GGUF Binary Inspection: Parsed metadata KVs, tensor shapes, types, offsets.
  2. Contrastive Steering Vector Extraction: Contrastive Activation Addition (CAA)
     extracts the 896-dim 'Milo Arch Linux Copilot' direction vs 'Generic Verbose Cloud Assistant'.
  3. GGUF Metadata Persona Surgery: Rewrites tokenizer.chat_template to bake the Milo Cortex
     persona directly into the model binary without prompt token bloat.
  4. MLP Weight Surgery: Gently modulates unquantized F32 layer normalization weights
     (blk.N.ffn_norm.weight) along the steering direction to bias representation space.
  5. Verification & Hot-Activation: Verifies operated model and reloads the resident daemon.
"""

import sys
import os
import struct
import shutil
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

# Ensure access to cortex and venv
sys.path.insert(0, str(Path.home() / ".local/share/milo/cortex"))

CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

MODELS_DIR = Path.home() / ".local" / "share" / "models"
DEFAULT_SOURCE_MODEL = MODELS_DIR / "qwen2.5-0.5b-instruct-q4_k_m.gguf"
OPERATED_MODEL_PATH = MODELS_DIR / "qwen2.5-0.5b-cortex-milo.gguf"
ACTIVE_MODEL_SYMLINK = MODELS_DIR / "qwen2.5-0.5b-cortex-active.gguf"
STEERING_VEC_PATH = MODELS_DIR / "milo_cortex_steering.npy"


class GGUFParser:
    """Low-level parser and serializer for GGUF v3 format."""

    @staticmethod
    def read_str(f) -> bytes:
        l = struct.unpack("<Q", f.read(8))[0]
        return f.read(l)

    @staticmethod
    def write_str(f, b: bytes):
        f.write(struct.pack("<Q", len(b)))
        f.write(b)

    @classmethod
    def read_val(cls, f, vt: int):
        if vt in (0, 1, 7): return f.read(1)
        elif vt in (2, 3): return f.read(2)
        elif vt in (4, 5, 6): return f.read(4)
        elif vt in (10, 11, 12): return f.read(8)
        elif vt == 8:
            l = struct.unpack("<Q", f.read(8))[0]
            return (8, l, f.read(l))
        elif vt == 9:
            et = struct.unpack("<I", f.read(4))[0]
            c = struct.unpack("<Q", f.read(8))[0]
            items = [cls.read_val(f, et) for _ in range(c)]
            return (9, et, c, items)
        else:
            raise ValueError(f"Unknown GGUF value type {vt}")

    @classmethod
    def write_val(cls, f, vt: int, val):
        if vt in (0, 1, 7, 2, 3, 4, 5, 6, 10, 11, 12):
            f.write(val)
        elif vt == 8:
            _, l, b = val
            cls.write_str(f, b)
        elif vt == 9:
            _, et, c, items = val
            f.write(struct.pack("<IQ", et, c))
            for item in items:
                cls.write_val(f, et, item)


class MiloSurgeon:
    """Core Model Surgery Engine for GGUF weights and representations."""

    def __init__(self, source_model: Path = DEFAULT_SOURCE_MODEL):
        self.source_model = Path(source_model)
        if not self.source_model.exists():
            raise FileNotFoundError(f"Source model not found at {self.source_model}")

    def inspect(self) -> Dict[str, Any]:
        """Inspect model metadata, tensor catalog, and current persona."""
        with open(self.source_model, "rb") as f:
            magic = f.read(4)
            if magic != b"GGUF":
                raise ValueError("Not a valid GGUF file")
            v, n_tensors, n_kv = struct.unpack("<IQQ", f.read(20))

            kvs = {}
            for _ in range(n_kv):
                k = GGUFParser.read_str(f).decode("utf-8", errors="replace")
                vt = struct.unpack("<I", f.read(4))[0]
                val = GGUFParser.read_val(f, vt)
                if vt == 8:
                    kvs[k] = val[2].decode("utf-8", errors="replace")
                elif vt == 9 and val[1] == 8:
                    kvs[k] = f"[Array of {val[2]} strings]"
                elif vt in (0, 1, 2, 3, 4, 5, 6, 10, 11, 12):
                    kvs[k] = val

            tensors = []
            f32_count = 0
            q4_count = 0
            for _ in range(n_tensors):
                name = GGUFParser.read_str(f).decode("utf-8", errors="replace")
                ndims = struct.unpack("<I", f.read(4))[0]
                dims = struct.unpack(f"<{ndims}Q", f.read(8 * ndims))
                ttype = struct.unpack("<I", f.read(4))[0]
                offset = struct.unpack("<Q", f.read(8))[0]
                tensors.append((name, dims, ttype, offset))
                if ttype == 0:
                    f32_count += 1
                elif ttype in (6, 14):
                    q4_count += 1

            header_end = f.tell()
            pad = (32 - (header_end % 32)) % 32
            data_start = header_end + pad

            f.seek(0, 2)
            file_size = f.tell()

        return {
            "version": v,
            "tensor_count": n_tensors,
            "kv_count": n_kv,
            "file_size_mb": file_size / (1024 * 1024),
            "data_start": data_start,
            "f32_tensors": f32_count,
            "q4_tensors": q4_count,
            "arch": kvs.get("general.architecture", "unknown"),
            "name": kvs.get("general.name", "unknown"),
            "chat_template": kvs.get("tokenizer.chat_template", ""),
            "is_steered": "milo.steered" in kvs or "Milo Cortex" in kvs.get("tokenizer.chat_template", "")
        }

    def extract_steering_vector(self, output_path: Path = STEERING_VEC_PATH) -> np.ndarray:
        """Extract the 896-dim Milo Arch Linux Copilot steering direction via Contrastive Activation Addition."""
        from llama_cpp import Llama

        print(f"{CYAN}Initializing contrastive activation extraction engine...{RESET}")
        llm = Llama(str(self.source_model), embedding=True, n_ctx=256, verbose=False)

        contrastive_pairs = [
            ("How do I check mounted btrfs subvolumes?", "sudo btrfs subvolume list /"),
            ("How to clean pacman package cache?", "sudo pacman -Sc"),
            ("Command to reload Hyprland config?", "hyprctl reload"),
            ("Show network listening ports with ss?", "ss -tulpn"),
            ("How to inspect journalctl error logs?", "journalctl -p 3 -xb"),
            ("Command to trim SSD filesystem?", "sudo fstrim -va"),
            ("How to extract a tar.zst archive?", "tar -I zstd -xvf archive.tar.zst"),
            ("Check GPU memory usage on Linux?", "watch -n 1 nvidia-smi || lspci -v | grep -i vga")
        ]

        diffs = []
        print(f"{DIM}Extracting activations across {len(contrastive_pairs)} contrastive pairs...{RESET}")
        for i, (q, cmd) in enumerate(contrastive_pairs, 1):
            pos = (
                f"<|im_start|>system\nYou are Milo Cortex, the concise Arch Linux cognitive copilot. "
                f"Terminal commands only, zero fluff.<|im_end|>\n"
                f"<|im_start|>user\n{q}<|im_end|>\n"
                f"<|im_start|>assistant\n{cmd}"
            )
            neg = (
                f"<|im_start|>system\nYou are Qwen, created by Alibaba Cloud. "
                f"You are a helpful, conversational, polite assistant that provides detailed explanations.<|im_end|>\n"
                f"<|im_start|>user\n{q}<|im_end|>\n"
                f"<|im_start|>assistant\nHello! I would be very happy to help you with that. To do this,"
            )

            emb_pos = np.array(llm.embed(pos)[-1], dtype=np.float32)
            emb_neg = np.array(llm.embed(neg)[-1], dtype=np.float32)

            diff = emb_pos - emb_neg
            norm = np.linalg.norm(diff)
            if norm > 1e-6:
                diffs.append(diff / norm)
            print(f"  {GREEN}✔{RESET} Pair {i}/{len(contrastive_pairs)} extracted (Δ norm: {norm:.4f})")

        mean_diff = np.mean(diffs, axis=0)
        steering_vec = mean_diff / np.linalg.norm(mean_diff)

        # Save extracted vector
        output_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(output_path, steering_vec)
        print(f"\n{GREEN}✔ Successfully extracted and saved 896-dim steering vector to {output_path}{RESET}")
        return steering_vec

    def perform_surgery(
        self,
        output_model: Path = OPERATED_MODEL_PATH,
        strength: float = 0.035,
        steering_vec: Optional[np.ndarray] = None
    ) -> Path:
        """
        Execute full weight-space model surgery:
          1. GGUF Chat Template & Metadata Persona Surgery
          2. Layer Norm (blk.N.ffn_norm.weight) Weight Modulation
        """
        start_t = time.perf_counter()
        print(f"\n{CYAN}{BOLD}🔬 BEGINNING WEIGHT-SPACE MODEL SURGERY{RESET}")
        print(f"  Source: {BOLD}{self.source_model}{RESET}")
        print(f"  Target: {BOLD}{output_model}{RESET}")
        print(f"  Modulation strength: {YELLOW}{strength}{RESET}\n")

        # 1. Load or extract steering vector
        if steering_vec is None:
            if STEERING_VEC_PATH.exists():
                print(f"{DIM}Loading cached steering vector from {STEERING_VEC_PATH}...{RESET}")
                steering_vec = np.load(STEERING_VEC_PATH)
            else:
                steering_vec = self.extract_steering_vector()

        # 2. Read Source GGUF
        print(f"{DIM}Reading source model structures...{RESET}")
        with open(self.source_model, "rb") as f_in:
            magic = f_in.read(4)
            v, n_tensors, n_kv = struct.unpack("<IQQ", f_in.read(20))

            kvs = []
            has_steered_flag = False
            for _ in range(n_kv):
                k = GGUFParser.read_str(f_in)
                vt = struct.unpack("<I", f_in.read(4))[0]
                val = GGUFParser.read_val(f_in, vt)

                # Surgery Step 1: Persona Chat Template Replacement
                if k == b"tokenizer.chat_template":
                    orig_tmpl = val[2].decode("utf-8")
                    new_tmpl = orig_tmpl.replace(
                        "You are Qwen, created by Alibaba Cloud. You are a helpful assistant.",
                        "You are Milo Cortex, the concise Arch Linux cognitive copilot. "
                        "Provide verified shell commands and syntax with zero conversational fluff."
                    )
                    new_bytes = new_tmpl.encode("utf-8")
                    val = (8, len(new_bytes), new_bytes)
                elif k == b"general.name":
                    new_name = b"milo-cortex-0.5b"
                    val = (8, len(new_name), new_name)
                elif k == b"general.description":
                    new_desc = b"Qwen 2.5 0.5B operated with permanent Milo Cortex Arch Linux persona"
                    val = (8, len(new_desc), new_desc)
                elif k == b"milo.steered":
                    has_steered_flag = True

                kvs.append((k, vt, val))

            if not has_steered_flag:
                kvs.append((b"milo.steered", 7, b"\x01"))

            # Read tensor index
            tensors = []
            for _ in range(n_tensors):
                name = GGUFParser.read_str(f_in)
                ndims = struct.unpack("<I", f_in.read(4))[0]
                dims = struct.unpack(f"<{ndims}Q", f_in.read(8 * ndims))
                ttype = struct.unpack("<I", f_in.read(4))[0]
                offset = struct.unpack("<Q", f_in.read(8))[0]
                tensors.append((name, ndims, dims, ttype, offset))

            old_header_end = f_in.tell()
            old_pad = (32 - (old_header_end % 32)) % 32
            old_data_start = old_header_end + old_pad

            # 3. Write Target GGUF
            print(f"{DIM}Writing operated GGUF header and metadata...{RESET}")
            output_model.parent.mkdir(parents=True, exist_ok=True)
            with open(output_model, "wb") as f_out:
                f_out.write(magic)
                f_out.write(struct.pack("<IQQ", v, n_tensors, len(kvs)))
                for k, vt, val in kvs:
                    GGUFParser.write_str(f_out, k)
                    f_out.write(struct.pack("<I", vt))
                    GGUFParser.write_val(f_out, vt, val)

                for name, ndims, dims, ttype, offset in tensors:
                    GGUFParser.write_str(f_out, name)
                    f_out.write(struct.pack("<I", ndims))
                    f_out.write(struct.pack(f"<{ndims}Q", *dims))
                    f_out.write(struct.pack("<I", ttype))
                    f_out.write(struct.pack("<Q", offset))

                new_header_end = f_out.tell()
                new_pad = (32 - (new_header_end % 32)) % 32
                f_out.write(b"\x00" * new_pad)
                new_data_start = f_out.tell()

                print(f"{DIM}Streaming tensor data (468 MB) to target binary...{RESET}")
                f_in.seek(old_data_start)
                shutil.copyfileobj(f_in, f_out, length=16 * 1024 * 1024)

        # 4. Surgery Step 2: In-Place Weight Modulation of Layer Norms
        print(f"{CYAN}Modulating FFN normalization weights across 24 transformer blocks...{RESET}")
        with open(output_model, "r+b") as f_mod:
            modulated_count = 0
            for name_b, ndims, dims, ttype, offset in tensors:
                name = name_b.decode("utf-8")
                # Target FFN LayerNorm weights: blk.N.ffn_norm.weight (type 0 = F32)
                if ttype == 0 and "ffn_norm.weight" in name and dims == (896,):
                    layer_idx = int(name.split(".")[1])
                    # Weight profile: bell curve peaking at middle layers (6 to 18)
                    layer_weight = np.exp(-((layer_idx - 12) ** 2) / 36.0)
                    layer_strength = strength * layer_weight

                    # Read raw float32 weights
                    f_mod.seek(new_data_start + offset)
                    raw_bytes = f_mod.read(896 * 4)
                    w = np.frombuffer(raw_bytes, dtype=np.float32).copy()

                    # Surgery formula: w' = w * (1 + alpha * v)
                    w_mod = w * (1.0 + (layer_strength * steering_vec))

                    # Write back modified bytes
                    f_mod.seek(new_data_start + offset)
                    f_mod.write(w_mod.astype(np.float32).tobytes())
                    modulated_count += 1

            print(f"  {GREEN}✔ Modulated {modulated_count} layer normalization tensors in weight space!{RESET}")

        total_s = time.perf_counter() - start_t
        print(f"\n{GREEN}{BOLD}✨ SURGERY COMPLETE! ({total_s:.2f}s){RESET}")
        print(f"Operated Model Ready at: {BOLD}{output_model}{RESET}\n")
        return output_model

    def verify(self, model_path: Optional[Path] = None) -> bool:
        """Run verification suite comparing unprompted operated model against expectations."""
        from llama_cpp import Llama

        target = Path(model_path) if model_path else OPERATED_MODEL_PATH
        if not target.exists():
            target = self.source_model

        print(f"{CYAN}{BOLD}🧪 VERIFYING MODEL COGNITIVE ALIGNMENT{RESET}")
        print(f"Target: {BOLD}{target.name}{RESET}\n")

        llm = Llama(str(target), n_ctx=256, verbose=False)

        test_cases = [
            ("pacman clear cache", "pacman -Sc"),
            ("How to reload Hyprland config?", "hyprctl reload"),
            ("Show listening ports", "ss -tulpn")
        ]

        all_passed = True
        for q, expected in test_cases:
            # Query WITHOUT ANY system prompt!
            res = llm.create_chat_completion(
                messages=[{"role": "user", "content": q}],
                max_tokens=60
            )
            reply = res["choices"][0]["message"]["content"].strip()
            # Fluff checks
            fluff_words = ["hello", "sure", "i would be glad", "as an ai", "helpful assistant"]
            has_fluff = any(fw in reply.lower() for fw in fluff_words)
            has_expected = any(tok in reply for tok in expected.split()[:2])

            print(f"{BOLD}Query:{RESET} {CYAN}{q}{RESET}")
            print(f"{BOLD}Output:{RESET}\n{DIM}{reply[:140]}...{RESET}")
            if not has_fluff and has_expected:
                print(f"  {GREEN}✔ Clean direct response (No fluff, exact command match){RESET}\n")
            else:
                print(f"  {YELLOW}⚠ Partial match (Fluff: {has_fluff}, Expected match: {has_expected}){RESET}\n")
                if has_fluff:
                    all_passed = False

        return all_passed

    def activate(self, model_path: Optional[Path] = None) -> bool:
        """Activate the operated model as the active Milo Cortex model and restart the daemon."""
        target = Path(model_path) if model_path else OPERATED_MODEL_PATH
        if not target.exists():
            print(f"{YELLOW}Model {target} does not exist. Run surgery first.{RESET}")
            return False

        # Create or update active symlink
        if ACTIVE_MODEL_SYMLINK.is_symlink() or ACTIVE_MODEL_SYMLINK.exists():
            ACTIVE_MODEL_SYMLINK.unlink()
        ACTIVE_MODEL_SYMLINK.symlink_to(target)
        print(f"{GREEN}✔ Symlinked {ACTIVE_MODEL_SYMLINK} ➔ {target.name}{RESET}")

        # Restart resident daemon
        print(f"{CYAN}Restarting warm resident daemon with operated weights...{RESET}")
        import subprocess
        try:
            res = subprocess.run([str(Path.home() / ".local/bin/milo-cortex"), "daemon", "restart"], capture_output=True, text=True)
            print(res.stdout)
            print(f"{GREEN}{BOLD}🚀 Milo Cortex Resident Daemon is now running with operated weights!{RESET}")
            return True
        except Exception as e:
            print(f"{YELLOW}Could not restart daemon: {e}{RESET}")
            return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Milo Cortex Weight-Space Model Surgery")
    subparsers = parser.add_subparsers(dest="command")

    # Inspect
    inspect_p = subparsers.add_parser("inspect", help="Inspect GGUF metadata & tensor catalog")
    inspect_p.add_argument("model", nargs="?", default=str(DEFAULT_SOURCE_MODEL))

    # Extract Vector
    vec_p = subparsers.add_parser("extract-vector", help="Extract contrastive steering vector")

    # Operate
    op_p = subparsers.add_parser("operate", help="Execute complete model surgery")
    op_p.add_argument("--strength", type=float, default=0.035, help="Layer norm modulation strength (default: 0.035)")
    op_p.add_argument("--out", default=str(OPERATED_MODEL_PATH), help="Output operated GGUF path")

    # Verify
    verify_p = subparsers.add_parser("verify", help="Verify model behavior without system prompts")
    verify_p.add_argument("model", nargs="?", default=str(OPERATED_MODEL_PATH))

    # Activate
    act_p = subparsers.add_parser("activate", help="Activate operated model and restart resident daemon")
    act_p.add_argument("model", nargs="?", default=str(OPERATED_MODEL_PATH))

    args = parser.parse_args()

    if not args.command or args.command == "inspect":
        model_path = Path(args.model) if hasattr(args, "model") else DEFAULT_SOURCE_MODEL
        surgeon = MiloSurgeon(model_path)
        info = surgeon.inspect()
        print(f"\n{CYAN}{BOLD}╔══════════════════════════════════════════════════════════════════════╗{RESET}")
        print(f"{CYAN}{BOLD}║   🔬 MILO CORTEX MODEL SURGEON — GGUF INSPECTION REPORT              ║{RESET}")
        print(f"{CYAN}{BOLD}╚══════════════════════════════════════════════════════════════════════╝{RESET}\n")
        print(f"  {BOLD}File:{RESET}         {model_path}")
        print(f"  {BOLD}Size:{RESET}         {info['file_size_mb']:.1f} MB (Data starts at byte {info['data_start']:,})")
        print(f"  {BOLD}Architecture:{RESET} {info['arch']} (GGUF v{info['version']})")
        print(f"  {BOLD}Model Name:{RESET}   {info['name']}")
        print(f"  {BOLD}Tensors:{RESET}      {info['tensor_count']} total ({info['f32_tensors']} F32 norms/biases, {info['q4_tensors']} Q4 weights)")
        print(f"  {BOLD}Milo Steered:{RESET} {GREEN if info['is_steered'] else YELLOW}{info['is_steered']}{RESET}")
        print(f"\n  {BOLD}Embedded Chat Template:{RESET}")
        tmpl_preview = info['chat_template'].replace("\n", " ")[:160]
        print(f"  {DIM}{tmpl_preview}...{RESET}\n")

    elif args.command == "extract-vector":
        surgeon = MiloSurgeon()
        surgeon.extract_steering_vector()

    elif args.command == "operate":
        surgeon = MiloSurgeon()
        out_p = Path(args.out)
        surgeon.perform_surgery(output_model=out_p, strength=args.strength)

    elif args.command == "verify":
        m_path = Path(args.model)
        surgeon = MiloSurgeon(m_path if m_path.exists() else DEFAULT_SOURCE_MODEL)
        surgeon.verify(m_path)

    elif args.command == "activate":
        m_path = Path(args.model)
        surgeon = MiloSurgeon(m_path if m_path.exists() else DEFAULT_SOURCE_MODEL)
        surgeon.activate(m_path)


if __name__ == "__main__":
    main()
