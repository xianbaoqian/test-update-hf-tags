# Requirements:
# - Load repos from a list
# - Filter out repos without pipeline_tag or pipeline_tag=text-generation, print filtered repos and repos that were filtered out, also save this result to a file in yaml
# - Go through them one by one by printing the readme.md (top 50 lines) and ask for confirmation, y to confirm, n to cancel and space to continue to the next 50 lines until all content has been shown (imagine the `less` CLI tool)
# - Print out all confirmed repos just the ID and not confirmed ones, also append this to the yaml file
# - For all confirmed repos, use @metadata.py to update their tag and add the below to readme.md and raise a PR. Please also check if another PR has been raised by user xianbao.
#   - library_name: transformers
#   - pipeline_tag: text-generation
# - At the end print out the repo with new PRs as well as repo that needs to be updated but not updated since a PR from xianbao already existed

import os
import yaml
import sys
import termios
import tty
from utils.metadata import load_metadata, update_metadata, save_metadata
from dotenv import load_dotenv
from huggingface_hub import HfApi

# Load environment variables from .env file
load_dotenv()

def load_repos_from_list(repo_ids):
    """
    Load repositories from a list and filter them based on metadata.

    Args:
        repo_ids (list): List of repository IDs to process.

    Returns:
        list: List of repository IDs that need updating.
    """
    filtered_repos = []
    repos_without_tags = []
    
    for repo_id in repo_ids:
        api = HfApi()
        try:
            model_info = api.model_info(repo_id=repo_id)
            if model_info.pipeline_tag and model_info.library_name:
                filtered_repos.append(repo_id)
            else:
                if any(sibling.rfilename == "config.json" for sibling in model_info.siblings):
                    # Transformers library requires this file.
                    repos_without_tags.append(repo_id)
        except Exception as e:
            print(f"An error occurred while fetching model info for {repo_id}: {e}")
            repos_without_tags.append(repo_id)
        
        # _, metadata = load_metadata(repo_id)
        # if 'pipeline_tag' in metadata:
        #     filtered_repos.append(repo_id)
        # elif 'tags' in metadata and 'text-to-image' in metadata['tags']:
        #     filtered_repos.append(repo_id)
        # elif 'library_name' in metadata and metadata['library_name'] == "transformers" and \
        #    'pipeline_tag' in metadata and metadata['pipeline_tag'] == "text-generation":
        #     filtered_repos.append(repo_id)
        # else:
        #     repos_without_tags.append(repo_id)
    
    print("Repos already tagged correctly:")
    print(filtered_repos)
    
    print("\nRepos that need updating:")
    print(repos_without_tags)
    
    with open("filtered_repos.yaml", "w") as file:
        yaml.dump({
            "filtered_repos": filtered_repos,
            "repos_without_tags": repos_without_tags
        }, file)

    return repos_without_tags

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
        print("Press 'y' to confirm update, 'n' to cancel, or space to continue: ", end='', flush=True)
        while True:
            key = get_key_press()
            if key.lower() == 'y':
                print(f"\nConfirmed: {repo_id}")
                return True
            elif key.lower() == 'n':
                print(f"\nNot confirmed: {repo_id}")
                return False
            elif key == ' ':
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
            metadata["pipeline_tag"] = "text-generation"
            pr_url = save_metadata(repo_id, metadata, create_pr=True, commit_message="Update metadata: Add library_name and pipeline_tag for text-generation pipeline using Transformers")
            if pr_url:
                print(f"PR created for {repo_id}. PR URL: {pr_url}")
            else:
                print(f"Failed to create PR for {repo_id}.")
        except Exception as e:
            print(f"Error updating {repo_id}: {str(e)}")
            import traceback
            print(traceback.format_exc())


