"""
AQUA-1B Inference Engine (Gemma 3 1B — KurmaAI)
=================================================
Cihaza göre otomatik backend seçer:
  • Apple Silicon → mlx-lm   (~2GB, quantization gerekmez)
  • CUDA / CPU   → transformers (BF16 / float32)

Prompt formatı: Gemma 3 chat template (<start_of_turn>)
apply_chat_template kullanır — model değişse bile format otomatik.
"""
from __future__ import annotations

import json
import os
import re
import torch
from pathlib import Path

BASE_MODEL_ID  = os.getenv("AQUA_BASE_MODEL", "KurmaAI/AQUA-1B")
ADAPTER_PATH   = os.getenv("AQUA_ADAPTER_PATH", "").strip()
MAX_NEW_TOKENS = int(os.getenv("AQUA_MAX_TOKENS", "512"))
TEMPERATURE    = float(os.getenv("AQUA_TEMPERATURE", "0.3"))

# S.U.R.E. sistem talimatı — tüm promptlara eklenir
SYSTEM_PROMPT = (
    "Sen S.U.R.E. adlı otonom mersin balığı (sturgeon) refah izleme sisteminin "
    "Türkçe karar motorusun. Kapalı Devre Balık Yetiştiriciliği (RAS) uzmanısın.\n\n"
    "GÜVENLİ ARALIKLAR:\n"
    "- Çözünmüş Oksijen (DO): 6.0-12.0 mg/L  →  <6.0 = KRİTİK\n"
    "- Sıcaklık: 16-21 °C\n"
    "- pH: 6.5-8.0\n"
    "- TDS: 200-450 ppm\n"
    "- avg_activity <0.002 → hareketsizlik/stres şüphesi"
)


def _detect_backend() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mlx"
    return "cpu"


BACKEND = _detect_backend()

# --------------------------------------------------------------------------- #
# MLX backend (Apple Silicon)
# --------------------------------------------------------------------------- #
_mlx_model     = None
_mlx_tokenizer = None


def _load_mlx() -> None:
    global _mlx_model, _mlx_tokenizer
    if _mlx_model is not None:
        return
    from mlx_lm import load
    adapter = ADAPTER_PATH if ADAPTER_PATH and Path(ADAPTER_PATH).exists() else None
    print(f"[AQUA/mlx] Yükleniyor: {BASE_MODEL_ID}"
          + (f" + adaptör: {adapter}" if adapter else ""))
    _mlx_model, _mlx_tokenizer = load(BASE_MODEL_ID, adapter_path=adapter)
    print("[AQUA/mlx] Hazır.")


def _apply_template_mlx(user_content: str) -> str:
    """Gemma 3 chat template'i mlx tokenizer ile uygular."""
    messages = [{"role": "user", "content": user_content}]
    if hasattr(_mlx_tokenizer, "apply_chat_template"):
        return _mlx_tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
    # Fallback: manuel Gemma format
    return (
        f"<start_of_turn>user\n{user_content}<end_of_turn>\n"
        "<start_of_turn>model\n"
    )


def _generate_mlx(user_content: str, temp: float = TEMPERATURE) -> str:
    _load_mlx()
    from mlx_lm import generate
    from mlx_lm.sample_utils import make_sampler
    prompt = _apply_template_mlx(user_content)
    return generate(
        _mlx_model, _mlx_tokenizer,
        prompt=prompt,
        max_tokens=MAX_NEW_TOKENS,
        sampler=make_sampler(temp=temp),
        verbose=False,
    )


# --------------------------------------------------------------------------- #
# HuggingFace backend (CUDA / CPU)
# --------------------------------------------------------------------------- #
_hf_model     = None
_hf_tokenizer = None


def _load_hf() -> None:
    global _hf_model, _hf_tokenizer
    if _hf_model is not None:
        return
    from transformers import AutoTokenizer, AutoModelForCausalLM

    # AQUA-1B: 1B parametre, BF16 ~2GB — Mac CPU/MPS'te quantization gerekmez
    dtype = torch.bfloat16 if BACKEND == "cuda" else torch.float32
    print(f"[AQUA/hf] Yükleniyor: {BASE_MODEL_ID}  (cihaz: {BACKEND}, dtype: {dtype})")

    _hf_tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL_ID, trust_remote_code=True
    )

    load_kwargs: dict = {
        "dtype": dtype,
        "trust_remote_code": True,
        "device_map": "auto" if BACKEND == "cuda" else {"": BACKEND},
    }
    _hf_model = AutoModelForCausalLM.from_pretrained(BASE_MODEL_ID, **load_kwargs)

    if ADAPTER_PATH and Path(ADAPTER_PATH).exists():
        from peft import PeftModel
        print(f"[AQUA/hf] Adaptör yükleniyor: {ADAPTER_PATH}")
        _hf_model = PeftModel.from_pretrained(_hf_model, ADAPTER_PATH)
        _hf_model = _hf_model.merge_and_unload()

    _hf_model.eval()
    print("[AQUA/hf] Hazır.")


