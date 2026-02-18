"""
THE RUBRIC - Multi-LLM Evaluation System
Harris Farm Markets AI Centre of Excellence

This script queries Claude, ChatGPT, and Grok with the same prompt
and presents results side-by-side for chairman evaluation.
"""

import anthropic
import openai
import httpx
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any
import os

class RubricEvaluator:
    """
    Multi-LLM evaluation system that queries multiple AI models
    and presents results for human decision-making.
    """
    
    def __init__(self):
        # API keys should be set as environment variables
        self.claude_client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY", "")
        )
        self.openai_client = openai.OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY", "")
        )
        self.grok_api_key = os.environ.get("GROK_API_KEY", "")
        
    async def query_claude(self, prompt: str, context: str = "") -> Dict[str, Any]:
        """Query Claude Sonnet 4.5"""
        start_time = datetime.now()
        
        try:
            message = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": f"{context}\n\n{prompt}" if context else prompt
                }]
            )
            
            end_time = datetime.now()
            latency = (end_time - start_time).total_seconds() * 1000
            
            return {
                "provider": "Claude Sonnet 4.5",
                "response": message.content[0].text,
                "tokens_used": message.usage.input_tokens + message.usage.output_tokens,
                "latency_ms": latency,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
        except Exception as e:
            return {
                "provider": "Claude Sonnet 4.5",
                "response": f"Error: {str(e)}",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
    
    async def query_chatgpt(self, prompt: str, context: str = "") -> Dict[str, Any]:
        """Query ChatGPT-4"""
        start_time = datetime.now()
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": context if context else "You are a helpful AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000
            )
            
            end_time = datetime.now()
            latency = (end_time - start_time).total_seconds() * 1000
            
            return {
                "provider": "ChatGPT-4 Turbo",
                "response": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
                "latency_ms": latency,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
        except Exception as e:
            return {
                "provider": "ChatGPT-4 Turbo",
                "response": f"Error: {str(e)}",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
    
    async def query_grok(self, prompt: str, context: str = "") -> Dict[str, Any]:
        """Query Grok (xAI)"""
        start_time = datetime.now()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.grok_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "grok-beta",
                        "messages": [
                            {"role": "system", "content": context if context else "You are Grok, a helpful AI assistant."},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 4000
                    },
                    timeout=60.0
                )
                
                end_time = datetime.now()
                latency = (end_time - start_time).total_seconds() * 1000
                
                result = response.json()
                
                return {
                    "provider": "Grok (xAI)",
                    "response": result["choices"][0]["message"]["content"],
                    "tokens_used": result.get("usage", {}).get("total_tokens", 0),
                    "latency_ms": latency,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success"
                }
        except Exception as e:
            return {
                "provider": "Grok (xAI)",
                "response": f"Error: {str(e)}",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
    
    async def run_rubric(self, prompt: str, context: str = "", 
                         providers: List[str] = ["claude", "chatgpt", "grok"]) -> Dict[str, Any]:
        """
        Run the rubric evaluation across multiple LLMs
        
        Args:
            prompt: The question or request to evaluate
            context: Additional context about Harris Farm or the situation
            providers: Which LLMs to query (default: all three)
            
        Returns:
            Dictionary containing all responses and metadata
        """
        tasks = []
        
        if "claude" in providers:
            tasks.append(self.query_claude(prompt, context))
        if "chatgpt" in providers:
            tasks.append(self.query_chatgpt(prompt, context))
        if "grok" in providers:
            tasks.append(self.query_grok(prompt, context))
        
        responses = await asyncio.gather(*tasks)
        
        return {
            "prompt": prompt,
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "responses": responses,
            "total_providers": len(responses),
            "successful_responses": sum(1 for r in responses if r["status"] == "success")
        }
    
    def format_results(self, results: Dict[str, Any]) -> str:
        """Format rubric results for display"""
        output = []
        output.append("=" * 80)
        output.append("THE RUBRIC - MULTI-LLM EVALUATION")
        output.append("=" * 80)
        output.append(f"\nPROMPT: {results['prompt']}")
        output.append(f"TIMESTAMP: {results['timestamp']}")
        output.append(f"PROVIDERS QUERIED: {results['total_providers']}")
        output.append(f"SUCCESSFUL RESPONSES: {results['successful_responses']}")
        output.append("\n" + "=" * 80)
        
        for i, response in enumerate(results['responses'], 1):
            output.append(f"\n{'=' * 80}")
            output.append(f"RESPONSE #{i}: {response['provider']}")
            output.append(f"{'=' * 80}")
            output.append(f"Status: {response['status']}")
            
            if response['status'] == 'success':
                output.append(f"Latency: {response.get('latency_ms', 0):.2f}ms")
                output.append(f"Tokens: {response.get('tokens_used', 0)}")
            
            output.append(f"\n{response['response']}")
            output.append("")
        
        output.append("=" * 80)
        output.append("CHAIRMAN'S DECISION REQUIRED")
        output.append("=" * 80)
        output.append("Review the responses above and select the winner.")
        output.append("Consider: accuracy, practicality, completeness, and alignment with Harris Farm strategy.")
        
        return "\n".join(output)


# ============================================================================
# EVALUATION SCRIPT FOR THE HUB BUILD
# ============================================================================

async def evaluate_hub_architecture():
    """
    Use the rubric to evaluate the optimal architecture for The Hub
    """
    
    evaluator = RubricEvaluator()
    
    context = """
    You are advising Harris Farm Markets, a premium Australian grocery retailer with 30+ stores.
    
    CO-CEO GUS wants to build an AI Centre of Excellence Hub this weekend with:
    - Custom web app foundation
    - Initial focus: Sales data queries + basic dashboards for finance team
    - Future capabilities: Multi-LLM evaluation, prompt training, self-improvement
    
    Current state:
    - Finance team already using Claude Excel add-in
    - Working on transport cost reduction, store profitability analysis
    - Need to query sales/ERP data with natural language
    - Want to become "prompt superstars"
    
    Tech stack considerations:
    - Must be production-ready but built quickly (weekend timeline)
    - Need to connect to their database (type TBD - likely SQL Server or PostgreSQL)
    - Must scale from finance team pilot to company-wide deployment
    """
    
    prompt = """
    Design the optimal architecture for "The Hub" - Harris Farm's AI Centre of Excellence.
    
    Requirements:
    1. Custom web app (React frontend + Python backend)
    2. Natural language queries to sales database → dashboards
    3. Multi-LLM evaluation system (Claude, ChatGPT, Grok) - "The Rubric"
    4. Prompt engineering training modules
    5. Self-improvement system that learns from user feedback
    6. Must be buildable this weekend as MVP
    
    Provide:
    - Recommended tech stack (specific frameworks/libraries)
    - Database integration approach
    - MVP feature prioritization for 2-day build
    - Deployment strategy
    - Security considerations
    - How to make it self-improving from day 1
    
    Be specific and practical. This needs to launch Monday morning.
    """
    
    print("Running THE RUBRIC evaluation...")
    print("Querying Claude, ChatGPT, and Grok...\n")
    
    results = await evaluator.run_rubric(prompt, context)
    
    formatted_output = evaluator.format_results(results)
    print(formatted_output)
    
    # Save results to file
    with open("rubric_evaluation_hub_architecture.json", "w") as f:
        json.dump(results, f, indent=2)
    
    with open("rubric_evaluation_hub_architecture.txt", "w") as f:
        f.write(formatted_output)
    
    print("\n\nResults saved to:")
    print("- rubric_evaluation_hub_architecture.json")
    print("- rubric_evaluation_hub_architecture.txt")
    
    return results


if __name__ == "__main__":
    # Run the evaluation
    results = asyncio.run(evaluate_hub_architecture())
