import os
import logging
from typing import Optional, Type, TypeVar
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger("jobhunt.llm")

T = TypeVar("T", bound=BaseModel)

class LLMConfigurationError(Exception):
    """Raised when LLM is requested but required API keys or configurations are missing."""
    pass

class LLMProviderError(Exception):
    """Raised when an external LLM provider encounters an error (rate limit, timeout, auth)."""
    pass

class LLMClient:
    """
    Production LLM provider abstraction supporting Anthropic Claude and OpenAI.
    Fails explicitly with clear actionable errors instead of silently fabricating output.
    """

    def __init__(self):
        self.provider = (settings.LLM_PROVIDER or "anthropic").lower()
        self.anthropic_key = settings.ANTHROPIC_API_KEY
        self.openai_key = settings.OPENAI_API_KEY
        self.model = settings.LLM_MODEL or "claude-3-haiku-20240307"

    def is_configured(self) -> bool:
        """Checks if a valid, non-placeholder API key is set for the active provider."""
        if self.provider == "anthropic":
            return bool(self.anthropic_key and self.anthropic_key not in ["mock-api-key", "your-api-key", ""])
        elif self.provider == "openai":
            return bool(self.openai_key and self.openai_key not in ["mock-api-key", "your-api-key", ""])
        return False

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2500,
        temperature: float = 0.2
    ) -> str:
        """
        Executes a real text generation request to the configured LLM provider.
        Raises LLMConfigurationError if keys are missing.
        """
        if not self.is_configured():
            raise LLMConfigurationError(
                f"LLM Provider '{self.provider}' is not configured with a valid API key. "
                f"Please add a valid key in your .env file (ANTHROPIC_API_KEY or OPENAI_API_KEY) "
                f"to enable AI resume tailoring and cover letter generation."
            )

        if self.provider == "anthropic":
            return self._call_anthropic(prompt, system_prompt, max_tokens, temperature)
        elif self.provider == "openai":
            return self._call_openai(prompt, system_prompt, max_tokens, temperature)
        else:
            raise LLMConfigurationError(f"Unsupported LLM provider: '{self.provider}'. Use 'anthropic' or 'openai'.")

    def _call_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> str:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.anthropic_key, timeout=30.0)
            
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            response = client.messages.create(**kwargs)
            return response.content[0].text
        except ImportError:
            raise LLMConfigurationError("The 'anthropic' package is not installed.")
        except anthropic.AuthenticationError:
            raise LLMProviderError("Anthropic authentication failed. The provided ANTHROPIC_API_KEY is invalid.")
        except anthropic.RateLimitError:
            raise LLMProviderError("Anthropic rate limit reached. Please retry after a brief delay.")
        except anthropic.APITimeoutError:
            raise LLMProviderError("Anthropic API request timed out after 30 seconds.")
        except Exception as e:
            logger.error("Anthropic API call failed: %s", str(e))
            raise LLMProviderError(f"Anthropic provider error: {str(e)}")

    def _call_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> str:
        try:
            import openai
            client = openai.OpenAI(api_key=self.openai_key, timeout=30.0)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            model_name = "gpt-4o-mini" if "haiku" in self.model else self.model
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content or ""
        except ImportError:
            raise LLMConfigurationError("The 'openai' package is not installed.")
        except openai.AuthenticationError:
            raise LLMProviderError("OpenAI authentication failed. The provided OPENAI_API_KEY is invalid.")
        except openai.RateLimitError:
            raise LLMProviderError("OpenAI rate limit reached. Please retry shortly.")
        except Exception as e:
            logger.error("OpenAI API call failed: %s", str(e))
            raise LLMProviderError(f"OpenAI provider error: {str(e)}")

llm_client = LLMClient()
