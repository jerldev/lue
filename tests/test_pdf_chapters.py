"""Tests for PDF chapter splitting in lue.content_parser.

Upstream LUE only detects English "chapter" headings in PDFs, so books in
other languages (e.g. Spanish "Capítulo N") end up as a single chapter and
the z/x chapter navigation does nothing. These tests pin the extracted
splitting helper: multilingual heading detection while preserving the
original English behavior exactly.
"""

from lue.content_parser import _is_pdf_chapter_heading, _split_pdf_chapters

LONG_BODY = (
    "Este es un parrafo de cuerpo del libro con suficientes caracteres para "
    "pasar los filtros de longitud y con contenido real de lectura."
)


class TestEnglishBehaviorPreserved:
    """The original upstream rule: 'chapter' (any mention) in a <10-word paragraph."""

    def test_english_rule_equivalent_to_baseline_loop(self):
        """Drift guard: the helper must stay output-identical to the original
        upstream inline loop on a mixed corpus."""
        def baseline(paragraphs):
            chapters = []
            current_chapter = []
            for paragraph in paragraphs:
                if "chapter" in paragraph.lower() and len(paragraph.split()) < 10:
                    if current_chapter:
                        chapters.append(current_chapter)
                    current_chapter = [paragraph]
                else:
                    current_chapter.append(paragraph)
            if current_chapter:
                chapters.append(current_chapter)
            if not chapters:
                return [list(paragraphs)]
            return chapters

        corpus = [
            LONG_BODY,
            "Chapter 1 The Beginnings of Everything",
            "this chapter is mentioned mid text",
            "Chapter",
            LONG_BODY,
            "Chapter 2 Next",
            "",
        ]
        assert _split_pdf_chapters(corpus) == baseline(corpus)

    def test_english_heading_starts_new_chapter(self):
        paragraphs = [
            LONG_BODY,
            "Chapter 1 The Beginnings of Everything",
            LONG_BODY,
            "Chapter 2 The New World Order",
            LONG_BODY,
        ]
        chapters = _split_pdf_chapters(paragraphs)
        assert len(chapters) == 3
        assert chapters[1][0] == "Chapter 1 The Beginnings of Everything"
        assert chapters[2][0] == "Chapter 2 The New World Order"

    def test_english_word_in_long_paragraph_is_not_a_heading(self):
        paragraphs = [
            "Chapter one of this book talks about " + LONG_BODY,
            LONG_BODY,
        ]
        chapters = _split_pdf_chapters(paragraphs)
        assert len(chapters) == 1

    def test_no_headings_returns_single_chapter(self):
        chapters = _split_pdf_chapters([LONG_BODY, LONG_BODY])
        assert len(chapters) == 1
        assert len(chapters[0]) == 2

    def test_empty_input_returns_single_empty_chapter(self):
        assert _split_pdf_chapters([]) == [[]]

    def test_content_before_first_heading_is_chapter_zero(self):
        paragraphs = [LONG_BODY, "Chapter 1 Title Here", LONG_BODY]
        chapters = _split_pdf_chapters(paragraphs)
        assert len(chapters) == 2
        assert chapters[0] == [LONG_BODY]


class TestSpanishChapters:
    """Regression: Spanish PDFs must split into chapters (user's core request)."""

    def test_capitulo_with_number_starts_new_chapter(self):
        paragraphs = [
            "Texto inicial del libro antes del primer capitulo.",
            "Capítulo 1 Los cambios del mercado mundial",
            LONG_BODY,
            "CAPÍTULO 2 Organización y personas",
            LONG_BODY,
        ]
        chapters = _split_pdf_chapters(paragraphs)
        assert len(chapters) == 3
        assert chapters[1][0] == "Capítulo 1 Los cambios del mercado mundial"
        assert chapters[2][0] == "CAPÍTULO 2 Organización y personas"

    def test_capitulo_without_accent(self):
        paragraphs = [LONG_BODY, "Capitulo 3 La maquina", LONG_BODY]
        chapters = _split_pdf_chapters(paragraphs)
        assert len(chapters) == 2

    def test_capitulo_with_roman_numerals(self):
        paragraphs = [LONG_BODY, "Capítulo IV Etapa decisiva", LONG_BODY, "Capítulo XIX", LONG_BODY]
        chapters = _split_pdf_chapters(paragraphs)
        assert len(chapters) == 3

    def test_word_capitulo_without_number_is_not_a_heading(self):
        paragraphs = [
            "En el capítulo anterior explicamos con detalle " + LONG_BODY,
            LONG_BODY,
        ]
        chapters = _split_pdf_chapters(paragraphs)
        assert len(chapters) == 1

    def test_long_paragraph_mentioning_capitulo_number_is_not_a_heading(self):
        filler = "palabra " * 20
        paragraphs = [f"El capítulo 1 menciona {filler}", LONG_BODY]
        chapters = _split_pdf_chapters(paragraphs)
        assert len(chapters) == 1

    def test_capitulo_heading_merges_pdf_block_text(self):
        """Real-world shape (Ray Dalio, es): PyMuPDF merges the heading block
        with all the body text that follows it on the page, so the heading
        paragraph starts with the keyword and runs for hundreds of chars."""
        paragraphs = [
            LONG_BODY,
            "CAPÍTULO 1 EL GRAN CICLO (EN POCAS PALABRAS) " + LONG_BODY + " " + LONG_BODY,
            "Otro parrafo de cuerpo normal que sigue al encabezado fusionado.",
            "CAPÍTULO 2 LOS PRINCIPIOS FUNDAMENTALES " + LONG_BODY,
        ]
        chapters = _split_pdf_chapters(paragraphs)
        assert len(chapters) == 3
        assert chapters[1][0].startswith("CAPÍTULO 1")
        assert chapters[2][0].startswith("CAPÍTULO 2")

    def test_multilingual_rule_is_start_anchored(self):
        assert _is_pdf_chapter_heading("El capítulo 3 dice algo más") is False
        assert _is_pdf_chapter_heading("Los capítulos anteriores") is False
        assert _is_pdf_chapter_heading("Capítulo 3 dice algo más") is True

    def test_short_standalone_heading_detection(self):
        """Short heading-only blocks must be recognized (they are otherwise
        dropped by the >25 char paragraph filter)."""
        assert _is_pdf_chapter_heading("CAPÍTULO 1") is True
        assert _is_pdf_chapter_heading("Capítulo XII") is True
        assert _is_pdf_chapter_heading("Véase el capítulo 1") is False


class TestOtherLanguages:
    def test_french_chapitre(self):
        chapters = _split_pdf_chapters([LONG_BODY, "Chapitre 2 Les fondements", LONG_BODY])
        assert len(chapters) == 2

    def test_german_kapitel(self):
        chapters = _split_pdf_chapters([LONG_BODY, "Kapitel 5 Die Prinzipien", LONG_BODY])
        assert len(chapters) == 2

    def test_italian_capitolo(self):
        chapters = _split_pdf_chapters([LONG_BODY, "Capitolo 3 Le regole", LONG_BODY])
        assert len(chapters) == 2
