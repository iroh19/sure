"""
S.U.R.E. × AQUA-7B — LoRA Fine-Tuning
=======================================
Cihaza göre otomatik backend seçer:
  • Apple Silicon (MPS) → MLX (mlx-lm)   — 4-bit quant, düşük bellek
  • CUDA              → HuggingFace PEFT  — 4-bit bitsandbytes
  • CPU               → HuggingFace PEFT  — float32, yavaş

Kullanım:
  python finetune.py --data sure_finetune_data.jsonl --output ./sure-aqua-adapter
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import torch

BASE_MODEL = "KurmaAI/AQUA-1B"   # Gemma 3 1B tabanlı

SYSTEM_PREFIX = (
    "Sen S.U.R.E. adlı otonom mersin balığı (sturgeon) refah izleme sisteminin "
    "Türkçe karar motorusun. Kapalı Devre Balık Yetiştiriciliği (RAS) uzmanısın.\n\n"
    "GÜVENLİ ARALIKLAR: DO: 6.0-12.0 mg/L | Sıcaklık: 16-21°C | pH: 6.5-8.0 | TDS: 200-450 ppm\n\n"
)


# --------------------------------------------------------------------------- #
# Cihaz tespiti
# --------------------------------------------------------------------------- #
def detect_backend() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mlx"
    return "cpu"


# --------------------------------------------------------------------------- #
# Veri hazırlama
# --------------------------------------------------------------------------- #
def load_jsonl(path: str) -> list[dict]:
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def format_gemma(ex: dict) -> str:
    """Gemma 3 chat template formatı (<start_of_turn>)."""
    snapshot = json.dumps(
        {"sensor": ex.get("sensor", {}), "vision": ex.get("vision", {})},
        ensure_ascii=False,
    )
    response = json.dumps(ex.get("label", {}), ensure_ascii=False)
    user_content = (
        f"{SYSTEM_PREFIX}ANLIK VERİ:\n{snapshot}\n"
        "SADECE geçerli JSON döndür."
    )
    return (
        f"<start_of_turn>user\n{user_content}<end_of_turn>\n"
        f"<start_of_turn>model\n{response}<end_of_turn>"
    )


def prepare_mlx_data(records: list[dict], out_dir: Path) -> None:
    """MLX-LM beklediği formata dönüştür: train.jsonl + valid.jsonl"""
    out_dir.mkdir(parents=True, exist_ok=True)
    texts = [{"text": format_gemma(r)} for r in records]
    split = max(1, len(texts) - 1)
    train_set, valid_set = texts[:split], texts[split:]
    if not valid_set:
        valid_set = texts[:1]

    (out_dir / "train.jsonl").write_text(
        "\n".join(json.dumps(t, ensure_ascii=False) for t in train_set)
    )
    (out_dir / "valid.jsonl").write_text(
        "\n".join(json.dumps(t, ensure_ascii=False) for t in valid_set)
    )
    print(f"[data] {len(train_set)} train / {len(valid_set)} valid örnek hazırlandı.")


# --------------------------------------------------------------------------- #
# MLX fine-tune (Apple Silicon)
# --------------------------------------------------------------------------- #
def _hide_mpich() -> "Path | None":
    """
    Anaconda MPICH'i geçici gizler — MLX Open MPI gerektirir ama MPICH bulunca
    SIGABRT ile crash eder. Fine-tune bittikten sonra _restore_mpich() çağrılmalı.
    """
    mpich = Path("/opt/anaconda3/lib/libmpi.12.dylib")
    bak   = Path("/opt/anaconda3/lib/libmpi.12.dylib.bak")
    if mpich.exists() and not bak.exists():
        mpich.rename(bak)
        print("[finetune/mlx] MPICH geçici gizlendi (SIGABRT önleme).")
        return bak
    return None


def _restore_mpich(bak: "Path | None") -> None:
    if bak and bak.exists():
        bak.rename(bak.with_suffix(""))   # .bak'ı kaldır
        print("[finetune/mlx] MPICH geri yüklendi.")


def finetune_mlx(records: list[dict], output_dir: str, epochs: int) -> None:
    print("[finetune/mlx] Apple Silicon → mlx-lm LoRA")

    data_dir = Path(output_dir) / "_mlx_data"
    prepare_mlx_data(records, data_dir)

    iters = max(50, len(records) * epochs * 4)

    cmd = [
        sys.executable, "-m", "mlx_lm", "lora",
        "--model",        BASE_MODEL,
        "--train",
        "--data",         str(data_dir),
        "--iters",        str(iters),
        "--batch-size",   "1",
        "--num-layers",   "8",
        "--learning-rate","2e-4",
        "--adapter-path", output_dir,
    ]
    print(f"[finetune/mlx] Komut: {' '.join(cmd)}")

    bak = _hide_mpich()
    try:
        subprocess.run(cmd, check=True)
    finally:
        _restore_mpich(bak)

    print(f"[finetune/mlx] Adaptör kaydedildi: {output_dir}")
    print(f"[finetune/mlx] Kullanmak için: AQUA_ADAPTER_PATH={output_dir} uvicorn main:app ...")


# --------------------------------------------------------------------------- #
# HuggingFace PEFT fine-tune (CUDA / CPU)
# --------------------------------------------------------------------------- #
def finetune_hf(records: list[dict], output_dir: str, epochs: int,
                batch_size: int, device: str) -> None:
    import torch
    from datasets import Dataset
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import (
        AutoModelForCausalLM, AutoTokenizer,
        DataCollatorForLanguageModeling, TrainingArguments,
    )
    from trl import SFTTrainer

    use_cuda = device == "cuda"
    dtype    = torch.float16 if use_cuda else torch.float32
    print(f"[finetune/hf] Cihaz: {device}")

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, use_fast=True)
    tokenizer.pad_token = tokenizer.eos_token

    load_kwargs: dict = {"dtype": dtype, "device_map": {"": device}}
    if use_cuda:
        from transformers import BitsAndBytesConfig
        load_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True,
        )
        load_kwargs["device_map"] = "auto"

    model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, **load_kwargs)
    model = get_peft_model(model, LoraConfig(
        r=16, lora_alpha=32,
        target_modules=["q_proj","k_proj","v_proj","o_proj",
                        "gate_proj","up_proj","down_proj"],
        lora_dropout=0.05, bias="none", task_type=TaskType.CAUSAL_LM,
    ))
    model.print_trainable_parameters()

    dataset = Dataset.from_dict({"text": [format_gemma(r) for r in records]})
    print(f"[finetune/hf] {len(dataset)} örnek")

    trainer = SFTTrainer(
        model=model, tokenizer=tokenizer, train_dataset=dataset,
        args=TrainingArguments(
            output_dir=output_dir, num_train_epochs=epochs,
            per_device_train_batch_size=batch_size, gradient_accumulation_steps=4,
            learning_rate=2e-4, lr_scheduler_type="cosine", warmup_ratio=0.05,
            fp16=use_cuda, logging_steps=10, save_strategy="epoch",
            optim="paged_adamw_8bit" if use_cuda else "adamw_torch",
            report_to="none",
        ),
        dataset_text_field="text", max_seq_length=1024,
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
    )
    trainer.train()
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"[finetune/hf] Adaptör kaydedildi: {output_dir}")


# --------------------------------------------------------------------------- #
# Giriş noktası
# --------------------------------------------------------------------------- #
def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data",   default="sure_finetune_data.jsonl")
    p.add_argument("--output", default="./sure-aqua-adapter")
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--batch",  type=int, default=1)
    a = p.parse_args()

    records = load_jsonl(a.data)
    print(f"[finetune] {len(records)} örnek yüklendi.")

    backend = detect_backend()
    print(f"[finetune] Backend: {backend}")

    if backend == "mlx":
        finetune_mlx(records, a.output, a.epochs)
    else:
        finetune_hf(records, a.output, a.epochs, a.batch, backend)


if __name__ == "__main__":
    main()
