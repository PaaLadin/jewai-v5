"""Provider registry. Importing this module never opens a browser."""
from importlib import import_module

PROVIDERS = {
    "deepseek": {"label": "DeepSeek", "module": "Adapters.deepseek", "class": "DeepSeek",
                 "url": "https://chat.deepseek.com/", "experimental": False},
    "qwen": {"label": "Qwen", "module": "Adapters.qwen", "class": "Qwen",
             "url": "https://chat.qwen.ai/", "experimental": False},
    "alice": {"label": "Alice", "module": "Adapters.alice", "class": "Alice",
              "url": "https://alice.yandex.ru/", "experimental": False},
    "perplexity": {"label": "Perplexity", "module": "Adapters.perplexity", "class": "Perplexity",
                   "url": "https://www.perplexity.ai/", "experimental": True},
}


def provider(model):
    key = str(model).strip().lower()
    if key not in PROVIDERS:
        raise ValueError("unsupported adapter: " + key)
    return PROVIDERS[key]


def create(model):
    item = provider(model)
    return getattr(import_module(item["module"]), item["class"])()


def choices():
    return [{"id": key, "label": item["label"], "url": item["url"],
             "experimental": item["experimental"]} for key, item in PROVIDERS.items()]
