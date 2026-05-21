class LanguageDetector:
    def detect(self, text: str) -> str:
        for char in text:
            code = ord(char)
            if 0x0900 <= code <= 0x097F:
                return "hi"
            if 0x0B80 <= code <= 0x0BFF:
                return "ta"
        return "en"

