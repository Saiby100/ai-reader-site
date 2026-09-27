from __future__ import annotations

import logging

from docling.datamodel.accelerator_options import AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from ..config import settings

logger = logging.getLogger(__name__)

_converter: DocumentConverter | None = None
# Built lazily on the first lossy-text-layer document — most PDFs never need it, so we
# avoid loading the OCR models at startup.
_ocr_converter: DocumentConverter | None = None
# Bare RapidOCR engine for recognising individual glyph crops; built lazily (see
# get_ocr_engine). Distinct from _ocr_converter, which is Docling's full-page OCR pipeline.
_ocr_engine = None


def load_models() -> None:
    global _converter
    logger.info(
        "Loading Docling models (enrichment=%s, ocr=%s, device=%s)...",
        settings.enable_enrichment,
        settings.do_ocr,
        settings.accelerator_device,
    )
    _converter = _make_converter()
    # Force model loading now (construction is lazy) so the first request isn't slowed
    # by model initialization.
    _converter.initialize_pipeline(InputFormat.PDF)
    logger.info("Docling models loaded")


def is_model_loaded() -> bool:
    return _converter is not None


def get_converter() -> DocumentConverter:
    """Return the converter built by ``load_models``, or raise if it has not run yet."""
    if _converter is None:
        raise RuntimeError("Models not loaded — call load_models() first")
    return _converter


def get_ocr_converter() -> DocumentConverter:
    """Return the full-page-OCR converter, building and warming it on first use."""
    global _ocr_converter
    if _ocr_converter is None:
        logger.info("Building full-page OCR fallback converter (RapidOCR)...")
        _ocr_converter = _make_converter(force_full_page_ocr=True)
        _ocr_converter.initialize_pipeline(InputFormat.PDF)
        logger.info("OCR fallback converter ready")
    return _ocr_converter


def get_ocr_engine():
    """Lazily build the RapidOCR engine used to recognise individual glyph crops.

    Distinct from ``get_ocr_converter`` (Docling's full-page OCR converter, used only as a
    backstop): this is a bare RapidOCR instance we call directly on small word images.
    """
    global _ocr_engine
    if _ocr_engine is None:
        from rapidocr import RapidOCR

        logger.info("Building RapidOCR engine for glyph recognition...")
        _ocr_engine = RapidOCR()
    return _ocr_engine


def _make_converter(*, force_full_page_ocr: bool = False) -> DocumentConverter:
    """Build a Docling converter for PDFs.

    The default converter is tuned for ordinary ebooks (text + images): image
    extraction is on (cheap) so figures survive, while OCR and formula/code enrichment
    default off because they are CPU-heavy and unnecessary for born-digital documents.
    Enrichment runs a vision-language model per equation/code block and can peg a CPU
    machine, so it is opt-in via ``settings.enable_enrichment`` for capable (ideally GPU)
    hardware.

    When ``force_full_page_ocr`` is set, the converter ignores the (possibly lossy) text
    layer and OCRs every page with RapidOCR. This is the backstop for PDFs whose embedded
    fonts have broken ligature mappings — see ``ligatures.repair_lossy_ligatures``.
    """
    options = PdfPipelineOptions()
    options.do_formula_enrichment = settings.enable_enrichment
    options.do_code_enrichment = settings.enable_enrichment
    options.do_ocr = settings.do_ocr or force_full_page_ocr
    if force_full_page_ocr:
        options.ocr_options = RapidOcrOptions(force_full_page_ocr=True)
    options.generate_picture_images = settings.generate_picture_images
    options.images_scale = settings.images_scale
    options.accelerator_options = AcceleratorOptions(
        device=settings.accelerator_device,
        num_threads=settings.num_threads,
    )
    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
    )
