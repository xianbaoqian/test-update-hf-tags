"""
This file contains utility functions to interact with the Hugging Face Hub to retrieve model information.
"""

from huggingface_hub import HfApi, hf_api
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_model_info(repo_id: str, revision: str = None, token: str = None, timeout: float = None, security_status: bool = None) -> hf_api.ModelInfo:
    """
    Retrieve the model information from the Hugging Face Hub.

    Parameters:
    - repo_id (str): A namespace (user or an organization) and a repo name separated by a /.
    - revision (str, optional): The revision of the model repository from which to get the information.
    - token (str, optional): An authentication token.
    - timeout (float, optional): Whether to set a timeout for the request to the Hub.
    - security_status (bool, optional): Whether to retrieve the security status from the model repository as well.

    Returns:
    - ModelInfo: The model repository information.
    """
    api = HfApi()
    return api.model_info(repo_id=repo_id, revision=revision, token=token, timeout=timeout, securityStatus=security_status,
                          # We do need to get files info.
                          files_metadata=True)

if __name__ == "__main__":
    # Test case to run through a model
    test_repo_id = "google/gemma-7b"
    hf_token = os.getenv("HF_TOKEN")  # Ensure you have your Hugging Face token in the .env file
    try:
        model_info = get_model_info(repo_id=test_repo_id, token=hf_token)
        print(model_info.siblings)
        print(model_info.tags)
        print(model_info.library_name)
        print(model_info.pipeline_tag)
    except Exception as e:
        print(f"An error occurred: {e}")
