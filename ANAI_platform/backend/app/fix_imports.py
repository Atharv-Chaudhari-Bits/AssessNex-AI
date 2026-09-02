"""
Import fix for LangGraph compatibility.
"""

import sys
import warnings

def fix_langgraph():
    """Apply LangGraph compatibility fixes."""
    try:
        import langgraph
        # Check if we need to patch
        if not hasattr(langgraph, '__version__'):
            return
        
        # Try to fix the Reviver issue
        try:
            from langgraph.checkpoint.serde import jsonplus
            if hasattr(jsonplus, 'Reviver'):
                original_init = jsonplus.Reviver.__init__
                
                def patched_init(self, *args, **kwargs):
                    # Remove problematic parameter
                    kwargs.pop('allowed_objects', None)
                    return original_init(self, *args, **kwargs)
                
                jsonplus.Reviver.__init__ = patched_init
                print("✅ LangGraph compatibility fix applied")
        except Exception as e:
            print(f"⚠️  LangGraph fix not applied: {e}")
    except ImportError:
        print("⚠️  LangGraph not installed")

# Apply the fix when imported
fix_langgraph()
