import re


def remove_line_padding(text):
    """
    Remove leading and trailing whitespace from each line in the text.
    :param text: The text to process.
    :return: The text with leading and trailing whitespace removed from each line.
    """
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def remove_thinking(text):
    """
    Remove <think>...</think> tags and their content from the text.
    :param text: The text to process.
    :return: The text with <think>...</think> tags and their content removed.
    """
    stripped_text = text.strip()
    if stripped_text.startswith("<think>") and "</think>" in stripped_text:
        return re.sub(r"<think>.*?</think>", "", stripped_text, flags=re.DOTALL)
    return stripped_text


def response_to_text(response):
    """
    Extract the content from the last message in the response.
    :param response: The response dictionary containing messages.
    :return: The content of the last message, or an empty string if no messages are present.
    """
    messages = response.get("messages", [])
    if not messages or len(messages) == 0:
        return ""
    return messages.pop().content