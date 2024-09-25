import os
import pickle
import sys
import termios
import tty
from utils.metadata import load_metadata, update_metadata, save_metadata
from dotenv import load_dotenv
from huggingface_hub import HfApi
import yaml

# Load environment variables from .env file
load_dotenv()

CACHE_FILE = "model_info_cache.pkl"

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as file:
            return pickle.load(file)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "wb") as file:
        pickle.dump(cache, file)

def find_likely_transformers_repos(repo_ids):
    """
    Identify repositories that are likely using the transformers library but are not fully tagged.

    Args:
        repo_ids (list): List of repository IDs to process.

    Returns:
        list: List of repository IDs that are likely using the transformers library.
    """
    already_tagged_repos = []
    likely_transformers_repos = []
    other_repos = []
    
    cache = load_cache()
    api = HfApi()

    for repo_id in repo_ids:
        if repo_id in cache:
            model_info = cache[repo_id]
        else:
            try:
                model_info = api.model_info(repo_id=repo_id)
                cache[repo_id] = model_info
            except Exception as e:
                print(f"An error occurred while fetching model info for {repo_id}: {e}")
                import traceback
                traceback.print_exc()
                print("Exiting the process due to an error.")
                sys.exit(1)

        if model_info.pipeline_tag and model_info.library_name:
            already_tagged_repos.append(repo_id)
            continue
        
        if model_info.library_name == "diffusers":
            already_tagged_repos.append(repo_id)
            continue
        
        if 'ggml' in repo_id.lower():
            other_repos.append(repo_id)
            continue
        
        if any(tag.lower() in ["colbert", "nemo", "paddlenlp", "ggml", "sam2"] for tag in model_info.tags):
            other_repos.append(repo_id)
            continue
        
        if any(sibling.rfilename == "config.json" for sibling in model_info.siblings):
            if not model_info.config or 'architectures' not in model_info.config:
                other_repos.append(repo_id)
                continue
                
            likely_transformers_repos.append(repo_id)
            continue

        other_repos.append(repo_id)
    
    save_cache(cache)

    print("Repos already tagged correctly:")
    print(already_tagged_repos)
    
    print("\nRepos likely using transformers but not fully tagged:")
    print(likely_transformers_repos)
    
    print("\nOther repos:")
    print(other_repos)
    
    with open("filtered_repos.yaml", "w") as file:
        yaml.dump({
            "already_tagged_repos": already_tagged_repos,
            "likely_transformers_repos": likely_transformers_repos,
            "other_repos": other_repos
        }, file)

    return likely_transformers_repos

def get_key_press():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def display_readme(repo_id):
    repo_card, metadata = load_metadata(repo_id)
    readme_lines = repo_card.content.split("\n")
    
    start = 0
    while start < len(readme_lines):
        msg = f"{'='*20} Repository: {repo_id} {'='*20}"
        print(f"\n{'='*len(msg)}")
        print(msg)
        print(f"{'='*len(msg)}\n")
        lines_per_page = 30
        
        for line in readme_lines[start:start+lines_per_page]:
            print(line)
        if start + lines_per_page >= len(readme_lines):
            print("Press 'y' to confirm update, 'n' to cancel: ", end='', flush=True)
        else:
            print("Press 'y' to confirm update, 'n' to cancel, or space to continue: ", end='', flush=True)
        while True:
            key = get_key_press()
            if key.lower() == 'y':
                print(f"\nConfirmed: {repo_id}")
                return True
            elif key.lower() == 'n':
                print(f"\nNot confirmed: {repo_id}")
                return False
            elif key == ' ' and start + lines_per_page < len(readme_lines):
                break
            elif key == '\x03':  # Ctrl+C
                print("\nOperation cancelled by user (Ctrl+C).")
                exit(1)
            elif key == '\x1c':  # Ctrl+\
                print("\nOperation cancelled by user (Ctrl+\\).")
                exit(1)
        start += lines_per_page
    return False

def display_and_confirm_repos(repo_ids):
    """
    Display README for each repository and collect confirmed repos.
    
    Args:
        repo_ids (list): List of repository IDs to process.
    
    Returns:
        list: List of confirmed repository IDs.
    """
    confirmed_repos = []
    not_confirmed_repos = []
    
    for repo_id in repo_ids:
        if display_readme(repo_id):
            confirmed_repos.append(repo_id)
        else:
            not_confirmed_repos.append(repo_id)
    
    with open("filtered_repos.yaml", "a") as file:
        yaml.dump({
            "confirmed_repos": confirmed_repos,
            "not_confirmed_repos": not_confirmed_repos
        }, file)

    return confirmed_repos

