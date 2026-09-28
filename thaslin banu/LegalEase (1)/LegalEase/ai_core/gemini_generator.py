"""Gemini integration. Falls back to an offline template if no API key is set,
so the whole app can be run and tested end-to-end without one."""
import config

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover
    genai = None


class GeminiDocumentGenerator:
    def __init__(self, model_name=None):
        self.model_name = model_name or config.GEMINI_MODEL
        self.model = None
        if config.GEMINI_API_KEY and genai is not None:
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(self.model_name)

    @staticmethod
    def _bullets(terms):
        items = [t.strip() for t in terms.split(";") if t.strip()]
        return "\n".join(f"- {t}" for t in items)

    def build_prompt(self, document_type, parties, terms, dates):
        return (
            f"Generate a comprehensive legal document titled '{document_type}'.\n"
            f"Involved parties: {parties}\n"
            f"Effective date: {dates}\n"
            f"Terms and conditions to include:\n{self._bullets(terms)}\n\n"
            "Use a formal legal structure with a title on the first line (prefixed with '## '), "
            "a preamble, numbered section headings (e.g. '1. Services:'), clearly written clauses, "
            "governing law, severability, and a signature block. "
            "Use placeholders in [square brackets] for any missing details. "
            "Output plain text only, with no commentary before or after the document."
        )

    def generate_document(self, document_type, parties, terms, dates):
        if self.model is None:
            return self._offline_template(document_type, parties, terms, dates)
        response = self.model.generate_content(
            self.build_prompt(document_type, parties, terms, dates)
        )
        return response.text

    def _offline_template(self, document_type, parties, terms, dates):
        clauses = "\n\n".join(
            f"{i}. Clause {i}:\n{t.strip()}."
            for i, t in enumerate((x for x in terms.split(";") if x.strip()), start=1)
        )
        return (
            f"## {document_type}\n\n"
            f"This Agreement is made effective as of {dates}.\n\n"
            f"Between:\n{parties}\n\n"
            "WITNESSETH:\n"
            "The parties agree to the following terms and conditions.\n\n"
            f"{clauses}\n\n"
            "Governing Law:\nThis Agreement shall be governed by the laws of [State/Country].\n\n"
            "Severability:\nIf any provision is held invalid, the remaining provisions remain in full force.\n\n"
            "IN WITNESS WHEREOF, the parties have executed this Agreement as of the Effective Date.\n\n"
            "______________________\nAuthorized Signature (Party 1)\n\n"
            "______________________\nAuthorized Signature (Party 2)\n\n"
            "[Offline template - set GEMINI_API_KEY in .env for AI-generated content]"
        )
