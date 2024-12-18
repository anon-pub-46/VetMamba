from transformers import MambaConfig, MambaForCausalLM, AutoTokenizer, Trainer, TrainingArguments
from datasets import load_dataset
from evaluate import load
import numpy as np
import warnings
from transformers import logging
logging.set_verbosity_error()
warnings.filterwarnings("ignore")
from trl import SFTTrainer
from peft import LoraConfig


checkpoint_path_model = 'mamba/mamba_ssm/retrain_checkpoints/checkpoint-517075'
checkpoint_path_qa_pairs = "mamba/mamba_ssm/mamba_finetune_results/checkpoint-600"
config_path = "mamba/mamba_ssm/checkpoints/checkpoint-3236/config.json"

config = MambaConfig.from_pretrained(config_path)
tokenizer = AutoTokenizer.from_pretrained(checkpoint_path_model)
model = MambaForCausalLM.from_pretrained(checkpoint_path_model, config=config, ignore_mismatched_sizes=True)

dataset_dir = 'repo/MedVetGPT/qa_generate/0508_short2_nodigit/'

datasets = load_dataset('json', data_files={
    'train': dataset_dir + 'train.json',
    'test': dataset_dir + 'test.json'
})

def tokenize_function(examples):
    inputs = [q for q in examples["Question"]]
    model_inputs = tokenizer(inputs, max_length=128, truncation=True, padding="max_length")
    model_inputs["labels"] = tokenizer(examples["Answer"], max_length=128, truncation=True, padding="max_length")["input_ids"]
    return model_inputs

tokenized_datasets = datasets.map(tokenize_function, batched=True)

rouge_metric = load("rouge")

def compute_metrics(eval_preds):
    preds, labels = eval_preds
    decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)

    result = rouge_metric.compute(predictions=decoded_preds, references=decoded_labels)
    result = {key: value.mid.fmeasure * 100 for key, value in result.items()}

    result["avg_rouge"] = np.mean(list(result.values()))
    return result

from datasets import load_dataset

training_args = TrainingArguments(
    output_dir="mamba/mamba_ssm/mamba_finetuned_results_1.4b",
    num_train_epochs=3,
    per_device_train_batch_size=8,
    logging_dir='mamba/mamba_ssm/mamba_finetuned_results_1.4b',
    logging_steps=100,
    learning_rate=2e-3,
    disable_tqdm=False,
    save_steps=100, 
    save_total_limit=3      
)

lora_config =  LoraConfig(
        r=8,
        target_modules=["x_proj", "embeddings", "in_proj", "out_proj"],
        task_type="CAUSAL_LM",
        bias="none"
)
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    args=training_args,
    peft_config=lora_config,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["test"]
)

# trainer.train()
trainer.train()

eval_results = trainer.evaluate()

import json

print(eval_results)
output_path = "mamba/mamba_ssm/mamba_finetuned_results_1.4b/eval_results.json"
with open(output_path, "w") as f:
    json.dump(eval_results, f, indent=4)

# CUDA_VISIBLE_DEVICES=6,7 python mamba/mamba_ssm/models/finetube_qa_pairs_mamba.py