if __name__ == "__main__":
    initial_repo_ids ="""
CompVis/stable-diffusion-v1-4
stabilityai/stable-diffusion-xl-base-1.0
meta-llama/Meta-Llama-3-8B
bigscience/bloom
stabilityai/stable-diffusion-3-medium
black-forest-labs/FLUX.1-dev
mistralai/Mixtral-8x7B-Instruct-v0.1
meta-llama/Llama-2-7b
meta-llama/Llama-2-7b-chat-hf
stabilityai/stable-diffusion-2-1
WarriorMama777/OrangeMixs
lllyasviel/ControlNet
lllyasviel/ControlNet-v1-1
meta-llama/Meta-Llama-3-8B-Instruct
mistralai/Mistral-7B-v0.1
openai/whisper-large-v3
microsoft/phi-2
prompthero/openjourney
google/gemma-7b
THUDM/chatglm-6b
bigcode/starcoder
CompVis/stable-diffusion-v-1-4-original
stabilityai/stable-video-diffusion-img2vid-xt
mistralai/Mistral-7B-Instruct-v0.2
tiiuae/falcon-40b
hakurei/waifu-diffusion
meta-llama/Meta-Llama-3.1-8B-Instruct
sentence-transformers/all-MiniLM-L6-v2
stabilityai/sdxl-turbo
openai-community/gpt2
black-forest-labs/FLUX.1-schnell
xai-org/grok-1
meta-llama/Llama-2-70b-chat-hf
THUDM/chatglm2-6b
databricks/dolly-v2-12b
ByteDance/SDXL-Lightning
stabilityai/stable-diffusion-2
google-bert/bert-base-uncased
coqui/XTTS-v2
lllyasviel/sd_control_collection
dreamlike-art/dreamlike-photoreal-2.0
meta-llama/Llama-2-7b-hf
stabilityai/stable-diffusion-xl-refiner-1.0
CohereForAI/c4ai-command-r-plus
mistralai/Mixtral-8x7B-v0.1
openai/whisper-large-v2
microsoft/Phi-3-mini-128k-instruct
HuggingFaceH4/zephyr-7b-beta
gsdf/Counterfeit-V2.5
mattshumer/Reflection-Llama-3.1-70B
h94/IP-Adapter-FaceID
mistralai/Mistral-7B-Instruct-v0.1
briaai/RMBG-1.4
webui/ControlNet-modules-safetensors
EleutherAI/gpt-j-6b
apple/OpenELM
meta-llama/Meta-Llama-3-70B-Instruct
stabilityai/stable-diffusion-xl-base-0.9
openai/clip-vit-large-patch14
openbmb/MiniCPM-Llama3-V-2_5
monster-labs/control_v1p_sd15_qrcode_monster
microsoft/phi-1_5
stabilityai/sd-vae-ft-mse-original
01-ai/Yi-34B
2Noise/ChatTTS
stabilityai/stable-cascade
BAAI/bge-m3
prompthero/openjourney-v4
cognitivecomputations/dolphin-2.5-mixtral-8x7b
tiiuae/falcon-40b-instruct
ai21labs/Jamba-v0.1
google/flan-t5-xxl
mosaicml/mpt-7b
google/gemma-7b-it
tiiuae/falcon-180B
openchat/openchat_3.5
facebook/bart-large-cnn
facebook/bart-large-mnli
hakurei/waifu-diffusion-v1-4
mistralai/Codestral-22B-v0.1
databricks/dbrx-instruct
HuggingFaceH4/zephyr-7b-alpha
microsoft/Florence-2-large
THUDM/chatglm3-6b
tiiuae/falcon-7b
TinyLlama/TinyLlama-1.1B-Chat-v1.0
Salesforce/blip-image-captioning-large
CohereForAI/c4ai-command-r-v01
mistralai/Mistral-Nemo-Instruct-2407
suno/bark
microsoft/Phi-3-mini-4k-instruct
dreamlike-art/dreamlike-diffusion-1.0
meta-llama/Llama-2-13b-chat-hf
h94/IP-Adapter
adept/fuyu-8b
miqudev/miqu-1-70b
nuigurumi/basil_mix
Envvi/Inkpunk-Diffusion
xinsir/controlnet-union-sdxl-1.0
lj1995/VoiceConversionWebUI
    """.split("\n")
    initial_repo_ids = [repo_id.strip() for repo_id in initial_repo_ids if repo_id.strip()]
    
    repos_to_update = load_repos_from_list(initial_repo_ids)
    confirmed_repos = display_and_confirm_repos(repos_to_update)
    repos_without_prs = filter_repos_without_prs(confirmed_repos)
    
    with open("repos_without_prs.yaml", "w") as file:
        yaml.dump(repos_without_prs, file)


