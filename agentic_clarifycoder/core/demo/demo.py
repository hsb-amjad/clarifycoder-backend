"""
ClarifyCoder-Agent Demo
=======================

Run the ClarifyCoder multi-agent system with baseline or LLM agents.

Usage:
    python -m agentic_clarifycoder.core.demo.demo --clarify_mode baseline --code_mode baseline --eval_mode baseline --refine_mode baseline --answer_mode human
    python -m agentic_clarifycoder.core.demo.demo --clarify_mode llm --code_mode llm --eval_mode llm --refine_mode llm --answer_mode human
    -> run from root clarifycoder-backend

Extra args:
    --num_prompts  N   Number of prompts to sample (default: random 5–10)
    --seed S         Random seed for reproducibility
    --log_file PATH  Unified log file to save metrics + results
"""

import json
import random
import argparse
from ..utils.logger import Logger
from colorama import Fore, Style, init

# === Baseline agents ===
from ..agents.clarify_agent_rulebased import ClarifyAgent as ClarifyAgentBaseline
from ..agents.code_agent_rulebased import CodeAgent as CodeAgentBaseline
from ..agents.eval_agent_rulebased import EvalAgent as EvalAgentBaseline
from ..agents.refine_agent_rulebased import RefineAgent as RefineAgentBaseline

# === LLM agents ===
from ..agents.clarify_agent_llm import ClarifyAgentLLM
from ..agents.code_agent_llm import CodeAgentLLM
from ..agents.eval_agent_llm import EvalAgentLLM
from ..agents.refine_agent_llm import RefineAgentLLM

# === AnswerAgent (human only) ===
from ..agents.answer_agent import AnswerAgent

# Initialize colorama
init(autoreset=True)


def colored_bar(label, value):
    """Pretty print colored bar for metrics."""
    colors = {
        "Pass": Fore.GREEN,
        "Fail": Fore.RED,
        "Unsupported": Fore.YELLOW,
        "Error": Fore.MAGENTA,
        "Invalid": Fore.CYAN,
    }
    color = colors.get(label, "")
    bar = "█" * value
    return f"{label:<12} | {color}{bar}{Style.RESET_ALL} {value}"


