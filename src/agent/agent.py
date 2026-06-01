import os
import re
import json
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

class ReActAgent:
    """
    A ReAct-style Agent that follows the Thought-Action-Observation loop.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        """
        System prompt that instructs the agent to follow ReAct loop and output JSON for tools.
        """
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
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

CRITICAL RULES:
1. 'Action' MUST be valid JSON matching the exact format.
2. Only use the tools provided above. Do not hallucinate tools.
3. NEVER output 'Observation:' yourself. The system will provide it.
"""

    def run(self, user_input: str) -> str:
        """
        The ReAct loop logic.
        1. Generate Thought + Action.
        2. Parse Action and execute Tool.
        3. Append Observation to prompt and repeat until Final Answer.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        
        current_prompt = user_input
        steps = 0

        while steps < self.max_steps:
            # TODO: Generate LLM response
            result = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
            content = result.get("content", "")
            
            # Print for visibility in the lab
            print(f"\n[Step {steps + 1}] LLM Output:\n{content}")
            
            # Check for Final Answer
            final_answer_match = re.search(r"Final Answer:\s*(.*)", content, re.DOTALL | re.IGNORECASE)
            if final_answer_match:
                final_answer = final_answer_match.group(1).strip()
                logger.log_event("AGENT_END", {"steps": steps + 1, "status": "success"})
                return final_answer
            
            # Parse Thought/Action from result
            action_start = content.find("Action:")
            action_data = None
            action_json_str = ""
            
            if action_start != -1:
                json_start = content.find("{", action_start)
                if json_start != -1:
                    json_str = content[json_start:]
                    for i in range(len(json_str), 0, -1):
                        if json_str[i-1] == "}":
                            try:
                                action_data = json.loads(json_str[:i])
                                action_json_str = json_str[:i]
                                break
                            except json.JSONDecodeError:
                                continue
                                
            if action_data:
                tool_name = action_data.get("tool")
                tool_args = action_data.get("args", {})
                
                # Execute tool
                print(f"--> Executing Tool: {tool_name} with {tool_args}")
                observation = self._execute_tool(tool_name, tool_args)
                print(f"--> Observation: {str(observation)[:200]}...") # Print snippet
                
                # Append Observation to prompt
                current_prompt += f"\n\n{content}\nObservation: {observation}\n"
            elif action_start != -1:
                observation = "Error: Invalid JSON format in Action. Please output valid JSON."
                current_prompt += f"\n\n{content}\nObservation: {observation}\n"
                logger.log_event("LLM_METRIC", {"error": "JSON_PARSER_ERROR", "content": content})
            else:
                # Fallback if no valid Action or Final Answer
                observation = "Error: No 'Action: {...}' or 'Final Answer: ...' found. Please follow the format."
                current_prompt += f"\n\n{content}\nObservation: {observation}\n"
                logger.log_event("LLM_METRIC", {"error": "FORMAT_ERROR", "content": content})
                
            steps += 1
            
        logger.log_event("AGENT_END", {"steps": steps, "status": "timeout"})
        return "Agent reached maximum steps without finding a final answer."

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """
        Helper method to execute tools dynamically.
        """
        for tool in self.tools:
            if tool['name'] == tool_name:
                try:
                    return tool['function'](**args)
                except Exception as e:
                    return f"Error executing tool {tool_name}: {str(e)}"
                    
        logger.log_event("LLM_METRIC", {"error": "HALLUCINATION_ERROR", "tool_name": tool_name})
        return f"Error: Tool '{tool_name}' not found. Check available tools."
