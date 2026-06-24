from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    service_secret: str = ""
    max_file_size_mb: int = 100
    allowed_extensions: str = ".pdf,.docx,.pptx,.html,.htm,.md,.txt"
    log_level: str = "info"

    # Formula/code enrichment runs a vision-language model (CodeFormulaV2) on every
    # equation/code block. Accurate but very heavy on CPU — a math-dense PDF can peg the
    # machine and time out. Off by default; enable only where the hardware (ideally a GPU)
    # can take it, to get equations back as LaTeX.
    enable_enrichment: bool = False
    # OCR (CPU-bound) is only needed for scanned/image-only PDFs. Born-digital ebooks have
    # a real text layer, so it is off by default; turn on for scanned documents.
    do_ocr: bool = False
    # Some PDFs (often re-encoded ebooks) embed fonts whose f-ligature glyphs (ft, fr, fi, fl,
    # ff) carry no real ToUnicode mapping, so every reader falls back to a Private Use Area
    # codepoint that renders as a blank gap — e.g. 'Often' -> 'O⟦⟧en'. When enabled, each unique
    # broken glyph is recognised once by OCR'ing a word that contains it, then replaced
    # everywhere; glyphs that can't be recognised fall back to full-page OCR of their pages.
    # Born-digital PDFs (no PUA chars) are untouched.
    ocr_fallback: bool = True
    # Minimum number of PUA codepoints in the parsed text before ligature recovery runs. A small
    # floor avoids spinning up OCR over a stray decorative glyph.
    ocr_fallback_pua_threshold: int = 4
    # How many sample occurrences of each broken glyph to OCR; the majority reading wins, which
    # absorbs the occasional bad crop. More samples = more robust but slower per glyph.
    glyph_ocr_samples: int = 3
    # Resolution multiplier when rendering a page to crop a word for glyph OCR. Higher is sharper
    # (better recognition of small body text) but uses more memory per page.
    glyph_render_scale: float = 6.0
    # Extract embedded images so figures survive in the output. Cheap (region cropping, no
    # model inference) — required for the data URIs the reader renders.
    generate_picture_images: bool = True
    # Resolution multiplier for extracted images (1.0 = standard, 2.0 = sharper figures).
    images_scale: float = 2.0
    # Device for model inference: 'auto' (detect CUDA -> MPS -> CPU), 'cpu', 'cuda', 'mps'.
    accelerator_device: Literal["auto", "cpu", "cuda", "mps"] = "auto"
    # CPU threads for inference (used when running on CPU).
    num_threads: int = 4

    @property
    def allowed_extensions_set(self) -> set[str]:
        return {ext.strip() for ext in self.allowed_extensions.split(",")}

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


settings = Settings()
