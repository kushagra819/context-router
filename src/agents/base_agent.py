"""Base agent class — wraps a prompt template + model into a callable unit."""

from src.models.base import BaseModel, ModelResponse


class BaseAgent:
    """
    An agent is a (role, prompt_template, model) tuple.
    It formats the prompt with inputs, calls the model, and returns the response.
    """

    def __init__(self, role: str, task_type: str, system_prompt: str, user_prompt_template: str, model: BaseModel):
        self.role = role                          # e.g., "analyzer", "solver", "verifier"
        self.task_type = task_type                # e.g., "extraction", "reasoning", "verification"
        self.system_prompt = system_prompt
        self.user_prompt_template = user_prompt_template
        self.model = model

    def run(self, **kwargs) -> ModelResponse:
        """
        Format the prompt with kwargs and call the model.
        
        Example:
            agent.run(problem="What is 2+2?", analysis="Simple addition")
        """
        user_prompt = self.user_prompt_template.format(**kwargs)
        response = self.model.generate(prompt=user_prompt, system=self.system_prompt)
        return response

    def __repr__(self):
        return f"Agent(role={self.role}, model={self.model.model_name})"
