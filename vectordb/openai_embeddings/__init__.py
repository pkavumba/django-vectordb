import openai

if openai.__version__.startswith("0."):
    from .prelease import OpenAIEmbeddings  # noqa
elif openai.__version__.startswith("1."):
    from .release_v1 import OpenAIEmbeddings  # noqa
