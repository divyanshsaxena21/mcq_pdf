from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
from langchain.llms import HuggingFacePipeline
from langchain.prompts import PromptTemplate

# Evaluation model
eval_model_id = "google/flan-t5-base"
eval_tokenizer = AutoTokenizer.from_pretrained(eval_model_id)
eval_model = AutoModelForSeq2SeqLM.from_pretrained(eval_model_id)
eval_pipe = pipeline("text2text-generation", model=eval_model, tokenizer=eval_tokenizer, max_new_tokens=128)
llm_eval = HuggingFacePipeline(pipeline=eval_pipe)

criteria_prompts = {
    "format": PromptTemplate.from_template(
        "You are evaluating a multiple-choice question for proper JSON structure.\n"
        "Is the MCQ formatted as a valid JSON object with keys: 'statement', 'options', 'answer', and 'reasoning'?\n\n"
        "{question}\nAnswer:"),
    "language": PromptTemplate.from_template(
        "Is the question written entirely in English?\n\n{question}\nAnswer:"),
    "grammar": PromptTemplate.from_template(
        "Is the grammar of this question correct?\n\n{question}\nAnswer:"),
    "relevance": PromptTemplate.from_template(
        "Is the question relevant to the excerpt?\nExcerpt:\n{article}\n\nQuestion:\n{question}\nAnswer:"),
    "options": PromptTemplate.from_template(
        "Does this MCQ have one correct and four plausible distractors?\nExcerpt:\n{article}\n\nQuestion:\n{question}\nAnswer:")
}

def evaluate_mcq(mcq, article):
    qtext = f"Statement: {mcq.get('statement', '')}\nOptions: {' | '.join(mcq.get('options', []))}"
    results = {}
    for name, prompt in criteria_prompts.items():
        inputs = {"question": qtext}
        if "article" in prompt.input_variables:
            inputs["article"] = article
        response = (prompt | llm_eval).invoke(inputs).strip().lower()
        results[name] = response
    return results