def main():
    # === CLI ARGUMENTS ===
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--clarify_mode", choices=["baseline", "llm"], default="baseline")
    parser.add_argument(
        "--code_mode", choices=["baseline", "llm"], default="baseline")
    parser.add_argument(
        "--eval_mode", choices=["baseline", "llm"], default="baseline")
    parser.add_argument(
        "--refine_mode", choices=["baseline", "llm"], default="baseline")
    parser.add_argument("--num_prompts", type=int, default=0)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--log_file", type=str, default=None)
    parser.add_argument("--answer_mode", choices=["human", "auto"], default="human",
                        help="Answer mode: human (interactive) or auto (LLM)")
    args = parser.parse_args()

    # === Initialize agents ===
    clarify = ClarifyAgentBaseline() if args.clarify_mode == "baseline" else ClarifyAgentLLM()
    code = CodeAgentBaseline() if args.code_mode == "baseline" else CodeAgentLLM()
    eval_agent = EvalAgentBaseline() if args.eval_mode == "baseline" else EvalAgentLLM()
    refine = RefineAgentBaseline() if args.refine_mode == "baseline" else RefineAgentLLM()

    # initialize AnswerAgent with CLI enabled
    answer_agent = AnswerAgent(mode=args.answer_mode, cli=True)

    logger = Logger()

    # === Load prompts ===
    with open("prompts.jsonl", "r", encoding="utf-8") as f:
        all_entries = [json.loads(line) for line in f]

    if args.seed is not None:
        random.seed(args.seed)

    if args.num_prompts > 0:
        prompts = random.sample(all_entries, k=min(
            args.num_prompts, len(all_entries)))
    else:
        prompts = random.sample(all_entries, k=random.randint(5, 10))

    # === Metrics ===
    total_prompts = len(prompts)
    total_ambiguous = 0
    total_clear = 0

    # Ambiguous-only
    amb_pass = amb_fail = amb_unsupported = amb_error = amb_invalid = 0
    # Clear-only
    clear_pass = clear_fail = clear_unsupported = clear_error = clear_invalid = 0
    # Global
    glob_pass = glob_fail = glob_unsupported = glob_error = glob_invalid = 0

    refine_attempts = refine_success = 0

    print(f"\n=== Running ClarifyCoder-Agent on {total_prompts} prompts ===")
    print(f"ClarifyAgent mode: {args.clarify_mode}")
    print(f"CodeAgent mode   : {args.code_mode}")
    print(f"EvalAgent mode   : {args.eval_mode}")
    print(f"RefineAgent mode : {args.refine_mode}")
    print(f"AnswerAgent mode : {args.answer_mode}")

    for entry in prompts:
        p = entry["prompt"]

        print("\n=== New Prompt ===")
        print("User prompt:", p)

        # Step 1: Clarification
        clar_result = clarify.run(p)
        print("ClarifyAgent status:", clar_result["status"])

        logger.log("clarify.jsonl", {
            "prompt": p,
            "status": clar_result["status"],
            "clarifications": clar_result["clarifications"]
        })

        # Step 1.5: Human answers
        if clar_result["clarifications"]:
            ans_result = answer_agent.run(
                clar_result["clarifications"], clar_result["original_prompt"])
            final_prompt = ans_result["augmented_prompt"]

            # log answers
            logger.log("answer.jsonl", {
                "prompt": p,
                "qa_pairs": ans_result["qa_pairs"]
            })
        else:
            final_prompt = clar_result["original_prompt"]

        # Step 2: Code Generation
        code_result = code.run(final_prompt)
        print("Generated Code:\n", code_result["code"])

        logger.log("code.jsonl", {
            "prompt": p,
            "clarified_prompt": final_prompt,
            "code": code_result["code"]
        })

        # Step 3: Evaluation
        eval_result = eval_agent.run(code_result["code"])
        print("EvalAgent result:", eval_result)

        logger.log("eval.jsonl", {
            "prompt": p,
            "function": eval_result.get("function"),
            "status": eval_result["status"],
            "details": eval_result["details"]
        })

        # Step 4: Refinement
        if eval_result["status"] in ["fail", "error", "unsupported", "invalid"]:
            refine_attempts += 1
            refine_result = refine.run(code_result["code"], eval_result)
            print("RefineAgent action:", refine_result["action"])
            print("Refined Code:\n", refine_result["refined_code"])

            re_eval_result = eval_agent.run(refine_result["refined_code"])
            print("Re-evaluated Result:", re_eval_result)

            if re_eval_result["status"] == "pass":
                refine_success += 1

            logger.log("refine.jsonl", {
                "prompt": p,
                "action": refine_result["action"],
                "refined_code": refine_result["refined_code"],
                "re_eval_status": re_eval_result["status"]
            })

            eval_result = re_eval_result

        # === Metrics tracking ===
        if clar_result["status"] == "ambiguous":
            total_ambiguous += 1
            if eval_result["status"] == "pass":
                amb_pass += 1
            elif eval_result["status"] == "fail":
                amb_fail += 1
            elif eval_result["status"] == "unsupported":
                amb_unsupported += 1
            elif eval_result["status"] == "error":
                amb_error += 1
            elif eval_result["status"] == "invalid":
                amb_invalid += 1
        else:
            total_clear += 1
            if eval_result["status"] == "pass":
                clear_pass += 1
            elif eval_result["status"] == "fail":
                clear_fail += 1
            elif eval_result["status"] == "unsupported":
                clear_unsupported += 1
            elif eval_result["status"] == "error":
                clear_error += 1
            elif eval_result["status"] == "invalid":
                clear_invalid += 1

        # Global
        if eval_result["status"] == "pass":
            glob_pass += 1
        elif eval_result["status"] == "fail":
            glob_fail += 1
        elif eval_result["status"] == "unsupported":
            glob_unsupported += 1
        elif eval_result["status"] == "error":
            glob_error += 1
        elif eval_result["status"] == "invalid":
            glob_invalid += 1

    # === Metrics Summary ===
    print("\n=== Evaluation Metrics Summary ===")
    print(f"Total Prompts: {total_prompts}")
    print(f"Ambiguous Prompts: {total_ambiguous}")
    print(f"Clear Prompts: {total_clear}")

    crr = (total_ambiguous / total_prompts) * 100
    print(f"CRR (Clarification Request Rate) = {crr:.2f}%")

    arsr = (amb_pass / total_ambiguous * 100) if total_ambiguous > 0 else 0
    csr = (clear_pass / total_clear * 100) if total_clear > 0 else 0

    print(f"ARSR (Ambiguity-Resolved Success Rate) = {arsr:.2f}%")
    print(f"CSR (Clear Success Rate) = {csr:.2f}%")

    rfr = (refine_success / refine_attempts *
           100) if refine_attempts > 0 else 0
    print(f"RFR (Refinement Fix Rate) = {rfr:.2f}%")

    usr = (glob_unsupported / total_prompts) * 100
    print(f"USR (Unsupported Rate) = {usr:.2f}%")

    # ARSR Breakdown
    if total_ambiguous > 0:
        print("\n--- ARSR Breakdown (ambiguous only) ---")
        outcomes = {
            "Pass": amb_pass,
            "Fail": amb_fail,
            "Unsupported": amb_unsupported,
            "Error": amb_error,
            "Invalid": amb_invalid
        }
        for k, v in outcomes.items():
            print(colored_bar(k, v))
    else:
        print("\nNo ambiguous prompts → ARSR not applicable.")

    # CSR Breakdown
    if total_clear > 0:
        print("\n--- CSR Breakdown (clear only) ---")
        outcomes = {
            "Pass": clear_pass,
            "Fail": clear_fail,
            "Unsupported": clear_unsupported,
            "Error": clear_error,
            "Invalid": clear_invalid
        }
        for k, v in outcomes.items():
            print(colored_bar(k, v))

    # Global Outcomes
    print("\n--- Global Outcomes (all prompts) ---")
    global_outcomes = {
        "Pass": glob_pass,
        "Fail": glob_fail,
        "Unsupported": glob_unsupported,
        "Error": glob_error,
        "Invalid": glob_invalid
    }
    for k, v in global_outcomes.items():
        print(colored_bar(k, v))

    # === Unified log file ===
    if args.log_file:
        with open(args.log_file, "w", encoding="utf-8") as f:
            json.dump({
                "metrics": {
                    "CRR": crr,
                    "CSR": csr,
                    "ARSR": arsr,
                    "RFR": rfr,
                    "USR": usr,
                    "Coverage": (glob_pass / total_prompts) * 100
                },
                "outcomes": {
                    "ambiguous": {"pass": amb_pass, "fail": amb_fail,
                                  "unsupported": amb_unsupported,
                                  "error": amb_error, "invalid": amb_invalid},
                    "clear": {"pass": clear_pass, "fail": clear_fail,
                              "unsupported": clear_unsupported,
                              "error": clear_error, "invalid": clear_invalid},
                    "global": {"pass": glob_pass, "fail": glob_fail,
                               "unsupported": glob_unsupported,
                               "error": glob_error, "invalid": glob_invalid}
                }
            }, f, indent=2)