def filter_repos_with_transformers_import(repo_ids):
    """
    Filter repositories that contain 'import transformers' or 'from transformers import' in their README.

    Args:
        repo_ids (list): List of repository IDs to check.

    Returns:
        list: List of repository IDs with the import statement.
    """
    auto_confirmed = []
    to_be_confirmed = []
    api = HfApi()

    for repo_id in repo_ids:
        repo_card, _ = load_metadata(repo_id)
        if not repo_card:
            # Skip these
            continue

        if "import transformers" in repo_card.content or "from transformers import" in repo_card.content:
            if 'pip install transformers' in repo_card.content:
                to_be_confirmed.append(repo_id)
                continue
            print(f"Repo {repo_id} contains 'import transformers' or 'from transformers import'")
            auto_confirmed.append(repo_id)
            continue
        
        model_info = api.model_info(repo_id=repo_id)
        if model_info.config and "transformers_version" in model_info.config:
            print(f"Repo {repo_id} contains 'transformers_version' in its config.")
            auto_confirmed.append(repo_id)
            continue
        
        to_be_confirmed.append(repo_id)

    print(f"repos auto-confirmed: {auto_confirmed}")
    print(f"repos to be confirmed: {to_be_confirmed}")
    return auto_confirmed, to_be_confirmed

def filter_repos_without_prs(repo_ids):
    """
    Check for existing PRs and filter out repos with PRs by user 'xianbao'.
    
    Args:
        repo_ids (list): List of repository IDs to check.
    
    Returns:
        list: List of repository IDs without PRs by 'xianbao'.
    """
    repos_without_prs = []
    api = HfApi(token=os.getenv("HF_TOKEN"))
    
    for repo_id in repo_ids:
        try:
            prs = api.get_repo_discussions(repo_id=repo_id, repo_type="model")
            if not any(pr.author == "xianbao" and pr.is_pull_request for pr in prs):
                repos_without_prs.append(repo_id)
            else:
                print(f"PR by user xianbao already exists for {repo_id}")
        except Exception as e:
            print(f"Error checking PRs for {repo_id}: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    with open("filtered_repos.yaml", "a") as file:
        yaml.dump({"repos_without_prs": repos_without_prs}, file)
        
    return repos_without_prs

def update_repos_metadata(repo_ids):
    """
    Update metadata and create PRs for the given repositories.
    
    Args:
        repo_ids (list): List of repository IDs to update.
    """
    for repo_id in repo_ids:
        print(f"Updating {repo_id}")
        try:
            _, metadata = load_metadata(repo_id)
            metadata["library_name"] = "transformers"
            # Note! Pipeline tag can be inferred when library_name is transformers so don't do the following.
            # metadata["pipeline_tag"] = "text-generation"
            pr_url = save_metadata(repo_id, metadata, create_pr=True, commit_message="Update metadata: Add library_name to Transformers")
            if pr_url:
                print(f"PR created for {repo_id}  PR URL: {pr_url}")
            else:
                print(f"Failed to create PR for {repo_id}.")
        except Exception as e:
            print(f"Error updating {repo_id}: {str(e)}")
            import traceback
            print(traceback.format_exc())




def dry_run():
    print("Starting dry run...")
    from utils.trendy import get_no_library_repos

    initial_repo_ids = get_no_library_repos(sort="likes30d", limit=500)
    with open("all_repos.yaml", "w") as file:
        yaml.dump({"all_repos": initial_repo_ids}, file)
    
    likely_transformers_repos = find_likely_transformers_repos(initial_repo_ids)
    repos_without_prs = filter_repos_without_prs(likely_transformers_repos)
    
    repos_with_import, repos_without_import = filter_repos_with_transformers_import(repos_without_prs)
    
    print(f"Repos without imports to be confirmed: {repos_without_import}")
        
    confirmed_repos = display_and_confirm_repos(repos_without_import)
    processing_repos = repos_with_import + confirmed_repos
    
    with open("processed_repos.yaml", "w") as file:
        yaml.dump(processing_repos, file)
    
    print(f"\nDry run completed. {len(processing_repos)} repositories identified for updating.")
    print("Review the 'processed_repos.yaml' file for the list of repositories.")
    
    return processing_repos

def update_repos():
    print("Starting the update process...")
    
    # Load processed repos from YAML file
    with open("processed_repos.yaml", "r") as file:
        processing_repos = yaml.safe_load(file)
    
    if not processing_repos:
        print("No repositories found in processed_repos.yaml. Exiting.")
        return
    
    print(f"Loaded {len(processing_repos)} repositories from processed_repos.yaml:")
    print(processing_repos)
    
    update_repos_metadata(processing_repos)
    print("Update process completed.")

if __name__ == "__main__":
    # Uncomment below to actually update the metadata
    # update_repos()
    
    processing_repos = dry_run()
    
    if processing_repos:
        print("\nDry run completed. Do you want to proceed with updating the repositories?")
        confirmation = input("Enter 'yes' to continue or any other key to exit: ").lower()
        
        if confirmation == 'yes':
            update_repos()
        else:
            print("Update process cancelled.")
    else:
        print("No repositories to update. Exiting.")