# LangCheckChat

A RAG application that lets you ask questions about LangCheck, and then
evaluates its own responses using LangCheck metrics.

## Demo

https://github.com/citadel-ai/langcheckchat/assets/107823399/1ff5cdc0-fbf3-4317-9877-bea4bac2401e

## Installation

```
# Clone the repo
git clone https://github.com/citadel-ai/langcheckchat.git

# Set up a virtual environment
cd langcheckchat
python -m venv env
source env/bin/activate

# Install the requirements
pip install -r requirements.txt
```

## Usage

LangCheckChat is a simple web app that answers your questions about LangCheck,
and then evaluates its responses using LangCheck. The component that answers
your question is a RAG system built using
[LlamaIndex](https://github.com/run-llama/llama_index), which in turn uses
OpenAI's models under the hood. The component that evaluates the system's
responses is built using LangCheck, which also uses OpenAI's models for a subset
of the metrics. We support both the standard OpenAI API and Azure's OpenAI API.

### 1. Update the environment variables with your OpenAI API details

In [.env](.env), first configure the models you want to use for the RAG system
in the top section. For example, if you set `OPENAI_API_TYPE = 'openai'` (which
is the default), then you need to replace the line
`OPENAI_API_KEY = 'YOUR_OPENAI_API_KEY'` with your actual OpenAI API key.

Then, configure the model that you want to use to compute LangCheck metrics in
the bottom section. This will often be the same model as the one you use for the
RAG system, but it doesn't have to be (e.g. you could use gpt-4 for evaluation
but the cheaper gpt-3.5-turbo for RAG).

(Optional) By default, we set `ENABLE_LOCAL_LANGCHECK_MODELS = 'False'`, which
disables certain LangCheck metrics that are quite slow at startup since they
require downloading a fairly large model locally. If you want to try these out
though, set to `ENABLE_LOCAL_LANGCHECK_MODELS = 'True'`.

### 2. Run the app

Start the app by running
```
python app.py
```

You should see an output that says `Running on http://127.0.0.1:5000` - click
on the link to open the app in your browser.

### 3. Ask questions!

Once the app is running, you can now ask some questions! The app will respond
with an answer to your question, and then some LangCheck metrics will
automatically be computed.

You can view the history by clicking "See Q&A Logs".

### (Optional) 4. Provide a reference answer

By default, only the Reference-Free and Source-Based metrics are shown. If you
enter a reference answer to your question, the Reference-Based metrics will
also get computed.
