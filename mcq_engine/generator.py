import os
import json
import torch
import re
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from langchain.llms import HuggingFacePipeline
from langchain.prompts import PromptTemplate
from mcq_engine.evaluator import evaluate_mcq
from dotenv import load_dotenv  # ← NEW

# Load environment variables from .env file
load_dotenv()  # ← NEW

# Retrieve Hugging Face token from environment
hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")  # ← UPDATED
os.environ["HUGGINGFACEHUB_API_TOKEN"] = hf_token  # For compatibility


# Generation model
mixtral_model_id = "mistralai/Mistral-7B-Instruct-v0.3"
mixtral_tokenizer = AutoTokenizer.from_pretrained(mixtral_model_id, token=hf_token)
mixtral_model = AutoModelForCausalLM.from_pretrained(
    mixtral_model_id,
    device_map="auto",
    torch_dtype=torch.float16,
    token=hf_token,
)
mixtral_pipe = pipeline("text-generation", model=mixtral_model, tokenizer=mixtral_tokenizer, max_new_tokens=384)
llm_gen = HuggingFacePipeline(pipeline=mixtral_pipe)

base_gen_prompt = PromptTemplate.from_template("""
You are a university professor creating academic MCQs.

Glossary:
{glossary}

Excerpt:
{article}

Respond with only a single valid JSON object. Do not include explanations or multiple blocks. Format:
{{
  "reasoning": "...",
  "statement": "...",
  "options": ["a) ...", "b) ...", "c) ...", "d) ...", "e) ..."],
  "answer": "c"
}}
""")

def extract_last_json_block(text):
    matches = list(re.finditer(r'{[\s\S]*?}', text))
    for match in reversed(matches):
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            continue
    return None

def generate_glossary(article):
    prompt = f"Extract all technical terms and their definitions from this excerpt. Respond in JSON:\n{article}"
    result = llm_gen(prompt)
    try:
        text = result[0]["generated_text"]
        json_start = text.index("{")
        return json.loads(text[json_start:])
    except:
        return {}

def generate_mcq(article, glossary):
    prompt = base_gen_prompt.format(article=article, glossary=json.dumps(glossary))
    result = llm_gen(prompt)
    raw_output = result[0]["generated_text"]
    mcq = extract_last_json_block(raw_output)
    if mcq and all(k in mcq for k in ["reasoning", "statement", "options", "answer"]):
        return mcq
    return {"error": "Invalid JSON", "raw": raw_output}

def generate_valid_mcq(article):
    glossary = generate_glossary(article)
    mcq = generate_mcq(article, glossary)
    if "error" in mcq:
        return mcq, {}, []
    evals = evaluate_mcq(mcq, article)
    confidence = sum(v == "yes" for v in evals.values()) / len(evals) if evals else 0
    mcq["confidence"] = confidence
    return mcq, evals, []

# --- New function added here ---
def generate_mcqs_from_sections(sections):
    """
    Given a list of text sections, generate MCQs for each section.
    Returns a list of MCQ dictionaries.
    """
    all_mcqs = []
    for section in sections:
        mcq, evals, errors = generate_valid_mcq(section)
        if "error" not in mcq:
            all_mcqs.append(mcq)
        else:
            # Optionally log or handle errors here
            pass
    return all_mcqs
