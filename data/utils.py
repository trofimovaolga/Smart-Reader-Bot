import re
import unicodedata


def sanitize_response(response: str) -> str:
    """Clean the response to make it safe for Telegram's MarkdownV2"""
    response = re.sub(r'(?<!\\)(?<!\*)[*_[\]()~>#\+\-=|{}.!]', lambda x: '\\' + x.group(), response)
    response = re.sub(r'\*\*\.', '**\\.', response)

    # Check for unbalanced curly brackets
    if response.count('{') > response.count('}'):
        response += '\n\}'

    # Check for unclosed code blocks
    code_block_open = len(re.findall(r'```', response)) % 2
    if code_block_open:
        response += '\n```'

    return response


def clean_md(content):
    """Clean markdown content by removing images and normalizing unicode"""
    content = re.sub(r'!\[(.*)]\((.*)\)', "", content)  # remove image lines
    content = unicodedata.normalize('NFKC', content)
    content = re.sub(r'[\x00-\x09\x0B-\x1F\x7F]', ' ', content)
    content = re.sub('[\n]+', '\n', content)
    content = re.sub(r'[ \t]+', ' ', content)
    content = re.sub(r'�', '', content)
    return content
