import os
import yaml
from dotenv import load_dotenv
from huggingface_hub import HfApi, Repository, ModelCard, ModelCardData


# Load variables from .env file
load_dotenv()

def get_library_name(model_card):
    try:
        metadata = yaml.safe_load(model_card.data.to_yaml())
        return metadata.get("library_name", None)
    except Exception as e:
        print(f"Error getting library_name from model card: {str(e)}")
        return None

def contains_keywords(model_card):
    keywords = ["Transformers", "llm", "text-generation"]
    content = model_card.data.to_dict().get("text", "").lower()
    for keyword in keywords:
        if keyword.lower() in content:
            return True
    return False

def categorize_repos(repo_ids):
    api = HfApi()
    transformers_repos = []
    other_library_repos = []
    no_library_transformers_repos = []
    no_library_other_repos = []

    for repo_id in repo_ids:
        try:
            model_card = ModelCard.load(repo_id)
            library_name = get_library_name(model_card)
            has_keywords = contains_keywords(model_card)

            if library_name:
                print(f"Repo: {repo_id}, Library Name: {library_name}")
                if library_name.lower() == "transformers":
                    transformers_repos.append(repo_id)
                else:
                    other_library_repos.append((repo_id, library_name))
            else:
                if has_keywords:
                    no_library_transformers_repos.append(repo_id)
                else:
                    no_library_other_repos.append(repo_id)
        except Exception as e:
            print(f"Error processing repository {repo_id}: {str(e)}")

    return transformers_repos, other_library_repos, no_library_transformers_repos, no_library_other_repos

def display_categorized_repos(transformers_repos, other_library_repos, no_library_transformers_repos, no_library_other_repos):
    print("\nRepos with library_name = Transformers:")
    print(transformers_repos)

    print("\nRepos with library_name but not Transformers (also list their tag):")
    for repo, library_name in other_library_repos:
        print(f"{repo} (Library Name: {library_name})")

    print("\nRepos without any library_name but should be tagged with transformers:")
    print(no_library_transformers_repos)

    print("\nRepos without any library_name and doesn't belong to transformers:")
    print(no_library_other_repos)

def add_transformers_tag(repo_id):
    try:
        # Load the model card from the repository
        model_card = ModelCard.load(repo_id)
        # Parse the YAML metadata from the model card content
        metadata = yaml.safe_load(model_card.data.to_yaml())
        # Add the "transformers" tag to the "tags" field in the metadata
        if "tags" not in metadata:
            metadata["tags"] = []
        if "transformers" not in metadata["tags"]:
            metadata["tags"].append("transformers")
        # Update the model card content with the modified metadata
        model_card.data = ModelCardData.from_yaml("---\n" + yaml.dump(metadata) + "---\n" + model_card.data.to_yaml().split("---")[2])
        # Save the updated model card
        model_card.save(repo_id)
        print(f"Added 'transformers' tag to model card for repository {repo_id}")
        return True
    except Exception as e:
        print(f"Error adding 'transformers' tag to model card for repository {repo_id}: {str(e)}")
        return False

def create_prs_for_missing_library_name(repos):
    for repo_id in repos:
        add_transformers_tag(repo_id)

def main():
    # Get the list of repository IDs to process (e.g., from a file or API)
    repo_ids = [
        "nateraw/vit-base-beans",
        "01-ai/Yi-Coder-9B-Chat",
        "deepseek-ai/DeepSeek-Coder-V2-Instruct-0724"
        # Add more repository IDs as needed
    ]

    transformers_repos, other_library_repos, no_library_transformers_repos, no_library_other_repos = categorize_repos(repo_ids)
    display_categorized_repos(transformers_repos, other_library_repos, no_library_transformers_repos, no_library_other_repos)

    # Suggest user to update the string list and call another function to create PRs to add the missing library_name
    print("\nPlease review the above lists and update the string list if needed.")
    user_input = input("Do you want to create PRs to add the missing library_name to the appropriate repos? (yes/no): ")
    if user_input.lower() == "yes":
        create_prs_for_missing_library_name(no_library_transformers_repos)

from huggingface_hub import login
if __name__ == "__main__":

    def huggingface_login():
        try:
            login(token=os.environ["HF_TOKEN"])
            print("Successfully logged in to Hugging Face Hub.")
        except Exception as e:
            print(f"Error logging in to Hugging Face Hub: {str(e)}")
            return False
        return True

    if not huggingface_login():
        print("Exiting due to login failure.")
        exit(1)
    main()