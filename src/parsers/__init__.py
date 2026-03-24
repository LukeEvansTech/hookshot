from src.parsers.generic import GenericParser
from src.parsers.ebay import EbayDeletionParser
from src.parsers.github import GithubParser
from src.parsers.template import TemplateParser

BUILTIN_PARSERS = {
    "ebay_deletion": EbayDeletionParser,
    "github": GithubParser,
}


def get_parser(parser_type: str, parser_name: str):
    if parser_type == "builtin" and parser_name in BUILTIN_PARSERS:
        return BUILTIN_PARSERS[parser_name]()
    if parser_type == "template" and parser_name:
        return TemplateParser(parser_name)
    return GenericParser()
