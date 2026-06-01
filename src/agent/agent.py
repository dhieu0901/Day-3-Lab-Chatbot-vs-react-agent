import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Union

from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger


class ReActAgent:
    """
    ReAct Agent: Thought → Action → Observation → Final Answer
    """

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 10):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.trace: List[Dict[str, str]] = []

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            f"- {t['name']}: {t['description']}" for t in self.tools
        )
        return f"""
You are an intelligent ReAct agent. You have access to the following tools:
{tool_descriptions}

You MUST follow this exact format for EVERY step:

Thought: explain your reasoning for the current step.
Action: {{"tool": "tool_name", "args": {{"arg_name": "value"}}}}
Observation: (Wait for the system to provide the result of the tool)

When you have enough information to answer the user's request, use this format:

Thought: I now have the final answer.
Final Answer: your detailed response to the user.

CRITICAL RULES (V2):
1. 'Action' MUST be raw, valid JSON. DO NOT wrap it in Markdown code blocks (like ```json).
2. ONLY use the exact tool names provided above. DO NOT guess or hallucinate tool names.
3. If an Observation returns an Error, read it and fix your args or try another tool.
4. NEVER output 'Observation:' yourself. The system will provide it.
5. Answer in the same language as the user.
"""

    def run(self, user_input: str) -> Union[str, Dict[str, Any]]:
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

        start = time.time()
        self.trace = []
        conversation = f"User question: {user_input}\n"
        tools_used = 0
        charts: List[Dict[str, str]] = []
        indicators: List[Dict[str, Any]] = []
        final_answer: Optional[str] = None

        for step in range(self.max_steps):
            result = self.llm.generate(conversation, system_prompt=self.get_system_prompt())
            content = result.get("content", "")

            # Prevent hallucinated Observations (from remote fix)
            obs_index = content.find("Observation:")
            if obs_index != -1:
                content = content[:obs_index].strip()

            logger.log_event("LLM_METRIC", {
                "step": step + 1,
                "latency_ms": result.get("latency_ms"),
                "usage": result.get("usage"),
            })

            thought = self._parse_thought(content)
            if thought:
                self.trace.append({
                    "type": "thought",
                    "label": f"Step {step + 1} — Thought",
                    "content": thought,
                })

            final = self._parse_final_answer(content)
            if final:
                self.trace.append({"type": "answer", "label": "Final Answer", "content": final})
                final_answer = final
                break

            action = self._parse_action(content)
            if not action:
                err = "Error: No valid Action JSON or Final Answer found."
                self.trace.append({"type": "error", "label": "Parse Error", "content": content})
                conversation += f"\n{content}\nObservation: {err}\n"
                logger.log_event("LLM_METRIC", {"error": "FORMAT_ERROR", "content": content})
                time.sleep(3)
                continue

            self.trace.append({
                "type": "action",
                "label": f"Step {step + 1} — Action",
                "content": f"{action['tool']}({action['args']})",
            })

            observation = self._execute_tool(action["tool"], action["args"])
            tools_used += 1
            self._collect_artifacts(action["tool"], observation, charts, indicators)

            self.trace.append({
                "type": "observation",
                "label": f"Step {step + 1} — Observation",
                "content": observation[:2000],
            })

            logger.log_event("TOOL_CALL", {"tool": action["tool"], "args": action["args"]})

            conversation += f"\n{content}\nObservation: {observation}\n"
            time.sleep(3)

        if not final_answer:
            final_answer = "Agent reached maximum steps without finding a final answer."
            self.trace.append({"type": "error", "label": "Timeout", "content": final_answer})

        latency_ms = int((time.time() - start) * 1000)
        logger.log_event("AGENT_END", {"steps": len(self.trace), "tools_used": tools_used})

        return {
            "mode": "agent",
            "answer": final_answer,
            "trace": self.trace,
            "tools_used": tools_used,
            "latency_ms": latency_ms,
            "charts": charts,
            "indicators": indicators,
        }

    def _parse_thought(self, text: str) -> Optional[str]:
        match = re.search(
            r"Thought:\s*(.+?)(?=\nAction:|\nFinal Answer:|$)",
            text, re.DOTALL | re.IGNORECASE,
        )
        return match.group(1).strip() if match else None

    def _parse_final_answer(self, text: str) -> Optional[str]:
        match = re.search(r"Final Answer:\s*(.+)", text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _parse_action(self, text: str) -> Optional[Dict[str, Any]]:
        action_start = text.find("Action:")
        if action_start == -1:
            return None

        json_start = text.find("{", action_start)
        if json_start == -1:
            return None

        action_data = None
        json_str = text[json_start:]
        for i in range(len(json_str), 0, -1):
            if json_str[i - 1] == "}":
                try:
                    action_data = json.loads(json_str[:i])
                    break
                except json.JSONDecodeError:
                    continue

        if not action_data or not action_data.get("tool"):
            return None

        return {
            "tool": str(action_data["tool"]).strip(),
            "args": action_data.get("args") or {},
        }

    def _collect_artifacts(
        self,
        tool_name: str,
        observation: str,
        charts: List[Dict[str, str]],
        indicators: List[Dict[str, Any]],
    ) -> None:
        try:
            data = json.loads(observation)
        except json.JSONDecodeError:
            return
        if data.get("status") != "ok":
            return

        if tool_name == "plot_stock_chart":
            filename = os.path.basename(data.get("file_path", ""))
            if filename:
                ticker = filename.replace("_chart.png", "").upper()
                charts.append({"ticker": ticker, "filename": filename})
        elif tool_name == "get_technical_indicators":
            indicators.append(data)

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        for tool in self.tools:
            if tool["name"] == tool_name:
                try:
                    return tool["function"](**args)
                except Exception as e:
                    return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

        logger.log_event("LLM_METRIC", {"error": "HALLUCINATION_ERROR", "tool_name": tool_name})
        return json.dumps(
            {"status": "error", "message": f"Tool '{tool_name}' not found."},
            ensure_ascii=False,
        )
