# OpenAI Embeddings

This package implements the OpenAI Embeddings. The primary goal of this package is to provide support for OpenAI embeddings in both the pre-release version of the OpenAI client and in version one.

To ensure backward compatibility, the implementation for the pre-release version is contained in `prelease.py`, while the implementation for version one is in `release_v1.py`.

## Files

- `prelease.py`: This file contains the implementation for the pre-release version of the OpenAI client. It is designed to be fully compatible with the pre-release version, allowing users to utilize OpenAI embeddings even in this early stage.

- `release_v1.py`: This file contains the implementation for version one of the OpenAI client. It ensures that users can continue to use OpenAI embeddings as they transition to the official release version.

## Usage

To use the OpenAI embeddings with either the pre-release version or release version of the OpenAI client simply import

```
from vectordb.openai_embeddings import OpenAIEmbeddings
```

This will import the embeddings class compatible with your installed openai client
