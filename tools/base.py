from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseTool(ABC):
    """
    Abstract base class for all tools.
    
    All tools must inherit from this class and implement its abstract methods.
    Tools are automatically discovered and registered by the ToolRegistry.
    
    Example:
        class MyTool(BaseTool):
            def __init__(self, api_key: str):
                self.api_key = api_key
                
            @property
            def name(self) -> str:
                return "my_tool"
                
            @property
            def description(self) -> str:
                return "Description of what my tool does"
                
            def execute(self, **kwargs) -> Any:
                return self._process_request(**kwargs)
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Name of the tool. This will be used as the function name in OpenAI's function calling.
        
        Returns:
            str: Tool name (should be unique across all tools)
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Description of what the tool does. This will be used by the LLM to understand
        when to use this tool.
        
        Returns:
            str: Tool description
        """
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Execute the tool's main functionality.
        
        Args:
            **kwargs: Keyword arguments matching the parameters schema
            
        Returns:
            Any: Result of the tool execution
            
        Raises:
            Exception: If execution fails
        """
        pass
        
    def validate_parameters(self, **kwargs) -> bool:
        """
        Validate that provided parameters match the schema.
        
        Args:
            **kwargs: Parameters to validate
            
        Returns:
            bool: True if parameters are valid
            
        Raises:
            ValueError: If parameters are invalid
        """
        required = self.parameters.get("required", [])
        properties = self.parameters.get("properties", {})
        
        # Check required parameters
        for param in required:
            if param not in kwargs:
                raise ValueError(f"Missing required parameter: {param}")
        
        # Check parameter types
        for param, value in kwargs.items():
            if param not in properties:
                raise ValueError(f"Unexpected parameter: {param}")
            
            expected_type = properties[param]["type"]
            if expected_type == "string" and not isinstance(value, str):
                raise ValueError(f"Parameter {param} must be a string")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                raise ValueError(f"Parameter {param} must be a number")
            elif expected_type == "array" and not isinstance(value, (list, tuple)):
                raise ValueError(f"Parameter {param} must be an array")
            
        return True
    
    def format_error(self, error: Exception) -> Dict[str, str]:
        """
        Format an error response.
        
        Args:
            error: The exception that occurred
            
        Returns:
            Dict with error information
        """
        return {
            "error": str(error),
            "tool": self.name
        }
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get the complete function schema for OpenAI.
        
        Returns:
            Dict containing the complete function schema
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
    
    @property
    def help(self) -> str:
        """
        Get help text for this tool.
        
        Returns:
            str: Formatted help text
        """
        schema = self.get_schema()
        params = schema["parameters"].get("properties", {})
        required = schema["parameters"].get("required", [])
        
        help_text = [
            f"Tool: {self.name}",
            f"Description: {self.description}",
            "\nParameters:"
        ]
        
        for param_name, param_info in params.items():
            req_str = "(required)" if param_name in required else "(optional)"
            desc = param_info.get("description", "No description")
            type_str = param_info.get("type", "any")
            help_text.append(f"  {param_name} ({type_str}) {req_str}: {desc}")
        
        return "\n".join(help_text)