def _apply_template_hf(user_content: str) -> "torch.Tensor":
    """Gemma 3 chat template'i HF tokenizer ile uygular, tensor döner."""
    messages = [{"role": "user", "content": user_content}]
    if hasattr(_hf_tokenizer, "apply_chat_template"):
        text = _hf_tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
    else:
        text = (
            f"<start_of_turn>user\n{user_content}<end_of_turn>\n"
            "<start_of_turn>model\n"
        )
    return _hf_tokenizer(text, return_tensors="pt").to(_hf_model.device)


def _generate_hf(user_content: str, temp: float = TEMPERATURE) -> str:
    _load_hf()
    inputs = _apply_template_hf(user_content)
    with torch.no_grad():
        out = _hf_model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=temp,
            do_sample=temp > 0,
            pad_token_id=_hf_tokenizer.eos_token_id,
        )
    return _hf_tokenizer.decode(
        out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
    ).strip()


# --------------------------------------------------------------------------- #
# Ortak arayüz
# --------------------------------------------------------------------------- #
def _load() -> None:
    if BACKEND == "mlx":
        _load_mlx()
    else:
        _load_hf()


def _generate(user_content: str, temp: float = TEMPERATURE) -> str:
    if BACKEND == "mlx":
        return _generate_mlx(user_content, temp)
    return _generate_hf(user_content, temp)


# --------------------------------------------------------------------------- #
# Prompt içerikleri (Gemma template'e gömülür)
# --------------------------------------------------------------------------- #
def _decision_user_content(snapshot: dict) -> str:
    return (
        f"{SYSTEM_PROMPT}\n\n"
        "KURAL: DO <6.0 ise status MUTLAKA 'critical'.\n"
        "SADECE geçerli JSON döndür:\n"
        '{"status":"ok|warning|critical","reasoning":"Türkçe açıklama",'
        '"recommendations":["öneri1","öneri2"]}\n\n'
        f"ANLIK VERİ:\n{json.dumps(snapshot, ensure_ascii=False)}"
    )


def _chat_user_content(message: str, context: dict) -> str:
    return (
        f"{SYSTEM_PROMPT}\n\n"
        "Kullanıcının sorularını kısa ve net Türkçe yanıtla.\n\n"
        f"SİSTEM VERİSİ:\n{json.dumps(context, ensure_ascii=False)}\n\n"
        f"SORU: {message}"
    )


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def generate_decision(snapshot: dict) -> dict:
    raw = _generate(_decision_user_content(snapshot))
    try:
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if not m:
            raise ValueError("model çıktısında JSON bulunamadı")
        parsed = json.loads(m.group())
        parsed["engine"] = f"aqua-1b/{BACKEND}"
        return parsed
    except (json.JSONDecodeError, AttributeError, ValueError):
        return {
            "engine": f"aqua-1b/{BACKEND}",
            "status": "ok",
            "reasoning": raw[:500],
            "recommendations": [],
        }


def generate_decision_stream(snapshot: dict):
    """Token-by-token generator for SSE streaming."""
    _load()
    user_content = _decision_user_content(snapshot)
    if BACKEND == "mlx":
        from mlx_lm import stream_generate
        from mlx_lm.sample_utils import make_sampler
        prompt = _apply_template_mlx(user_content)
        for response in stream_generate(
            _mlx_model, _mlx_tokenizer,
            prompt=prompt, max_tokens=MAX_NEW_TOKENS,
            sampler=make_sampler(temp=TEMPERATURE),
        ):
            yield response if isinstance(response, str) else response.text
    else:
        from transformers import TextIteratorStreamer
        from threading import Thread
        inputs = _apply_template_hf(user_content)
        streamer = TextIteratorStreamer(_hf_tokenizer, skip_special_tokens=True)
        thread = Thread(target=_hf_model.generate, kwargs={
            **inputs, "max_new_tokens": MAX_NEW_TOKENS,
            "temperature": TEMPERATURE, "do_sample": False,
            "pad_token_id": _hf_tokenizer.eos_token_id, "streamer": streamer,
        }, daemon=True)
        thread.start()
        try:
            for token in streamer:
                yield token
        finally:
            thread.join()


def generate_chat(message: str, context: dict) -> str:
    return _generate(_chat_user_content(message, context), temp=0.7)


def generate_chat_stream(message: str, context: dict):
    """Token-by-token generator for chat SSE streaming."""
    _load()
    user_content = _chat_user_content(message, context)
    if BACKEND == "mlx":
        from mlx_lm import stream_generate
        from mlx_lm.sample_utils import make_sampler
        prompt = _apply_template_mlx(user_content)
        for response in stream_generate(
            _mlx_model, _mlx_tokenizer,
            prompt=prompt, max_tokens=MAX_NEW_TOKENS,
            sampler=make_sampler(temp=0.7),
        ):
            yield response if isinstance(response, str) else response.text
    else:
        from transformers import TextIteratorStreamer
        from threading import Thread
        inputs = _apply_template_hf(user_content)
        streamer = TextIteratorStreamer(_hf_tokenizer, skip_special_tokens=True)
        thread = Thread(target=_hf_model.generate, kwargs={
            **inputs, "max_new_tokens": MAX_NEW_TOKENS,
            "temperature": 0.7, "do_sample": True,
            "pad_token_id": _hf_tokenizer.eos_token_id, "streamer": streamer,
        }, daemon=True)
        thread.start()
        try:
            for token in streamer:
                yield token
        finally:
            thread.join()
