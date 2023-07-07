# RelevanceBot: Evaluating Relevance with OpenAI API

The module **RelevanceBot** and **SmartScroll** evaluate the relevancy of chunks of a large body of text based on a provided query using OpenAI language models (like GPT-3). 

## RelevanceBot

The `RelevanceBot` is a class that acts as an interface with the OpenAI API. It creates an instance of OpenAI's `ChatCompletion` to evaluate if a chunk of text is relevant with respect to a supplied query. The response from the OpenAI API determines if the text chunk is relevant.

### _init_(self, api_key, model_name)

Initializes the RelevanceBot with the supplied API key and model name.

**Arguments**:
* `api_key`(str): Your OpenAI API key.
* `model_name`(str): The name of the OpenAI model to be used.

### is_relevant_chunk(self, chunk, query)

Method to determine if a chunk of text is relevant to the supplied query.

**Arguments:**
* `chunk`(str): Chunk of text to evaluate.
* `query`(str): Query in context of which the chunk is evaluated.

**Returns:**
* `True` if the chunk is relevant to the query; `False` otherwise.

## SmartScroll

The `SmartScroll` class utilizes an instance of `RelevanceBot` along with tokenization to chunk up a large piece of text. It creates an iterable over these chunks, only yielding those which are deemed relevant to the query.

### _init_(self, text, query, window_size, api_key, model_name, token_limit)

Initializes the SmartScroll with the supplied text, query, window size, api_key, model_name, and token limit.

**Arguments:**
* `text`(str): Large text to split into chunks
* `query`(str): Query to test chunk relevance to
* `window_size`(int): Size of the window to tokenize text into chunks for the `RelevanceBot`
* `api_key`(str): Your OpenAI API key
* `model_name`(str): The OpenAI model name to use
* `token_limit`(int): Maximum limit for the total tokens for OpenAI model input

### text_to_chunks(self)

Method to split the text into manageable chunks that can be passed to the `RelevanceBot` for evaluation.

**Returns:**
* A list of chunks that fit within the token demands of the OpenAI model.

### _iter_(self)

An iterator yielding chunks of text that are evaluated as relevant to the query.

**Returns:**
* A generator object where each subsequent call with `next()` returns a relevant text chunk.

## How to use

1. Import the necessary module.
2. Initialize an instance of `RelevanceBot` with your OpenAI API key and the model name.
3. Initialize an instance of `SmartScroll`, passing it your text, query, window size, OpenAI API key, model name, and token limit.
4. To get relevant chunks of text, iterate over the instance of `SmartScroll`. Each pass of the iteration will yield a relevant chunk of text.
