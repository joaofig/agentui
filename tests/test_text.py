import unittest

from src.services.text import count_words


class CountWordsTests(unittest.TestCase):
    def test_counts_words_in_a_sentence(self) -> None:
        """Count words separated by spaces in a sentence."""
        self.assertEqual(count_words("The quick brown fox jumps over the lazy dog."), 9)

    def test_counts_words_separated_by_whitespace(self) -> None:
        """Count words separated by tabs and newlines."""
        self.assertEqual(count_words("one\ttwo\nthree"), 3)

    def test_ignores_punctuation_and_case(self) -> None:
        """Count case-insensitive words around punctuation."""
        self.assertEqual(count_words("Hello, WORLD! Don't stop."), 5)

    def test_returns_zero_for_empty_or_whitespace_text(self) -> None:
        """Return zero when the input contains no word characters."""
        for text in ("", " \t\n", "...!?", "---"):
            with self.subTest(text=text):
                self.assertEqual(count_words(text), 0)


if __name__ == "__main__":
    unittest.main()
