import os
import importlib
import inspect
from typing import List, Type, Any, Dict
from pathlib import Path
from dotenv import load_dotenv
from .base import BaseTool

class ToolRegistry:
    """Registry for managing and executing tools"""
    
    def __init__(self):
        """Initialize the tool registry and discover available tools"""
        self.tools: List[BaseTool] = []
        self._discover_and_register_tools()
    
    def _discover_and_register_tools(self) -> None:
        """Automatically discover and register tools from the tools directory"""
        # Get the tools directory path
        tools_dir = Path(__file__).parent
        
        # Find all Python files in the tools directory (excluding __init__.py, base.py, and registry.py)
        tool_files = [
            f for f in tools_dir.glob('*.py')
            if f.name not in ['__init__.py', 'base.py', 'registry.py']
        ]
        
        for tool_file in tool_files:
            # Convert file path to module path
            relative_path = tool_file.relative_to(Path(__file__).parent.parent)
            module_path = str(relative_path.with_suffix('')).replace(os.sep, '.')
            
            try:
                # Import the module
                module = importlib.import_module(f"tools.{module_path}")
                
                # Find all classes in the module that inherit from BaseTool
                tool_classes = inspect.getmembers(
                    module,
                    lambda member: (inspect.isclass(member) 
                                  and issubclass(member, BaseTool)
                                  and member != BaseTool)
                )
                
                # Initialize and register each tool
                for _, tool_class in tool_classes:
                    try:
                        # Get the required initialization parameters
                        init_params = self._get_init_params(tool_class)
                        tool_instance = tool_class(**init_params)
                        self.tools.append(tool_instance)
                        print(f"Successfully registered tool: {tool_class.__name__}")
                    except Exception as e:
                        print(f"Failed to initialize {tool_class.__name__}: {str(e)}")
                        
            except Exception as e:
                print(f"Failed to load module {module_path}: {str(e)}")
    
    def _get_init_params(self, tool_class: Type[BaseTool]) -> Dict[str, Any]:
        """
        Get initialization parameters for a tool class from environment variables.
        
        Args:
            tool_class: The tool class to get parameters for
            
        Returns:
            Dict of parameter names and values
        """
        load_dotenv()
        
        # Get the __init__ signature
        sig = inspect.signature(tool_class.__init__)
        params = {}
        
        # For each parameter in __init__
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
                
            # Convert parameter name to expected env var name
            # e.g., api_key -> WEATHERTOOL_API_KEY
            env_var_name = f"{tool_class.__name__.upper()}_{param_name.upper()}"
            
            # Get value from environment variables
            value = os.getenv(env_var_name)
            
            # If parameter has a default value, use it when env var is not set
            if value is None and param.default != inspect.Parameter.empty:
                value = param.default
                
            if value is not None:
                # Convert value to parameter's annotated type if specified
                if param.annotation != inspect.Parameter.empty:
                    try:
                        if param.annotation == bool:
                            value = value.lower() in ('true', '1', 'yes')
                        elif param.annotation == tuple:
                            # Handle tuple conversion for coordinates
                            if isinstance(value, str):
                                value = tuple(map(float, value.split(',')))
                        else:
                            value = param.annotation(value)
                    except ValueError as e:
                        print(f"Warning: Could not convert {env_var_name} to {param.annotation}")
                        
                params[param_name] = value
                
        return params
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Get schemas for all tools in format expected by OpenAI.
        
        Returns:
            List of tool schemas
        """
        return [{
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters
        } for tool in self.tools]
    
    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Execute a specific tool by name.
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Arguments to pass to the tool
            
        Returns:
            Tool execution results
            
        Raises:
            ValueError: If tool not found
        """
        for tool in self.tools:
            if tool.name == tool_name:
                try:
                    return tool.execute(**kwargs)
                except Exception as e:
                    return {"error": str(e)}
        raise ValueError(f"Tool '{tool_name}' not found")
    
    def list_available_tools(self) -> List[str]:
        """
        Get list of available tool names.
        
        Returns:
            List of tool names
        """
        return [tool.name for tool in self.tools]

    def get_tool(self, tool_name: str) -> BaseTool:
        """
        Get a specific tool instance by name.
        
        Args:
            tool_name: Name of the tool to get
            
        Returns:
            Tool instance
            
        Raises:
            ValueError: If tool not found
        """
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        raise ValueError(f"Tool '{tool_name}' not found")

    def get_tool_help(self, tool_name: str) -> str:
        """
        Get help text for a specific tool.
        
        Args:
            tool_name: Name of the tool to get help for
            
        Returns:
            Help text for the tool
            
        Raises:
            ValueError: If tool not found
        """
        tool = self.get_tool(tool_name)
        return tool.help
