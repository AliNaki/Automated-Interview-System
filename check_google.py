
try:
    from autogen_ext.models.google import GeminiChatCompletionClient
    print("GeminiChatCompletionClient available")
except ImportError:
    print("GeminiChatCompletionClient NOT available")
