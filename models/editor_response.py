from dataclasses import dataclass


@dataclass
class EditorResponse:
    editor_response_id: str
    editor_request_id: str
    content: str