from jinja2 import Environment, BaseLoader


class TemplateParser:
    def __init__(self, template_str: str):
        self.template_str = template_str
        self._env = Environment(loader=BaseLoader(), autoescape=True)

    def parse(self, payload: dict, headers: dict, endpoint_name: str) -> dict:
        title = ""
        body = ""
        for line in self.template_str.strip().splitlines():
            rendered = self._env.from_string(line).render(data=payload, headers=headers)
            if rendered.startswith("title:"):
                title = rendered[len("title:"):].strip()
            elif rendered.startswith("body:"):
                body = rendered[len("body:"):].strip()
        return {"title": title or f"Webhook from {endpoint_name}", "body": body or "No body"}