def run_single_prompt(prompt: str, mode: str = "baseline", answers: list = None, answer_mode: str = "auto"):
    clarify = ClarifyAgentBaseline() if mode == "baseline" else ClarifyAgentLLM()
    code = CodeAgentBaseline() if mode == "baseline" else CodeAgentLLM()
    eval_agent = EvalAgentBaseline() if mode == "baseline" else EvalAgentLLM()
    refine = RefineAgentBaseline() if mode == "baseline" else RefineAgentLLM()

    clar_result = clarify.run(prompt)
    clarifications = clar_result.get("clarifications", [])
    final_prompt = clar_result["original_prompt"]

    from ..agents.answer_agent import AnswerAgent
    answer_agent = AnswerAgent(mode=answer_mode)

    used_answers = []

    if clarifications:
        if answer_mode == "human" and not answers:
            return {
                "status": "awaiting_answers",
                "clarifications": clarifications,
                "answers": [],
                "output": None,
                "metrics": {}
            }
        ans_result = answer_agent.run(
            clarifications, clar_result["original_prompt"], answers
        )
        final_prompt = ans_result["augmented_prompt"]
        used_answers = ans_result["answers"]

    # Step 2: Code generation
    code_result = code.run(final_prompt)
    generated_code = code_result["code"]

    # Step 3: Initial evaluation
    eval_result = eval_agent.run(generated_code)

    # Step 4: Refinement (only if eval failed)
    refine_info = None
    rfr = 0.0
    if eval_result["status"] in ["Fail", "Error", "Unsupported", "Invalid"]:
        refine_result = refine.run(generated_code, eval_result)
        re_eval_result = eval_agent.run(refine_result["refined_code"])

        refine_info = {
            "action": refine_result["action"],
            "refined_code": refine_result["refined_code"],
            "re_eval_status": re_eval_result["status"]
        }

        if re_eval_result["status"] == "Pass":
            rfr = 1.0

        generated_code = refine_result["refined_code"]
        # ❌ Do NOT overwrite eval_result → keep initial status for display

    # === Metrics ===
    metrics = {
        "CRR": 1.0 if clar_result["status"] == "ambiguous" else 0.0,
        "CSR": 1.0 if clar_result["status"] == "clear" and eval_result["status"] == "pass" else 0.0,
        "ARSR": 1.0 if clar_result["status"] == "ambiguous" and eval_result["status"] == "pass" else 0.0,
        "RFR": rfr,
        "USR": 1.0 if eval_result["status"] == "unsupported" else 0.0,
    }

    return {
        "status": eval_result["status"],
        "clarifications": clarifications,
        "answers": used_answers,
        "output": generated_code,
        "metrics": metrics,
        "refine": refine_info
    }


if __name__ == "__main__":
    main()
