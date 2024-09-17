from typing import Dict, Optional, Tuple
import traceback
from huggingface_hub import RepoCard
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_metadata(repo_id: str) -> Optional[Tuple[RepoCard, Dict]]:
    """
    Load metadata from a Hugging Face model repository.

    Args:
        repo_id (str): The repository ID on Hugging Face.

    Returns:
        Optional[Tuple[RepoCard, Dict]]: A tuple containing the RepoCard and metadata as a dictionary, or None if loading fails.
    """
    try:
        repo_card = RepoCard.load(repo_id)
        metadata = repo_card.data.to_dict()
        return repo_card, metadata
    except Exception as e:
        print(f"Error loading metadata from repository {repo_id}: {str(e)}")
        print(traceback.format_exc())
        return None, None

def update_metadata(metadata: Dict, library_name: str = "transformers") -> Dict:
    """
    Update the metadata with the specified library name.

    Args:
        metadata (Dict): The original metadata dictionary.
        library_name (str): The library name to add or update. Defaults to "transformers".

    Returns:
        Dict: The updated metadata dictionary.
    """
    metadata["library_name"] = library_name
    return metadata

def save_metadata(repo_id: str, metadata: Dict, create_pr: bool = True, commit_message: str = "Update metadata tags") -> Optional[str]:
    """
    Save the updated metadata to the Hugging Face model repository.

    Args:
        repo_id (str): The repository ID on Hugging Face.
        metadata (Dict): The updated metadata dictionary.
        create_pr (bool): Whether to create a pull request. Defaults to True.

    Returns:
        Optional[str]: The PR URL if created successfully, None otherwise.
    """
    try:
        repo_card = RepoCard.load(repo_id)
        for key, value in metadata.items():
            repo_card.data[key] = value
        
        pr_url = repo_card.push_to_hub(
            repo_id=repo_id,
            commit_message=commit_message,
            create_pr=create_pr
        )
        print(f"Successfully {'created a pull request' if create_pr else 'pushed'} to update metadata for {repo_id}")
        return pr_url
    except Exception as e:
        print(f"Error saving metadata for {repo_id}: {str(e)}")
        print(traceback.format_exc())
        return None

def run_tests(test_repo_id: str):
    """
    Run tests for the metadata functions.

    Args:
        test_repo_id (str): The repository ID to use for testing.
    """
    print("Running tests...")
    
    # Test load_metadata
    result = load_metadata(test_repo_id)
    if result is not None:
        repo_card, original_metadata = result
        print("Metadata loaded successfully.")
        print(f"Original metadata: {original_metadata}")
        
        # Test update_metadata
        updated_metadata = update_metadata(original_metadata)
        print(f"Updated metadata: {updated_metadata}")
        assert "library_name" in updated_metadata, "library_name not added to metadata"
        assert updated_metadata["library_name"] == "transformers", "library_name not set to 'transformers'"
        
        # Test save_metadata
        if "HF_TOKEN" in os.environ:
            pr_url = save_metadata(test_repo_id, updated_metadata)
            if pr_url:
                print("Pull request for metadata update created successfully.")
                print(f"Pull request URL: {pr_url}")
            else:
                print("Failed to create pull request for metadata update.")
        else:
            print("Skipping save_metadata test: HF_TOKEN not found in environment variables.")
    else:
        print("Failed to load metadata.")
    
    print("Tests completed.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        test_repo_id = sys.argv[1]
        run_tests(test_repo_id)
    else:
        print("Usage: python utils/metadata.py <test_repo_id>")
        print("Running tests with default repo...")
        run_tests("huggingface/transformers-dummy-model")
